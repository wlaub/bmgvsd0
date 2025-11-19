import sys, os

import math
import random
import datetime
import time
import json

import pygame

import pymunk as pm
import pymunk.util
from enum import Enum

from pymunk import Vec2d

from objects import Controller, Entity, COLLTYPE_DEFAULT
from entities import Ball, Wall
from pickups import HealthPickup
from guns import Sord
from feets import Leg, Exoskeleton, StepState

class Player(Entity):
    debug_draw = False
    def __init__(self, app, pos):
        super().__init__(app)
        self.health = 3
        self.grace_time = 1
        self.app = app
        self.m = m = 10000
        self.body = body = pm.Body(self.m, float("inf"))
        body.position = Vec2d(*pos)

        self.fast_walk = False
        self.stick_active = False
        self.aim = Vec2d(0,0)

        self.w =w= 10
        self.h =h= 17
        self.hips = 1
        self.leg = 3

        self.slots = {}

        self.base_slots = {
            'front_hand', 'back_hand',
            'legs', 'feets', 'eyes'
            }

        for slot in self.base_slots:
            self.create_slot(slot)

        self.shoulder_position = Vec2d(0,-5)
        self.front_hand_position = Vec2d(3,-5)
        self.front_elbow_position = Vec2d(2,-5)
        self.front_unarmed_position = Vec2d(2,-4)

        self.back_hand_position = Vec2d(-3,-5)
        self.back_unarmed_position = Vec2d(-2,-4)
        self.back_elbow_position = Vec2d(-2,-5)

        #stuff
        self.bean_hot_counter = 0
        self.bean_hot_potency = 1
        self.walk_rate = 1

        #physics
        self.shape = pm.Poly(self.body, [
            (-w/2, -h+w),
            (-w/2, -h),
            (w/2, -h),
            (w/2, -h+w),
            ])
        self.shape.collision_type = COLLTYPE_DEFAULT

        #layugs
        self.left_leg = Leg(self.app, self, pos, self.leg, (-self.hips,0))
        self.right_leg = Leg(self.app, self, pos, self.leg, (self.hips,0))

        self.legs = [self.left_leg, self.right_leg]
        self.active_leg_idx = 0
        self.active_leg = self.legs[self.active_leg_idx]

        #feets
        self.feets = []
        feets = Exoskeleton(self.app, self, pos, self.hips)
        self.equip('legs', feets)

        #hayunds
        sord = Sord(self.app, self)
        self.equip('front_hand', sord)

        #body control
        self.center_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.set_center_position()
        self.app.space.add(self.center_body)

        c = pymunk.DampedSpring(self.center_body, self.body, (0,0), (0,0), 0, m*1000,1000000)
        self.app.space.add(c)

    def create_slot(self, slot):
        if not slot in self.slots.keys():
            self.slots[slot] = None

    def equip(self, slot, entity):
        if slot in entity.valid_slots and self.slots[slot] is None:
            self.slots[slot] = entity
            self.app.add_entity(entity)
            if entity.is_feets:
                self.feets.append(entity)

    def unequip(self, slot):
        if self.slots[slot] is not None:
            entity = self.slots[slot]
            self.app.remove_entity(entity)
            self.slots[slot] = None
            if entity.is_feets:
                self.feets.remove(entity)


    def boost_speed(self, amt, dur):
        if self.bean_hot_counter > self.app.engine_time:
            return
        self.bean_hot_potency = amt
        self.bean_hot_counter = self.app.engine_time+dur

    def set_center_position(self):
        left = self.left_leg.foot_body.position
        right = self.right_leg.foot_body.position

        #the body center should go down when the feet are far apart
        dist = max(0,abs(left-right)-self.w)
        alpha = 1-min(1,dist/(self.leg*2))

        self.center_body.position = Vec2d(
                (left.x+right.x)/2, (left.y+right.y)/2-self.leg*alpha
                )

    def add_to_space(self, space):
        space.add(self.body, self.shape)

    def on_remove(self):
        for slot, entity in self.slots.items():
            self.unequip(slot)

        self.app.player = None
        self.write_session_stats()

    def write_session_stats(self):
        now = datetime.datetime.now()
        filename=now.strftime('%Y%m%d_%H%M%S.json')
        stats = {
            'now': now.isoformat(),
            'then': self.app.startup_time.isoformat(),
            'title': self.app.title,
            'seed': self.app.seed,
            'health': self.health,
            'time_of_death': self.app.engine_time,
            'lore_score': self.app.lore_score,
            'beans': self.app.beans,
           }
        print(f'{stats["lore_score"]} {stats["title"]} {stats["seed"]}')
        print(json.dumps(stats, indent=2))
        with open(os.path.join('stats/', filename) ,'w') as fp:
            json.dump(stats, fp)


    def draw(self):
        body = self.body
        poly = self.shape
        p = body.position #+ self.shape.offset.cpvrotate(self.body.rotation_vector)
        p = self.app.jj(p)

        #head
        color = (240,192,160)
        if ( self.app.engine_time-self.last_hit >= self.grace_time-0.1 or
             int(7*(self.app.engine_time-self.last_hit)/self.grace_time) % 2 == 0
            ):
            pygame.draw.rect(self.app.screen, color,
                pygame.Rect(p+Vec2d(-self.w/2, -self.h), (self.w, self.w))
                )
        pygame.draw.rect(self.app.screen, (0,0,0),
            pygame.Rect(p+Vec2d(-self.w/2-1, -self.h-1), (self.w+2, self.w+2)),
            1
            )
        #hair
        pygame.draw.rect(self.app.screen, (128,128,128),
            pygame.Rect(p+Vec2d(-self.w/2, -self.h), (5, self.health))
            )
        #eye
        pygame.draw.rect(self.app.screen, (0,0,128),
            pygame.Rect(p+Vec2d(4, -self.h+2), (2, 2))
            )
        #body
        pygame.draw.line(self.app.screen, (0,0,0), p, p+Vec2d(0,-6))
        pygame.draw.line(self.app.screen, (0,0,0), p-Vec2d(-1,0), p-Vec2d(1,0))
        #arms
        if self.slots['front_hand'] is not None:
            pygame.draw.line(self.app.screen, (0,0,0),
                p+self.shoulder_position,
                p+self.front_hand_position,
                )
        else:
            pygame.draw.line(self.app.screen, (0,0,0),
                p+self.shoulder_position,
                p+self.front_elbow_position,
                )
            pygame.draw.line(self.app.screen, (0,0,0),
                p+self.front_elbow_position,
                p+self.front_unarmed_position,
                )
        if self.slots['back_hand'] is not None:
            pygame.draw.line(self.app.screen, (0,0,0),
                p+self.shoulder_position,
                p+self.back_hand_position,
                )
        else:
            pygame.draw.line(self.app.screen, (0,0,0),
                p+self.shoulder_position,
                p+self.back_elbow_position,
                )
            pygame.draw.line(self.app.screen, (0,0,0),
                p+self.back_elbow_position,
                p+self.back_unarmed_position,
                )


        #layugs
        for leg in self.legs:
            leg.draw()

    def get_hit(self, dmg):
        self._basic_hit_spell(dmg)

    def update(self):
        self.friction =-10

        #boosts
        dt = self.bean_hot_counter - self.app.engine_time
        if dt > 0:
            self.walk_speed = self.bean_hot_potency
        else:
            self.walk_speed = 1

        #controls
        speed = abs(self.body.velocity)

        controller = self.app.controller

        self.fast_walk = fast_walk = controller.get_right_trigger()
        dx, dy = controller.get_left_stick()
        self.stick_active = stick_active = (dx*dx+dy*dy) > 0.5
        self.aim = aim = Vec2d(dx,dy)

        for feet in self.feets:
            feet.pre_foot_update()

        #update legs
        self.active_leg.update()

        idle = True
        for feet in self.feets:
            feet.post_foot_update()
            if feet.walking:
                idle = False

        #if no feets active, shuffle in place
        if idle and not stick_active and self.active_leg.step_state == StepState.idle:
            if self.active_leg == self.left_leg:
                self.right_leg.do_step(self.left_leg.foot_body.position, StepState.shuffle)
                self.active_leg = self.right_leg
            elif self.active_leg == self.right_leg:
                self.left_leg.do_step(self.right_leg.foot_body.position, StepState.shuffle)
                self.active_leg = self.left_leg

        #finally update the center based on where the feets are
        self.set_center_position()

        #apply friction if slow walk
        if not fast_walk:
            self.body.apply_force_at_local_point(self.friction*self.body.velocity*self.m)



