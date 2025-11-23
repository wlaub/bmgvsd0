import random
import math
import enum

import pygame

from pygame.locals import *

import pymunk as pm
import pymunk.util
from pymunk import pygame_util
from pymunk import Vec2d

from registry import register, entity_registry

COLLTYPE_DEFAULT = 0

class ControlType(enum.Enum):
    joy = 0
    key = 1

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
        self.last_kind = ControlType.joy

        self.last_stick = (0,0)

    def get_left_stick(self):
        keys = self.app.keys
        lrud = [keys[x] for x in (K_LEFT, K_RIGHT, K_UP, K_DOWN)]
        if any(lrud):
            L,R,U,D = lrud
            xpos = 1 if R else -1 if L else 0
            ypos = 1 if D else -1 if U else 0
            xpos += random.random()*0.05-0.025
            ypos += random.random()*0.05-0.025
            self.last_kind = ControlType.key
            return (xpos, ypos)

        xpos = self.joystick.get_axis(self.axis_map['lx'])
        ypos = self.joystick.get_axis(self.axis_map['ly'])
        if (xpos, ypos) != self.last_stick:
            self.last_kind = ControlType.joy
            self.last_stick = (xpos, ypos)

        return (xpos, ypos)

    def get_right_trigger(self):
        if self.app.keys[K_SPACE]:
            self.last_kind = ControlType.key
            return True
        if self.joystick.get_axis(self.axis_map['rt']) > 0.5:
            self.last_kind = ControlType.joy
            return True
        return False

    def get_button(self, name):
        return self.joystick.get_button(self.button_map[name])

class Camera:
    def __init__(self, app, parent, position, scale):
        self.app = app
        self.parent = parent

        self.reference_position = position
        self.set_scale(scale)
        self.update_scale()
        self.update_position(position)

    def s2w(self, pos):
        pos = Vec2d(*pos)/self.scale
        pos += self.half_off
        return pos

    def set_scale(self, scale):
        self.pending_scale = scale

    def update_scale(self):
        if self.pending_scale is not None:
            self.scale = scale = self.pending_scale
            self.w = self.app.ws/scale
            self.h = self.app.hs/scale

            self.half_off = Vec2d(-self.w/2, -self.h/2)
            self.screen = pygame.Surface((self.w, self.h))

            self.app.screen = self.screen
            self.app.draw_options = pygame_util.DrawOptions(self.screen)

            self.pending_scale = None

            self.update_position(self.reference_position)

    def update_position(self, position = None):
        if position is None and self.parent is None:
            return

        if self.parent is not None:
            self.reference_position = self.parent.body.position

        elif position is not None:
            self.reference_position = Vec2d(*position)
        self.position = self.reference_position+self.half_off

        self.left = self.position.x
        self.right = self.position.x+self.w
        self.up = self.position.y
        self.down = self.position.y+self.h

        self.lrud = (self.left, self.right, self.up, self.down)

    def update(self):
        self.update_position()

    def contains(self, pos, margin=0):
        x,y = pos
        return x > self.left-margin and x < self.right+margin and y > self.up-margin and y < self.down+margin

class Entity:
    track_as = set()

    def __str__(self):
        p = self.position
        name = self.__class__.__name__
        return f'E{self.eid:05} {p.x:6.1f} {p.y:6.1f} {name}'

    def __init__(self, app, parent = None):
        self.app = app
        self.parent = parent
        self.last_hit = -100
        self.grace_time = 0.2
        self.health = 1
        self.vocal = False
        self.eid = self.app.get_eid()

    def __hash__(self):
        return self.eid

    def say(self, text):
        if self.vocal:
            print(text)

    @property
    def position(self):
        return self.body.position

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

class Equipment(Entity):
    valid_slots = []
    is_feets = False

class BallEnemy(Entity):
    def __init__(self, app, pos, r, m, health, speed=150, friction =-10):
        super().__init__(app)
        self.r = r
        self.m = m
        self.speed = speed*m
        self.friction = friction*m

        self.moment = pm.moment_for_circle(m, 0, r)
        self.body = body = pm.Body(m, self.moment)
        body.position = Vec2d(*pos)

        self.shape = shape = pm.Circle(body, r)
#        shape.friction = 1.5
        shape.collision_type = COLLTYPE_DEFAULT

        self.health = health

    def draw(self):
        p = self.body.position + self.shape.offset.cpvrotate(self.body.rotation_vector)
        p = self.app.jj(p)

        color = (0,0,255)
        if self.app.engine_time-self.last_hit < 0.08:
            color = (255,0,0)

        pygame.draw.circle(self.app.screen, color, p, int(self.r), 2)


    def hit_player(self, player, dmg=1):
        try:
            hit = self.shape.shapes_collide(player.shape)
            player.get_hit(dmg)
        except AssertionError: pass

    def seek_player(self, player):
        delta = player.body.position-self.body.position
        delta /= abs(delta)
        self.body.apply_force_at_local_point(delta*self.speed)

    def apply_friction(self, player):
        friction = self.body.velocity*self.friction
        self.body.apply_force_at_local_point(friction)

    def update(self):
        self.normal_update()

    def normal_update(self):
        player = self.app.player
        if player is None: return
        self.hit_player(player)
        self.seek_player(player)
        self.apply_friction(player)

    def get_hit(self, dmg):
        dead = self._basic_hit_spell(dmg)
        if dead:
            for drop in self.get_drops():
                self.app.add_entity(drop)
            self.app.remove_entity(self)

    def get_drops(self):
        return []


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
        p = self.app.jj(self.body.position)
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


