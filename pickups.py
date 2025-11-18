import math
import random
import time

import pygame

import pymunk as pm
import pymunk.util
from pymunk import Vec2d

from objects import Controller, Entity, COLLTYPE_DEFAULT, Pickup
from guns import Sord

class HealthPickup(Pickup):

    def __init__(self, app, pos):
        super().__init__(app, pos, 4)

    def on_player(self, player):
        extra = max(0,player.health-3)
        player.health += 1/(1+extra)
        super().on_player(player)

class LengthPickup(Pickup):

    def __init__(self, app, pos):
        super().__init__(app, pos, 4)

    def on_player(self, player):
        for sord in self.app.tracker['Sord']:
            sord.offset += Vec2d(1,0)
        super().on_player(player)

class LoreOrePickup(Pickup):

    def __init__(self, app, pos):
        super().__init__(app, pos, 2)

    def on_player(self, player):
        self.app.lore_score += 1
        super().on_player(player)

class BeanPickup(Pickup):

    def __init__(self, app, pos):
        super().__init__(app, pos, 2)

    def on_player(self, player):
        self.app.beans += 1
        super().on_player(player)

class CoffeePotPickup(Pickup):

    def __init__(self, app, pos):
        super().__init__(app, pos, 16)

    def on_player(self, player):
        if self.app.beans > 0:
            self.app.beans -= 1
            player.boost_speed(amt=10, dur=10)
            super().on_player(player)


