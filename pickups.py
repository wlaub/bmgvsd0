import math
import random
import time

import pygame

import pymunk as pm
import pymunk.util
from pymunk import Vec2d

from registry import register, entity_registry

from objects import Controller, Entity, COLLTYPE_DEFAULT, Pickup

"""
Pck'p:
* tracks if targets ares on
* tracks if targets haves been off

hitbox is circle of variable radius
hitbox targets player
pick up on touch [if has been off]

dren:
what it does on touch
how big it is
whether player has to step off first

EquipPck'p:
* tracks if targets ares on
* tracks if targets haves been off

hitbox is 3x3 square
hitbox targets all valid equipment slots
equips the entity when target is on and current equipment is different and slot is valid and activates (on button?)
? signals if any target is on

dren:
which valid slots
which equipment entity

TODO make sure that when equipment drops, it retains the original equipment entity as its entity instead of creating a new one
"""

@register
class SordPickup(Pickup):
    track_as = {'EquipPckp'}

    def __init__(self, app, pos):
        super(Pickup, self).__init__(app)
        self.body = body = pm.Body(body_type = pymunk.Body.STATIC)
        body.position = Vec2d(*pos)

        self.w = 3
        self.h = 3

        self.shape = shape = pm.Poly.create_box(body, (self.w, self.h))
        shape.sensor = True
        shape.collision_type = COLLTYPE_DEFAULT
        self.player_on = False

    def draw(self):
        p = self.app.jj(self.body.position)
        color = (0,0,255)

#        if self.player_on:
#            color = (255,0,0)

        vertices = []
        for v in self.shape.get_vertices():
            p = self.app.jj(v.rotated(self.body.angle)+self.position)
            vertices.append(p)
        pygame.draw.polygon(self.app.screen, color, vertices, 1)


    def update(self):
        player = self.app.player
        if player is None: return
        slot = player.get_slot_hit(self.shape, {'front_hand'})
        if slot is not None:
            self.player_on = True
        else:
            self.player_on = False

        if self.app.controller.equip():
            if self.player_on:
                if player.equip(slot, 'RbtcSord'):
                    self.app.start_game()
                    super().on_player(player)


    def on_player(self, player):
        #TODO formalize player_on for pickups
        self.player_on = True
        if self.app.controller.equip():

#            sord = self.app.create_entity('Sord', player)
            if player.equip('front_hand', 'Sord'):
                self.app.start_game()
                super().on_player(player)


@register
class HealthPickup(Pickup):

    def __init__(self, app, pos):
        super().__init__(app, pos, 4)

    def on_player(self, player):
        extra = max(0,player.health-3)
        player.health += 1/(1+extra)
        super().on_player(player)

@register
class LengthPickup(Pickup):

    def __init__(self, app, pos):
        super().__init__(app, pos, 4)

    def on_player(self, player):
        for sord in self.app.tracker['Sord']:
            sord.offset += Vec2d(1,0)
        super().on_player(player)

@register
class LoreOrePickup(Pickup):

    def __init__(self, app, pos):
        super().__init__(app, pos, 2)

    def on_player(self, player):
        self.app.lore_score += 1
        super().on_player(player)

@register
class BeanPickup(Pickup):

    def __init__(self, app, pos):
        super().__init__(app, pos, 2)

    def on_player(self, player):
        self.app.beans += 1
        super().on_player(player)

@register
class CoffeePotPickup(Pickup):

    def __init__(self, app, pos):
        super().__init__(app, pos, 16)

    def on_player(self, player):
        if self.app.beans > 0:
            self.app.beans -= 1
            player.boost_speed(amt=10, dur=10)
            super().on_player(player)


