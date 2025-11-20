import math
import random
import time
import enum

import pygame

import pymunk as pm
import pymunk.util
from pymunk import Vec2d

from objects import Controller, Entity, COLLTYPE_DEFAULT, BallEnemy
from pickups import HealthPickup, LoreOrePickup, LengthPickup, BeanPickup, CoffeePotPickup

"""
zippy ball pursues and eats beans?
if it gets enough it transforms into eye ball and multiple eye balls can merge into eye boss
and eye boss drops portable camera pickup


forgetful ball rests on lore wil eat it and ??
"""

class Zippy(BallEnemy):
    track_as = ['Enemy']
    def __init__(self, app, pos):
        super().__init__(app, pos, 3, 32*32/1.8, 3, 1200)
        self.direction = Vec2d(0,0)
        self.going = False
        self.cooldown = self.app.engine_time
        self.can_stop = False
        self.beans = 0

    def update(self):
        player = self.app.player
        if player is None: return
        self.hit_player(player)

        beans = self.app.tracker['BeanPickup']

        if not self.going and (self.app.engine_time-self.cooldown > 0 or self.app.camera.contains(self.body.position, 1)):
#            print('going')
            self.going = True
            self.can_stop = False


            target = player
            if len(beans) > 0:
                #TODO this might want to filter for on-screen beans
#                print('bean')
                target = beans[0]


            delta = target.body.position-self.body.position
            delta /= abs(delta)
            self.direction = delta*self.speed
            self.friction = -10*self.m

        if self.going:
            for bean in beans:
                try:
                    hit = self.shape.shapes_collide(bean.shape)
#                    print('bwned')
                    self.beans+= 1
                    self.app.remove_entity(bean)
                except AssertionError: pass

            self.body.apply_force_at_local_point(self.direction)

            if not self.can_stop and self.app.camera.contains(self.body.position, 0):
#                print('can stop')
                self.can_stop = True

            if self.can_stop and not self.app.camera.contains(self.body.position, 50):
#                print('stopping')
                self.going = False
                self.cooldown = self.app.engine_time+5
                self.friction = -100*self.m

        self.apply_friction(player)

    def get_drops(self):
        result = []
        if random.random() < 0.1 and  len(self.app.tracker['CoffeePotPickup']) == 0:
           result.append(CoffeePotPickup(self.app, self.body.position))

        result.append(BeanPickup(self.app, self.body.position))
        t = random.random()
        M = 7 + int(self.beans/7)*7
        N = int((M+1)*t)
        if N > 0:
            a = random.random()
            for i in range(N+1):
                aa = a+2*math.pi*i/M
                dx,dy = random.random()-0.5, random.random()-0.5
                r = 7+2*i%2
                result.append(LoreOrePickup(self.app, self.body.position +
                    Vec2d(r*math.cos(aa)+dx, r*math.sin(aa)+dy)
                    ))

        return result


class BallState(enum.Enum):
    NORML = 0
    FGTFL = 1
    LSTFL = 2

class Ball(BallEnemy):
    track_as = ['Enemy']

    update_map = {
        BallState.NORML: BallEnemy.update,
        }

    def __str__(self):
        p = self.position
        return f'E {p.x:6.1f} {p.y:6.1f} Ball {self.state}'

    def __init__(self, app, pos, r = None, m = None, h = None):
        if r is None:
            r= 4+4*random.random()
            m = r*r/1.8
            h = r/4
        super().__init__(app, pos, r, m, h)
        self.last_aggro = 0
        self._going = True
        self.lores = 0

        if random.random() > 0.15:
            self.set_state(BallState.NORML)
        else:
            self.set_state(BallState.FGTFL)

    def set_state(self, state):
        self.state = state
        if state is BallState.NORML:
            self.update = self.normal_update
        elif state is BallState.FGTFL:
            self.update = self.forgetful_update
        elif state is BallState.LSTFL:
            self.update = self.lustful_update

    def forgetful_update(self):
        player = self.app.player
        if player is None: return
        self.hit_player(player)

        dt = self.app.engine_time-self.last_aggro
        delta = player.body.position-self.body.position
        r = abs(delta)

        if self._going and dt > 10:
            self._going = False
            lores = self.app.tracker['LoreOrePickup']
            for lore in lores:
                try:
                    hit = self.shape.shapes_collide(lore.shape)
                    self.app.remove_entity(lore)
                    self.set_state(BallState.LSTFL)
                    break
                except AssertionError: pass

        if not self._going and dt > 15:
            if r < 80:
                self.last_aggro = self.app.engine_time
                self._going = True

        if self._going:
            self.seek_player(player)

        self.apply_friction(player)

    def lustful_update(self):
        player = self.app.player
        if player is None: return
        self.hit_player(player)

        target = player
        lores = self.app.tracker['LoreOrePickup']

        if len(lores) > 0:
            target = lores[0]

            try:
                hit = self.shape.shapes_collide(target.shape)
                self.lores+= 1
                self.app.remove_entity(target)
                target = player
            except AssertionError: pass

        self.seek_player(target)

        self.apply_friction(player)

    def get_drops(self):
        if random.random() > 1-(self.r-5)/16: #heath drop
            return [HealthPickup(self.app, self.body.position)]
        elif random.random() > 1-self.r/8: #lore/bean
            if random.random() > self.app.field_richness:
                return [BeanPickup(self.app, self.body.position)]
            else:
                return [LoreOrePickup(self.app, self.body.position)]
        elif random.random() > .75 and self.r > 7: #length pickup
            return [LengthPickup(self.app, self.body.position)]
        elif random.random() > 0.97-0.03*self.app.beans:
            if len(self.app.tracker['CoffeePotPickup']) == 0:
                return [CoffeePotPickup(self.app, self.body.position)]
        return []


class Wall(Entity):
    def __init__(self, app, start, end):
        super().__init__(app)
        self.start = start
        self.end = end

        self.body = pm.Body(body_type=pm.Body.STATIC)
        self.shape = pm.Segment(self.body, Vec2d(*start), Vec2d(*end), 0)
        self.shape.friction = 1
        self.shape.collision_type = COLLTYPE_DEFAULT

    def draw(self):
#        pv1 = self.app.flipyv(self.body.position + self.shape.a.cpvrotate(self.body.rotation_vector))
#        pv2 = self.app.flipyv(self.body.position + self.shape.b.cpvrotate(self.body.rotation_vector))
        pv1 = self.body.position + self.shape.a.cpvrotate(self.body.rotation_vector)
        pv2 = self.body.position + self.shape.b.cpvrotate(self.body.rotation_vector)
        pv1 = self.app.jj(pv1)
        pv2 = self.app.jj(pv2)

        pygame.draw.lines(self.app.screen, (0,0,0), False, [pv1, pv2])

    def update(self):
        pass


