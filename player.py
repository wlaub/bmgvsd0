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

from registry import register, entity_registry

from objects import Controller, Entity, COLLTYPE_DEFAULT
from feets import StepState

@register
class Player(Entity):
    debug_draw = False
    def __init__(self, app, pos):
        super().__init__(app)
        self.health = 3
        self.grace_time = 1
        self.app = app
#        self.m = m = 10000
        self.m = m = 1000
        self.body = body = pm.Body(self.m, float("inf"))
        body.position = Vec2d(*pos)

        self.fast_walk = False
        self.stick_active = False
        self.aim = Vec2d(0,0)

        self.can_get_hurt = True

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
        self.left_leg = self.app.create_entity('Leg', self, pos, self.leg, (-self.hips,0))
        self.right_leg = self.app.create_entity('Leg', self, pos, self.leg, (self.hips,0))

        self.legs = [self.left_leg, self.right_leg]
        self.active_leg_idx = 0
        self.active_leg = self.legs[self.active_leg_idx]

        #feets
        self.feets = []
        self.equip('legs', 'Exoskeleton')

        #hayunds

        #body control
        self.center_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.set_center_position()
        self.app.space.add(self.center_body)

#        c = pymunk.DampedSpring(self.center_body, self.body, (0,0), (0,0), 0, m*1000,1000000)
        c = pymunk.DampedSpring(self.center_body, self.body, (0,0), (0,0), 0, m*1000,m*100)
        self.app.space.add(c)


        #TODO slot active and unactive positions

        self.slot_positions = {
            'front_hand': (self.front_unarmed_position, self.front_hand_position),
            'back_hand': (self.back_unarmed_position, self.back_hand_position),
            }

        self.slot_sensors = {}

        for slot in self.base_slots:
            if slot in self.slot_positions:
                body = pm.Body(body_type = pm.Body.KINEMATIC)
                body.position = self.get_slot_position(slot)
                shape = pm.Circle(body, 0.5)
                shape.sensor=True
                shape.collision_type = COLLTYPE_DEFAULT
            else:
                body = self.body
                shape = self.shape
            self.slot_sensors[slot] = {body:(shape,)}

    def get_slot_hit(self, other_shape, slots):
        for slot in slots:
            bmap = self.slot_sensors[slot]
            for body, shapes in bmap.items():
                for shape in shapes:
                    try:
                        hit = other_shape.shapes_collide(shape)
                        return slot
                    except AssertionError: pass
        return None


    def get_slot_position(self, slot):
        if slot in self.slot_positions.keys():
            inactive, active = self.slot_positions[slot]
            if self.slots[slot] is not None:
                return self.position + active
            else:
                return self.position + inactive

    def update_slot_positions(self):
        for slot, bmap in self.slot_sensors.items():
            position = self.get_slot_position(slot)
            for body, shapes in bmap.items():
                if body is not self.body:
                    body.position = position

    def create_slot(self, slot):
        if not slot in self.slots.keys():
            self.slots[slot] = None

    def equip(self, slot, name):
        entity = self.app.create_entity(name, self)
        return self.equip_entity(slot, entity)

    def drop_equipment(self, slot):
        old = self.slots[slot]
        if old is not None:
            pickup_name = f'{old.ename}Pickup'
            if pickup_name in entity_registry.by_name.keys():
                #TODO use the slot position here
                self.app.spawn_entity(pickup_name, self.position)
            self.unequip(slot)

    def equip_entity(self, slot, entity):
        if not slot in entity.valid_slots:
            print(f"can't put {entity.ename} in {slot}")
            return False

        if self.slots[slot] is None or self.slots[slot].ename != entity.ename:
            self.drop_equipment(slot)
            self.slots[slot] = entity
            self.app.add_entity(entity)
            if entity.is_feets:
                self.feets.append(entity)
            return True
        return False

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

        for slot, bmap in self.slot_sensors.items():
            position = self.get_slot_position(slot)
            for body, shapes in bmap.items():
                if body is not self.body:
                    space.add(body, *shapes)

    def on_remove(self):
        for slot, entity in self.slots.items():
            self.unequip(slot)

        for slot, bmap in self.slot_sensors.items():
            position = self.get_slot_position(slot)
            for body, shapes in bmap.items():
                if body is not self.body:
                    self.app.space.remove(body, *shapes)

        self.app.player = None
        self.write_session_stats()

        if self.app.flags.getv('_loop', False):
            engine_time = self.app.engine_time
            def _loop():
                while len(self.app.entities) > 0:
                    dt = self.app.engine_time-engine_time
                    self.app.forget_range = 0.1-dt/5
                    yield
                self.app.queue_reset = True
                return

            self.app.coroutines.add(_loop())


    def write_session_stats(self):
        now = datetime.datetime.now()
        filename=now.strftime('%Y%m%d_%H%M%S.json')
        startup_time =self.app.flags.getv('_startup_time')
        stats = {
            'now': now.isoformat(),
            'then': startup_time.isoformat(),
            'title': self.app.title,
            'seed': self.app.seed,
            'health': self.health,
            'time_of_death': self.app.engine_time-self.app.flags.getv('_startup_engine_time'),
            'fleshworld_duration': str(self.app.get_fleshtime(now)),
            'lore_score': self.app.lore_score,
            'beans': self.app.beans,
            'field': self.app.field.current_props,
           }
        print(f'{stats["lore_score"]} {stats["title"]} {stats["seed"]}')
        print(json.dumps(stats, indent=2))

        stats['counts'] = counts = {}
        for k,v in self.app.tracker.items():
            counts[k] = len(v)

        #TODO fixme
        stats['vflags'] = {k:v for k,v in self.app.flags.volatile_flags.items() if not isinstance(v, datetime.datetime)}
        stats['nvflags'] = self.app.flags.flags
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
        if self.health >= 0:
            pygame.draw.rect(self.app.screen, (128,128,128),
                pygame.Rect(p+Vec2d(-self.w/2, -self.h), (5, self.health))
                )
        else:
            pygame.draw.rect(self.app.screen, (128,128,128),
                pygame.Rect(p+Vec2d(-self.w/2, -self.h+self.health), (5, -self.health))
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

#        body = self.center_body
#        p = body.position #+ self.shape.offset.cpvrotate(self.body.rotation_vector)
#
#        p = self.app.jj(p)
#        pygame.draw.circle(self.app.screen, (255,0,255), p, 1, 2)


#        #slots
#        for slot, bmap in self.slot_sensors.items():
#            position = self.get_slot_position(slot)
#            for body, shapes in bmap.items():
#                if body is not self.body:
#                    p = body.position #+ self.shape.offset.cpvrotate(self.body.rotation_vector)
#                    p = self.app.jj(p)
#                    pygame.draw.circle(self.app.screen, (255,0,255), p, 1, 2)


    def get_hit(self, dmg):
        self._advanced_hit_spell(dmg)

    def update(self):
        self.friction =-10

        self.update_slot_positions()

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



