import math
import random
import time

import pygame

import pymunk as pm
import pymunk.util
from pymunk import Vec2d

from objects import Controller, Entity, COLLTYPE_DEFAULT

class HealthPickup(Entity):

    def __init__(self, app, pos):
        super().__init__()
        self.app = app
        self.body = body = pm.Body(body_type = pymunk.Body.STATIC)
        body.position = Vec2d(*pos)

        self.r = 4
        self.shape = shape = pm.Circle(body, self.r)
#        shape.friction = 1.5
        shape.sensor = True
        shape.collision_type = COLLTYPE_DEFAULT

    def draw(self):
        p = self.body.position

        color = (0,0,255)

        pygame.draw.circle(self.app.screen, color, p, int(self.r), 2)

    def update(self):
        player = self.app.player
        try:
            hit = self.shape.shapes_collide(player.shape)

            extra = max(0,player.health-3)
            player.health += 1/(1+extra)

            self.app.remove_entity(self)
        except: AssertionError



class LoreOrePickup(Entity):

    def __init__(self, app, pos):
        super().__init__()
        self.app = app
        self.body = body = pm.Body(body_type = pymunk.Body.STATIC)
        body.position = Vec2d(*pos)

        self.r = 2
        self.shape = shape = pm.Circle(body, self.r)
#        shape.friction = 1.5
        shape.sensor = True
        shape.collision_type = COLLTYPE_DEFAULT

    def draw(self):
        p = self.body.position

        color = (0,0,255)

        pygame.draw.circle(self.app.screen, color, p, int(self.r), 2)

    def update(self):
        player = self.app.player
        try:
            hit = self.shape.shapes_collide(player.shape)
            self.app.lore_score += 1
            self.app.remove_entity(self)
        except: AssertionError




