import math
import random
import time

import pygame

import pymunk as pm
import pymunk.util
from pymunk import Vec2d

from registry import register, entity_registry

from objects import Controller, Entity, COLLTYPE_DEFAULT, Pckp

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

class EquipPckp(Pckp):
    def __init__(self, app, pos, equipment = None):
        super().__init__(app, pos)

        self.cooldown = self.app.engine_time + 0.5

        if equipment is not None:
            self.equipment = equipment
        else:
            self.equipment = self.app.create_entity(self.equipment_name)

    def prepare_shape(self):
        self.prepare_box(3,3)

    def draw(self):
        self.draw_poly()

    def update(self):
        player = self.app.player

        if player is None: return
        slot = player.get_slot_hit(self.shape, self.equipment.valid_slots)
        if slot is not None:
            self.player_on = True
        else:
            self.player_on = False

        if self.app.controller.equip() and self.app.engine_time > self.cooldown:
            if self.player_on:
                if player.equip_entity(slot, self.equipment):
                    self.app.start_game()
                    super().on_player(player)

@register
class SordPickup(EquipPckp):
    track_as = {'EquipPckp'}
    equipment_name = 'RbtcSord'

@register
class RckngBallPickup(EquipPckp):
    track_as = {'EquipPckp'}
    equipment_name = 'RckngBall'

@register
class SkltnPickup(EquipPckp):
    track_as = {'EquipPckp'}
    equipment_name = 'Exoskeleton'




@register
class HealthPickup(Pckp):

    def prepare_shape(self):
        self.prepare_circle(4)

    def on_player(self, player):
        extra = max(0,player.health-3)
        player.health += 1/(1+extra)
        super().on_player(player)

@register
class LengthPickup(Pckp):

    def prepare_shape(self):
        self.prepare_circle(4)

    def on_player(self, player):
        for slot in {'front_hand', 'back_hand'}:
            sord = player.slots[slot]
            if sord is not None:
                sord.grow(1)
                break #TODO yes or no?
        super().on_player(player)

@register
class LoreOrePickup(Pckp):

    def prepare_shape(self):
        self.prepare_circle(2)

    def on_player(self, player):
        self.app.lore_score += 1
        super().on_player(player)

@register
class BeanPickup(Pckp):

    def prepare_shape(self):
        self.prepare_circle(2)

    def on_player(self, player):
        self.app.beans += 1
        super().on_player(player)

@register
class CoffeePotPickup(Pckp):

    def prepare_shape(self):
        self.prepare_circle(16)

    def on_player(self, player):
        if self.app.beans > 0:
            self.app.beans -= 1
            player.boost_speed(amt=10, dur=10)
            super().on_player(player)


