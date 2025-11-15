import math
import random
import time

import pygame

import pymunk as pm
import pymunk.util
from pymunk import Vec2d

from objects import Controller, Entity, COLLTYPE_DEFAULT

class Ball(Entity):
    def __init__(self, app, pos, m, r):
        self.app = app
        self.m = m
        self.r = r
        self.moment = pm.moment_for_circle(m, 0, r)
        self.body = body = pm.Body(m, self.moment)
        body.position = Vec2d(*pos)

        self.shape = shape = pm.Circle(body, r)
#        shape.friction = 1.5
        shape.collision_type = COLLTYPE_DEFAULT

    def draw(self):
        v = self.body.position + self.shape.offset.cpvrotate(self.body.rotation_vector)
        p = self.app.flipyv(v)

        pygame.draw.circle(self.app.screen, pygame.Color("blue"), p, int(self.r), 2)

    def update(self):
        player = self.app.player

        delta = player.body.position-self.body.position
        delta /=abs(delta)
#        self.body.velocity = delta*70
        self.body.apply_force_at_local_point(delta*1000*self.m)

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
        pv1 = self.app.flipyv(self.body.position + self.shape.a.cpvrotate(self.body.rotation_vector))
        pv2 = self.app.flipyv(self.body.position + self.shape.b.cpvrotate(self.body.rotation_vector))
        pygame.draw.lines(self.app.screen, (0,0,0), False, [pv1, pv2])

    def update(self):
        pass


