import math
import random
import time

import pygame

import pymunk as pm
import pymunk.util
from pymunk import Vec2d

from objects import Controller, Entity, COLLTYPE_DEFAULT

class Sord(Entity):
    def __init__(self, app, parent):
        self.app = app
        self.parent = parent
        self.last_hit = self.app.engine_time

        self.offset = self.parent.front_hand_position + Vec2d(8,0)
        x,y = self.offset

        self.body = pm.Body(body_type = pm.Body.KINEMATIC)
        self.body.position = parent.body.position + self.offset
        self.shape = pm.Circle(self.body, 0.5)
        self.shape.sensor=True
        self.shape.collision_type = COLLTYPE_DEFAULT

        self.lines = [
                [
                self.parent.front_hand_position,
                self.offset,
                ],
                [
                self.parent.front_hand_position + Vec2d(1,-1),
                self.parent.front_hand_position + Vec2d(1,1)
                ],
            ]

        self.app.add_entity(self)

    def update(self):
        controller = self.app.controller
        player = self.parent

        now = self.app.engine_time
        dt = now-self.last_hit

        self.body.position = player.body.position+self.offset
        for ball in self.app.tracker['Ball']:
            try:
                hit = self.shape.shapes_collide(ball.shape)
                dmg = 1
                dv = player.body.velocity.x - ball.body.velocity.x
#                print(dv)
                if dv > 31:
                    dmg = 2

                if dv > -5:
                    ball.get_hit(dmg)
            except AssertionError: pass

    def draw(self):
        p = self.parent.body.position
        pygame.draw.line(self.app.screen, (128,128,128),
                p+self.parent.front_hand_position,
                p+self.offset
                )
        pygame.draw.line(self.app.screen, (128,128,128),
                p+self.lines[1][0],
                p+self.lines[1][1],
                )




