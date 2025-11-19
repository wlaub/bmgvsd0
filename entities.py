import math
import random
import time

import pygame

import pymunk as pm
import pymunk.util
from pymunk import Vec2d

from objects import Controller, Entity, COLLTYPE_DEFAULT, BallEnemy
from pickups import HealthPickup, LoreOrePickup, LengthPickup, BeanPickup, CoffeePotPickup

"""
what if like a forgetful ball that stops on top of a bean
with the bean centered turned into an EyeBall that drops
like the camera upgrade


diver enemy targets player when it comes on screen and goes until offscreen
"""

class Ball(BallEnemy):
    def __init__(self, app, pos):
        r= 4+4*random.random()
        m = r*r/1.8
        h = r/4
        super().__init__(app, pos, r, m, h)

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


class ForgetfulBall(Ball):
    track_as = ['Ball']
    def __init__(self, app, pos):
        super().__init__(app, pos)
#        self.last_aggro = self.app.engine_time
        self.last_aggro = 0

    def update(self):
        player = self.app.player
        if player is None: return
        self.hit_player(player)

        dt = self.app.engine_time-self.last_aggro
        delta = player.body.position-self.body.position
        r = abs(delta)

        go = False
        if dt < 10:
            go = True
        elif dt > 15:
            if r < 80:
                self.last_aggro = self.app.engine_time
                go = True

        if go:
            self.seek_player(player)

        self.apply_friction(player)



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


