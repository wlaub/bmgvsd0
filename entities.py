import math
import random
import time

import pygame

import pymunk as pm
import pymunk.util
from pymunk import Vec2d

from objects import Controller, Entity, COLLTYPE_DEFAULT
from pickups import HealthPickup, LoreOrePickup, LengthPickup

class Ball(Entity):
    def __init__(self, app, pos):
        super().__init__()
        self.app = app
        self.r =r= 4+4*random.random()
        self.m = m = r*r/1.8


        self.moment = pm.moment_for_circle(m, 0, r)
        self.body = body = pm.Body(m, self.moment)
        body.position = Vec2d(*pos)

        self.shape = shape = pm.Circle(body, r)
#        shape.friction = 1.5
        shape.collision_type = COLLTYPE_DEFAULT

        self.health = r/4

    def draw(self):
        p = self.body.position + self.shape.offset.cpvrotate(self.body.rotation_vector)

        color = (0,0,255)
        if self.app.engine_time-self.last_hit < 0.08:
            color = (255,0,0)

        pygame.draw.circle(self.app.screen, color, p, int(self.r), 2)

    def update(self):
        player = self.app.player
        if player is None: return

        delta = player.body.position-self.body.position
        delta /=abs(delta)
        self.body.apply_force_at_local_point(delta*150*self.m)

        friction = self.body.velocity*-10*self.m
        self.body.apply_force_at_local_point(friction)

    def get_hit(self, dmg):
        dead = self._basic_hit_spell(dmg)
        if dead:

            if random.random() > 1-(self.r-5)/16:
                self.app.add_entity(HealthPickup(self.app, self.body.position))
            elif random.random() > 1-self.r/8:
                self.app.add_entity(LoreOrePickup(self.app, self.body.position))
            elif random.random() > .75 and self.r > 7:
                self.app.add_entity(LengthPickup(self.app, self.body.position))

class ForgetfulBall(Ball):
    track_as = ['Ball']
    def __init__(self, app, pos):
        super().__init__(app, pos)
#        self.last_aggro = self.app.engine_time
        self.last_aggro = 0

    def update(self):
        player = self.app.player

        if player is None:
            return

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
            delta /= r
            self.body.apply_force_at_local_point(delta*150*self.m)

        friction = self.body.velocity*-10*self.m
        self.body.apply_force_at_local_point(friction)



class Wall(Entity):
    def __init__(self, app, start, end):
        self.app = app
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

        pygame.draw.lines(self.app.screen, (0,0,0), False, [pv1, pv2])

    def update(self):
        pass


