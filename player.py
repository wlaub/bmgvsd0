import sys, os

import math
import random
import datetime
import time
import json

import pygame

import pymunk as pm
import pymunk.util
from pymunk import Vec2d

from objects import Controller, Entity, COLLTYPE_DEFAULT
from entities import Ball, Wall
from pickups import HealthPickup
from guns import Sord

class Leg:
    debug_draw = False

    def __init__(self, app, parent_body, pos, l, offset, m):
        self.app = app
        self.m = m

        x,y = offset

        self.x = x
        self.y = y
        self.l = l
        self.parent_body = parent_body

        self.foot_body = foot_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        foot_body.position = pos+Vec2d(x, l)
        self.foot_shape = foot_shape = pymunk.Poly.create_box(foot_body, (4,2))
        self.app.space.add(foot_body, foot_shape)

        self.anchor = Vec2d(x,0)

        self.active = False
        self.active_position = Vec2d(*self.foot_body.position)
        self.offset = Vec2d(x,y)

        self.speed = 4

    def update(self):
        if self.active:
            dt = self.app.engine_time-self.active_time
            t = dt*self.speed

            if t >= 1:
                self.active = False
                t = 1

            self.foot_body.position = self.active_position+self.active_direction*t

            if self.debug_draw:
                pygame.draw.circle(self.app.screen, (0,128,0), self.active_position, 2)
                pygame.draw.circle(self.app.screen, (128,0,128), self.active_position+self.active_direction, 2)


    def draw(self):

        p0 = self.parent_body.position+self.anchor
        p1 = self.foot_body.position

        pygame.draw.line(self.app.screen, (0,0,0), p0, p1)

        if self.debug_draw:
            if self.app.player.active_leg == self:
                if self.app.player.left_leg == self:
                    pygame.draw.circle(self.app.screen, (0,0,128), p1, 2)
                else:
                    pygame.draw.circle(self.app.screen, (128,0,0), p1, 2)

    def activate(self, dx, dy):
        self.active = True
        self.active_position = self.foot_body.position
        self.active_direction = self.l*1.5*Vec2d(dx,dy)
        self.active_time = self.app.engine_time

    def deactivate(self, other):
        #TODO turn all this nonsense into a proper state machine
        self.speed = 12
        dx = 2*(random.random()-0.5)
        rest = self.x*2.5



        dy = self.parent_body.position.y - self.app.player.center_body.position.y
        if dy > 0:
            rest = self.x*2.5*(1+dy/15)
        self.activate_target(Vec2d(rest+dx,0)+other.foot_body.position)

    def activate_target(self, pos):
        if self.active:
            print('no')
            return
        self.active = True
        self.active_position = self.foot_body.position
        self.active_direction = (pos-self.foot_body.position)
        self.active_time = self.app.engine_time




class Player(Entity):
    debug_draw = False
    def __init__(self, app, pos):
        super().__init__()
        self.health = 3
        self.grace_time = 1
        self.app = app
        self.m = m = 10000
        self.body = body = pm.Body(self.m, float("inf"))
        body.position = Vec2d(*pos)

        self.w =w= 10
        self.h =h= 17
        self.hips = 1
        self.leg = leg = 3

        self.front_hand_position = Vec2d(4,-5)
        self.back_hand_position = Vec2d(-2,-4)
        self.back_elbow_position = Vec2d(-2,-5)

        self.shape = pm.Poly(self.body, [
            (-w/2, -h+w),
            (-w/2, -h),
            (w/2, -h),
            (w/2, -h+w),
            ])
        self.shape.collision_type = COLLTYPE_DEFAULT

        self.feets = []

        self.left_leg = Leg(self.app, self.body, pos, leg, (-self.hips,0), m)
        self.right_leg = Leg(self.app, self.body, pos, leg, (self.hips,0), m)

        self.legs = [self.left_leg, self.right_leg]
        self.active_leg_idx = 0
        self.active_leg = self.legs[self.active_leg_idx]
        self.active_leg.activate(0,0)
        self.walking = False

        #body control
        self.center_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.set_center_position()
        self.app.space.add(self.center_body)

        c = pymunk.DampedSpring(self.center_body, self.body, (0,0), (0,0), 0, m*1000,1000000)
        self.app.space.add(c)

        self.angle = 0

        self.guns = []
        self.guns.append(Sord(self.app, self))

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
        for gun in self.guns:
            self.app.remove_entity(gun)
        self.app.player = None
        self.write_session_stats()

    def write_session_stats(self):
        now = datetime.datetime.now()
        filename=now.strftime('%Y%m%d_%H%M%S.json')
        stats = {
            'now': now.isoformat(),
            'title': self.app.title,
            'seed': self.app.seed,
            'health': self.health,
            'time_of_death': self.app.engine_time,
            'lore_score': self.app.lore_score,
           }
        print(f'{stats["lore_score"]} {stats["title"]} {stats["seed"]}')
        with open(os.path.join('stats/', filename) ,'w') as fp:
            json.dump(stats, fp)


    def draw(self):
        body = self.body
        poly = self.shape
        p = body.position #+ self.shape.offset.cpvrotate(self.body.rotation_vector)

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
        pygame.draw.line(self.app.screen, (0,0,0),
                p+self.back_elbow_position,
                p+self.front_hand_position,
                )
        pygame.draw.line(self.app.screen, (0,0,0),
                p+self.back_elbow_position,
                p+self.back_hand_position,
                )

        #layugs
        for leg in self.legs:
            leg.draw()


        for gun in self.guns:
            gun.draw()

    def get_hit(self, dmg):
        self._basic_hit_spell(dmg)

    def update(self):
        self.friction =-10

        #guns
        for gun in self.guns:
            gun.update()

        #damage TODO move this elsewhere?
        for ball in self.app.tracker['Ball']:
            try:
                hit = self.shape.shapes_collide(ball.shape)
                self.get_hit(1)
            except AssertionError: pass

        #controls
        speed = abs(self.body.velocity)
        controller = self.app.controller

        fast_walk = controller.get_right_trigger()
        dx, dy = controller.get_left_stick()
        stick_active = (dx*dx+dy*dy) > 0.5
        aim = Vec2d(dx,dy)

        #TODO move this leg control stuff into the proper leg controller
        if stick_active:
            #start the next stick-driven step
            if not self.active_leg.active:
                #toggle the active leg TODO: remove this? it does nothing?
                if self.walking:
                    if self.active_leg == self.left_leg:
                        self.active_leg = self.right_leg
                    else:
                        self.active_leg = self.left_leg

                #select the new active leg
                left = self.left_leg.foot_body.position
                right = self.right_leg.foot_body.position

                if left.dot(aim) < right.dot(aim):
                    self.active_leg = self.left_leg
                    other_leg = self.right_leg
                else:
                    self.active_leg = self.right_leg
                    other_leg = self.left_leg

                """
                select the position on a radius around the other foot that
                maximizes the motion of their center of mass in the direction
                of the stick
                """
                pos = self.active_leg.foot_body.position
                other_pos = other_leg.foot_body.position
                dr = abs(aim)
                dr2 = dr*dr
                x1,y1 = pos
                x0,y0 = other_pos

                if not fast_walk:
                    R = self.leg*1
                    self.active_leg.speed = 7
                else:
                    R = self.leg*7
                    self.active_leg.speed = 3

                c1 = dr2*x0
                c2 = abs(dx*R*dr)


                sgn = -1 if dy < 0 else 1

                cx1 = (c1-c2)/dr2
                cx2 = (c1+c2)/dr2
                cy1 = y0 + sgn*math.sqrt(R*R+2*x0*cx1 -x0*x0 - cx1*cx1)
                cy2 = y0 + sgn*math.sqrt(R*R+2*x0*cx2 -x0*x0 - cx2*cx2)

                if self.debug_draw:
                    pygame.draw.circle(self.app.screen, (255,0,0), other_pos, R, 1)

                p0 = Vec2d(cx1, cy1)
                p1 = Vec2d(cx2, cy2)

                #TODO there has got to be a better way to pick the branch
                #pick the one that goes the furthest in the aim direction?
                if (p0-pos).dot(aim) > (p1-pos).dot(aim):
                    self.active_leg.activate_target(p0)
                else:
                    self.active_leg.activate_target(p1)


                self.walking = True

        #update legs
        self.active_leg.update()

        #stop walking after last step
        if self.walking and not self.active_leg.active and not stick_active:
            self.walking = False

        #deactivate and shufle in place
        if not self.walking and not stick_active and not self.active_leg.active:
            if self.active_leg == self.left_leg:
                self.right_leg.deactivate(self.left_leg)
                self.active_leg = self.right_leg
            elif self.active_leg == self.right_leg:
                self.left_leg.deactivate(self.right_leg)
                self.active_leg = self.left_leg

        #finally update the center based on where the feets are
        self.set_center_position()

        #apply friction if slow walk
        if not fast_walk:
            self.body.apply_force_at_local_point(self.friction*self.body.velocity*self.m)



