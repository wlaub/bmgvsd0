import math
import random
import time

import pygame

import pymunk as pm
import pymunk.util
from pymunk import Vec2d

from registry import register, entity_registry

from objects import Controller, Entity, COLLTYPE_DEFAULT, Equipment

@register
class RbtcSord(Equipment):
    valid_slots = ['front_hand']
    pickup = 'SordPickup'

    def __init__(self, app, parent):
        super().__init__(app, parent)
        self.last_hit = self.app.engine_time

        self.offset = self.parent.front_hand_position + Vec2d(8,0)
        x,y = self.offset

        self.body = pm.Body(body_type = pm.Body.KINEMATIC)
        self.body.position = parent.body.position + self.offset
        self.shape = pm.Circle(self.body, 0.5)
        self.shape.sensor=True
        self.shape.collision_type = COLLTYPE_DEFAULT

        self.lines = [
                [
                self.parent.front_hand_position+Vec2d(1,0),
                self.offset,
                ],
                [
                self.parent.front_hand_position + Vec2d(2,-1),
                self.parent.front_hand_position + Vec2d(2,1)
                ],
            ]

    def update(self):
        controller = self.app.controller
        player = self.parent

        now = self.app.engine_time
        dt = now-self.last_hit

        self.body.position = player.body.position+self.offset
        for ball in self.app.tracker['Enemy']:
            try:
                #so what i really need is to unfuck collision detection
                #so that i can just find all the bodies that have hit this body and their entities
                ball.try_hit(self.shape)
                dmg = 1
                dv = player.velocity.x - ball.velocity.x
#                print(dv)
                if dv > 31:
                    dmg = 2

                if dv > -5:
                    ball.get_hit(dmg)
            except AssertionError: pass

    def draw(self):
        p = self.app.jj(self.parent.body.position)
        pygame.draw.line(self.app.screen, (128,128,128),
                p+self.parent.front_hand_position,
                p+self.offset
                )
        pygame.draw.line(self.app.screen, (128,128,128),
                p+self.lines[1][0],
                p+self.lines[1][1],
                )



@register
class RckngBall(Equipment):
    valid_slots = ['back_hand', 'front_hand']
    def __init__(self, app, parent):
        super().__init__(app, parent)
        self.last_hit = self.app.engine_time

        self.link = 7
        self.N = 7

        self.m = m = 25
        self.m = m = 420
        self.r = r = 8

        pos = self.parent.back_hand_position + Vec2d(0,+self.link*self.N)

        root_pos = parent.position + self.parent.back_hand_position

        self.joints = []

        jm = 10

        joint_body = pm.Body(jm, math.inf)
        joint_body.position = root_pos + Vec2d(0, +self.link)
        c = pymunk.SlideJoint(self.parent.body, joint_body, self.parent.back_hand_position, (0,0), 0, self.link)
        c.collide_bodies = False
        self.app.space.add(joint_body)
        self.app.space.add(c)
        last_joint = joint_body
        self.joints.append(joint_body)

        for idx in range(2,self.N):
            joint_body = pm.Body(jm, math.inf)
            joint_body.position = root_pos + Vec2d(0, +self.link*idx)
            c = pymunk.SlideJoint(last_joint, joint_body, (0,0), (0,0), 0, self.link)
            c.collide_bodies = False
            self.app.space.add(joint_body)
            self.app.space.add(c)
            last_joint = joint_body
            self.joints.append(joint_body)

        self.moment = pm.moment_for_circle(m, 0, r)
        self.body = body = pm.Body(m, self.moment)
        body.position = Vec2d(*pos)
        self.shape = pm.Circle(self.body, self.r)
        self.shape.collision_type = COLLTYPE_DEFAULT
        self.app.space.add(self.body, self.shape)

        c = pymunk.PinJoint(last_joint, self.body)
        self.app.space.add(c)

    def update(self):
        self.body.apply_force_at_local_point(Vec2d(0,self.m*240))



    def draw(self):
        points = [self.app.jj(self.parent.position+self.parent.back_hand_position)]
        for joint in (*self.joints, self.body):
            pv = joint.position
            pv = self.app.jj(pv)
            points.append(pv)
#            pygame.draw.circle(self.app.screen, (255,0,0), pv, 1, 2)
        pygame.draw.lines(self.app.screen, (0,0,0), False, points)

        p = self.body.position + self.shape.offset.cpvrotate(self.body.rotation_vector)
        p = self.app.jj(p)

        pygame.draw.circle(self.app.screen, (0,0,0), p, int(self.r))
        #TODO if dmg:
        pygame.draw.circle(self.app.screen, (128,128,128), p, int(self.r), 1)


    def add_to_space(self, space):
        pass
    def remove_from_space(self, space):
        #TODO
        pass
#        space.remove(self.body, self.shape)


