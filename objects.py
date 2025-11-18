import random
import math

import pygame

from pygame.locals import *

import pymunk as pm
import pymunk.util
from pymunk import Vec2d

COLLTYPE_DEFAULT = 0

class Controller:
    button_map = {
    'a': 0,
    'b': 1,
    'x': 2,
    'y': 3,
    'rb': 5,
    'lb': 4,
    'select': 6,
    'start': 7,
    'xbox': 8,
    'l3': 9,
    'r3': 10,
    }

    axis_map = {
    'lx': 0,
    'ly': 1,
    'lt': 2,
    'rx': 3,
    'ry': 4,
    'rt': 5,
    }

    def __init__(self, app):
        self.app = app
        self.joystick = pygame.joystick.Joystick(0)

    def get_left_stick(self):
        keys = self.app.keys
        lrud = [keys[x] for x in (K_LEFT, K_RIGHT, K_UP, K_DOWN)]
        if any(lrud):
            L,R,U,D = lrud
            xpos = 1 if R else -1 if L else 0
            ypos = 1 if D else -1 if U else 0
            xpos += random.random()*0.05-0.025
            ypos += random.random()*0.05-0.025
            return (xpos, ypos)

        xpos = self.joystick.get_axis(self.axis_map['lx'])
        ypos = self.joystick.get_axis(self.axis_map['ly'])
        return (xpos, ypos)

    def get_right_trigger(self):
        if self.app.keys[K_SPACE]:
            return True
        return self.joystick.get_axis(self.axis_map['rt']) > 0.5

    def get_button(self, name):
        return self.joystick.get_button(self.button_map[name])


class Entity:
    track_as = []
    def __init__(self, app, parent = None):
        self.app = app
        self.parent = parent
        self.last_hit = -100
        self.grace_time = 0.2
        self.health = 1

    def draw(self):
        pass
    def update(self):
        pass
    def add_to_space(self, space):
        space.add(self.body, self.shape)
    def remove_from_space(self, space):
        space.remove(self.body, self.shape)

    def on_add(self):
        pass

    def on_remove(self):
        pass

    def get_hit(self, dmg):
      pass


    def _basic_hit_spell(self, dmg):
        if self.app.engine_time - self.last_hit > self.grace_time:
            self.health -= dmg
            self.last_hit = self.app.engine_time
            if self.health <= 0:
                self.app.remove_entity(self)
                return True
        return False

class Pickup(Entity):
    def __init__(self, app, pos, r):
        super().__init__(app)
        self.body = body = pm.Body(body_type = pymunk.Body.STATIC)
        body.position = Vec2d(*pos)

        self.r = r
        self.shape = shape = pm.Circle(body, self.r)
        shape.sensor = True
        shape.collision_type = COLLTYPE_DEFAULT

    def draw(self):
        p = self.body.position
        color = (0,0,255)
        pygame.draw.circle(self.app.screen, color, p, int(self.r), 2)

    def update(self):
        player = self.app.player
        if player is None: return
        try:
            hit = self.shape.shapes_collide(player.shape)
            self.on_player(player)

        except AssertionError: pass

    def on_player(self, player):
        self.app.remove_entity(self)


