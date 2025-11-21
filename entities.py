import math
import random
import time
import enum

import pygame

import pymunk as pm
import pymunk.util
from pymunk import Vec2d

from registry import register, entity_registry

from objects import Controller, Entity, COLLTYPE_DEFAULT, BallEnemy
#from pickups import HealthPickup, LoreOrePickup, LengthPickup, BeanPickup, CoffeePotPickup

"""
need a debug console that can spawn enemies and stuff

and eye boss drops portable camera pickup
"""

@register
class Zippy(BallEnemy):
    track_as = {'Enemy'}
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

        if not self.going and (self.app.engine_time-self.cooldown > 0 or self.app.camera.contains(self.position, 1)):
#            print('going')
            self.going = True
            self.can_stop = False


            target = player
            for bean in beans:
                if self.app.camera.contains(bean.position, 0):
                    self.say('bean')
                    target = bean
                    break

            delta = target.position-self.position
            delta /= abs(delta)
            self.direction = delta*self.speed
            self.friction = -10*self.m

        if self.going:

            for bean in beans:
                try:
                    hit = self.shape.shapes_collide(bean.shape)
                    self.say('bwned')
                    self.beans+= 1
                    self.app.remove_entity(bean)
                    if self.beans == 7:
                        self.app.remove_entity(self)
                        self.app.spawn_entity('Zeeker', self.position)
                        return

                except AssertionError: pass

            self.body.apply_force_at_local_point(self.direction)

            if not self.can_stop and self.app.camera.contains(self.position, 0):
                self.say('can stop')
                self.can_stop = True

            if self.can_stop and not self.app.camera.contains(self.position, 50):
                self.say('stopping')
                self.going = False
                self.cooldown = self.app.engine_time+5
                self.friction = -100*self.m

        self.apply_friction(player)

    def get_drops(self):
        result = []
        if random.random() < 0.1 and  len(self.app.tracker['CoffeePotPickup']) == 0:
           result.append(self.app.create_entity('CoffeePotPickup', self.position))

        result.append(self.app.create_entity('BeanPickup', self.position))
        t = random.random()
        M = 7 + int(self.beans/7)*7
        N = int((M+1)*t)
        if N > 0:
            a = random.random()
            for i in range(N+1):
                aa = a+2*math.pi*i/M
                dx,dy = random.random()-0.5, random.random()-0.5
                r = 7+2*i%2
                result.append(self.app.create_entity('LoreOrePickup',
                    self.position + Vec2d(r*math.cos(aa)+dx, r*math.sin(aa)+dy)
                    ))

        return result


@register
class Zeeker(BallEnemy):
    track_as = {'Enemy'}
    def __init__(self, app, pos):
        super().__init__(app, pos, 3, 32*32/1.8, 3, 1200)
        self.direction = Vec2d(0,0)
        self.going = False
        self.cooldown = self.app.engine_time
        self.can_stop = False
        self.beans = 0
        self.target = None
        self.target_position = None

        self.zeek_radius = 90


    def update(self):
        player = self.app.player
        if player is None: return
        self.hit_player(player)

        beans = self.app.tracker['Zeeker']

        if self.target is None:
            self.target = player
            self.target_position = self.target.position

        if not self.going:
            self.say('going')
            self.going = True
            self.can_stop = False
            for bean in beans:
                if bean is not self and self.app.camera.contains(bean.position, 0):
                    self.say('hello there')
                    self.target = bean
                    break
            else:
                self.target = player

            self.target_position = self.target.position
            delta = self.target_position-self.position
            r = abs(delta)
            r2=r

            if r != 0:
                delta /= r
                self.direction = delta*self.speed
                self.friction = -10*self.m
            else:
                self.going = False
                self.direction = Vec2d(0,0)
        else:
            delta = self.target_position-self.position
            r = abs(delta)
            r2 = abs(self.target.position-self.position)


        if self.going:
            for bean in beans:
                if bean is self: continue
                try:
                    hit = self.shape.shapes_collide(bean.shape)
                    self.say('blessed union')
                    #TODO merge into new enemy
                    self.app.remove_entity(bean)
                    self.app.remove_entity(self)
                    return
                except AssertionError: pass

            self.body.apply_force_at_local_point(self.direction)

            if not self.can_stop and min(r,r2) < self.zeek_radius-5:
                self.say('can stop')
                self.can_stop = True

            if self.can_stop and max(r,r2) > self.zeek_radius:
                self.say('stopping')
                self.going = False
                self.cooldown = self.app.engine_time+5
                self.friction = -100*self.m

        self.apply_friction(player)

    def get_drops(self):
        result = []
        #TODO
        return result



class BallState(enum.Enum):
    NORML = 0
    FGTFL = 1
    LSTFL = 2

@register
class Ball(BallEnemy):
    track_as = {'Enemy'}

    update_map = {
        BallState.NORML: BallEnemy.update,
        }

    def __str__(self):
        p = self.position
        return f'{super().__str__()} {self.state}'

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
        delta = player.position-self.position
        r = abs(delta)

        if self._going and dt > 10:
            self._going = False
            lores = self.app.tracker['LoreOrePickup']
            for lore in lores:
                try:
                    hit = self.shape.shapes_collide(lore.shape)
                    self.say("what's this?")
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
            return [self.app.create_entity('HealthPickup', self.position)]
        elif random.random() > 1-self.r/8: #lore/bean
            if random.random() > self.app.field_richness:
                return [self.app.create_entity('BeanPickup', self.position)]
            else:
                return [self.app.create_entity('LoreOrePickup', self.position)]
        elif random.random() > .75 and self.r > 7: #length pickup
            return [LengthPickup(self.app, self.position)]
        elif random.random() > 0.97-0.03*self.app.beans:
            if len(self.app.tracker['CoffeePotPickup']) == 0:
                return [self.app.create_entity('CoffeePotPickup', self.position)]
        return []

@register
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


