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

class Spnlþ(Entity):

    def draw(self):
        color = (0,0,255)
        for body, shapes in self.body_map.items():
            for shape in shapes:
                vertices = []
                for v in shape.get_vertices():
                    p = self.app.jj(v.rotated(body.angle)+body.position)
                    vertices.append(p)
                pygame.draw.polygon(self.app.screen, color, vertices, 1)

        if (z := self.app.flags.getv('_draw_spawn_bounds', 0)) > 0:
            self.app.camera.draw_boundary(z, 50)


    def add_to_space(self, space):
        for body, shapes in self.body_map.items():
            space.add(body, *shapes)
    def remove_from_space(self, space):
        for body, shapes in self.body_map.items():
            space.remove(body, *shapes)

    def update(self):

        pass


@register
class BallSpnlþ(Spnlþ):
    def __init__(self, app, pos):
        super().__init__(app)

        self.body = body = pm.Body(body_type = pymunk.Body.STATIC)
        body.position = Vec2d(*pos)

        shapes = []

        r = 49*7
        s = 67*7
        da = -math.pi/7
        for i in range(3):
            dx = r*math.cos(2*i*math.pi/3+da)
            dy = r*math.sin(2*i*math.pi/3+da)
            shape = pm.Poly(body, [
                (dx-s/2, dy-s/2),
                (dx+s/2, dy-s/2),
                (dx+s/2, dy+s/2),
                (dx-s/2, dy+s/2),
                ])
            shapes.append(shape)

        self.body_map = {self.body: shapes}

    def spawn(self):
        t = random.random()
        pos = self.app.camera.get_boundary_point(t, 50)
        if random.random() < 0.15:
            new_entity = self.app.create_entity('FgtflBall', pos)
        else:
            new_entity = self.app.create_entity('Ball', pos)

        return [new_entity]


@register
class ZippySpnlþ(Spnlþ):
    def __init__(self, app, pos):
        super().__init__(app)

        self.body = body = pm.Body(body_type = pymunk.Body.STATIC)
        body.position = Vec2d(*pos)


        shapes = []

        _r = 42*7
        s = 35*7
        da = -math.pi/7
        for i in range(7):
            ix = i-3
            r = _r*abs(ix)**0.5
            if ix < 0:
                r*= -1
            a = (abs(ix)**2)*2*math.pi/28
            dx = r*math.cos(a+da)
            dy = r*math.sin(a+da)
            shape = pm.Poly(body, [
                (dx-s/2, dy-s/2),
                (dx+s/2, dy-s/2),
                (dx+s/2, dy+s/2),
                (dx-s/2, dy+s/2),
                ])
            shapes.append(shape)

        self.body_map = {self.body: shapes}

    def spawn(self):
        t = random.random()
        pos = self.app.camera.get_boundary_point(t, 50)

        z = len(self.app.tracker['BeanPickup'])-2
        if len(self.app.tracker['Zbln']) == 0:
            z+= len(self.app.tracker['Zeeky'])*3

        if len(self.app.tracker['Zippy']) == 0 and random.random() < 0.2*z:
            return [self.app.create_entity('Zippy', pos)]

        return []

