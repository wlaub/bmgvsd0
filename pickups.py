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
    cooldown_duration = 0.3
    def __init__(self, app, pos, equipment = None):
        super().__init__(app, pos)

        self.cooldown = self.app.engine_time + self.cooldown_duration

        if equipment is not None:
            self.equipment = equipment
        else:
            self.equipment = self.app.create_entity(self.equipment_name)
        self.equipment.pckp = self

    def on_add(self):
        super().on_add()
        self.cooldown = self.app.engine_time + self.cooldown_duration

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
    track_as = {'SpawnStop'}
    equipment_name = 'RbtcSord'

    def draw_sprite(self):
        p = self.app.jj(self.position)
        pygame.draw.line(self.app.screen, (128,128,128),
                p+Vec2d(0,-1),
                p+Vec2d(0,self.equipment.length-2)
                )
        pygame.draw.line(self.app.screen, (128,128,128),
                p+Vec2d(-1,0),
                p+Vec2d(1,0),
                )


@register
class RckngBallPickup(EquipPckp):
    #TODO
    """
    it might persist the whole body and maybe even create the body on init
    attach the pickup hitbox to the end of the chain
    """
    equipment_name = 'RckngBall'

    def draw_sprite(self):
        self.equipment.draw()

@register
class SkltnPickup(EquipPckp):
    equipment_name = 'Exoskeleton'

@register
class EyesPickup(EquipPckp):
    equipment_name = 'RbtcEyes'

@register
class EulLntrnPickup(EquipPckp):
    track_as = {'SpawnStop'}
    equipment_name = 'EulLntrn'


@register
class BrewPotPckp(EquipPckp):
    """
    a brew pot
    """
    equipment_name = 'BrewPot'
    hype = 5
    energy_of_instantiation = 1
    cooldown_duration = 0.3

    def __init__(self, app, pos, equipment = None):
        super().__init__(app, pos)

    def prepare_shape(self):
        self.w = w = 2
        self.h = h = 7

        xoff = 10
        dx = 0
        dy = 1
        self.front_hand = shape = pm.Poly(self.body, [
                    [-xoff+dx,-h/2+dy],
                    [-xoff-w+dx,-h/2+dy],
                    [-xoff-w+dx,h/2+dy],
                    [-xoff+dx,h/2+dy],
                    ])
        shape.sensor = True
        shape.collision_type = COLLTYPE_DEFAULT

        self.back_hand = shape = pm.Poly(self.body, [
                    [xoff+dx,-h/2+dy],
                    [xoff+w+dx,-h/2+dy],
                    [xoff+w+dx,h/2+dy],
                    [xoff+dx,h/2+dy],
                    ])

        shape.sensor = True
        shape.collision_type = COLLTYPE_DEFAULT

        self.slot_shapes = {
            'back_hand': self.back_hand,
            'front_hand': self.front_hand,
            }

    def add_to_space(self, space):
        space.add(self.body, *self.slot_shapes.values())

    def remove_from_space(self, space):
        space.remove(self.body, *self.slot_shapes.values())

    def draw(self):
        p = self.app.jj(self.body.position)
        color = (0,0,255)
#        if self.player_on:
#            color = (255,0,0)

        for shape in self.slot_shapes.values():
            vertices = []
            for v in shape.get_vertices():
                pv = self.app.jj(v.rotated(self.body.angle)+self.position)
                vertices.append(pv)
            pygame.draw.polygon(self.app.screen, color, vertices, 1)

    def draw_sprite(self):
        p = self.app.jj(self.body.position)
        self.equipment._draw_sprite(p)

    def update(self):
        player = self.app.player

        if player is None: return
        if self.app.beans == 0: return

        self.player_on = False
        for slot_name, shape in self.slot_shapes.items():
            slot = player.get_slot_hit(shape, {slot_name})
            if slot is not None:
                self.player_on = True
                target_slot = slot
                break
            else:
                self.player_on = False

#        if self.app.controller.equip() and self.app.engine_time > self.cooldown:
        if self.app.engine_time > self.cooldown:
            if self.player_on:
                if player.equip_entity(slot, self.equipment):
                    self.app.beans -= 1
                    self.app.start_game()
                    super(EquipPckp, self).on_player(player)




@register
class HealthPickup(Pckp):
    """
    bls'd hair tonic
    """

    def prepare_shape(self):
        self.prepare_circle(4)

    def on_player(self, player):
        extra = max(0,player.health-3)
        player.health += 1/(1+extra)
        super().on_player(player)

@register
class LengthPickup(Pckp):
    """
    you can't quite make it out
    """

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
    """
    its intricate crystal prism weaves light into knowledge
    """

    def prepare_shape(self):
        self.prepare_circle(2)

    def on_add(self):
        deviancy, richness = self.app.field.update_lore()
        self.say(f"lore {deviancy:.2f} {richness:.3f}")
        super().on_add()

    def on_player(self, player):
        self.app.lore_score += 1
        deviancy, richness = self.app.field.update_bean(self.app.field.get('regression'))
        self.say(f"unlore {deviancy:.2f} {richness:.3f}")
        super().on_player(player)

@register
class BeanPickup(Pckp):
    """
    a bean
    """

    def prepare_shape(self):
        self.prepare_circle(2)

    def on_add(self):
        deviancy, richness = self.app.field.update_bean()
        self.say(f"bean {deviancy:.2f} {richness:.3f}")
        super().on_add()

    def on_player(self, player):
        self.app.beans += 1
        deviancy, richness = self.app.field.update_lore(self.app.field.get('regression'))
        self.say(f"unbean {deviancy:.2f} {richness:.3f}")
        super().on_player(player)

@register
class CoffeePotPickup(Pckp):
    """
    a brew pot
    """
    hype = 5
    energy_of_instantiation = 1

    def prepare_shape(self):
        self.prepare_circle(16)

    def on_player(self, player):
        if self.app.beans > 0:
            self.app.beans -= 1
            player.boost_speed(amt=10, dur=10)
            super().on_player(player)

