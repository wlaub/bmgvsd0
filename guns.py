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
    """
    its cool, firm grip grows warm even from your meg'r wrmth.
    there was a loss you can't recal but still rm'br.
    it's not very good, but it can still point frwrd.
    """
    valid_slots = ['front_hand']
    pickup = 'SordPickup'

    def __init__(self, app):
        super().__init__(app)
        self.last_hit = self.app.engine_time
        self.length = 9 #this is off by one because of the way it is

    def attach(self, parent, slot):
        self.parent = parent

        self.offset = self.parent.front_hand_position + Vec2d(self.length,0)
        x,y = self.offset

        self.body = pm.Body(body_type = pm.Body.KINEMATIC)
        self.body.position = parent.body.position + self.offset
        self.shape = pm.Circle(self.body, 0.5)
        self.shape.sensor=True
        self.shape.collision_type = COLLTYPE_DEFAULT

        self.lines = [
                [
                self.parent.front_hand_position+Vec2d(0,0),
                self.offset,
                ],
                [
                self.parent.front_hand_position + Vec2d(1,-1),
                self.parent.front_hand_position + Vec2d(1,1)
                ],
            ]

    def grow(self, amt):
        self.length += amt
        self.offset += Vec2d(amt, 0)

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
    pickup = 'RckngBallPickup'

    def __init__(self, app):
        super().__init__(app)
        self.last_hit = self.app.engine_time

    def attach(self, parent, slot):
        self.parent=parent

        self.link = 7
        self.N = 7

        self.m = m = 25
        self.m = m = 420
        self.r = r = 8

        if slot == 'back_hand': #TODO retrieve slot positions throug hplayer
            self.slot_position = self.parent.back_hand_position
        else:
            self.slot_position = self.parent.front_hand_position

        root_pos = parent.position + self.slot_position
        pos = self.slot_position + Vec2d(0,+self.link*self.N)

        self.joints = []
        self.jcs = []

        jm = 10

        joint_body = pm.Body(jm, math.inf)
        joint_body.position = root_pos + Vec2d(0, +self.link)
        c = pymunk.SlideJoint(self.parent.body, joint_body, self.slot_position, (0,0), 0, self.link)
        c.collide_bodies = False
        self.app.space.add(joint_body)
        self.app.space.add(c)
        last_joint = joint_body
        self.joints.append(joint_body)
        self.jcs.append(c)

        for idx in range(2,self.N):
            joint_body = pm.Body(jm, math.inf)
            joint_body.position = root_pos + Vec2d(0, +self.link*idx)
            c = pymunk.SlideJoint(last_joint, joint_body, (0,0), (0,0), 0, self.link)
            c.collide_bodies = False
            self.app.space.add(joint_body)
            self.app.space.add(c)
            last_joint = joint_body
            self.joints.append(joint_body)
            self.jcs.append(c)

        self.moment = pm.moment_for_circle(m, 0, r)
        self.body = body = pm.Body(m, self.moment)
        body.position = Vec2d(*pos)
        self.shape = pm.Circle(self.body, self.r)
        self.shape.collision_type = COLLTYPE_DEFAULT
        self.app.space.add(self.body, self.shape)

        c = pymunk.PinJoint(last_joint, self.body)
        self.app.space.add(c)
        self.jcs.append(c)

    def update(self):
        self.body.apply_force_at_local_point(Vec2d(0,self.m*240))

    def grow(self, amt):
        self.r += amt
        self.app.space.remove(self.shape)
        self.shape = pm.Circle(self.body, self.r)
        self.shape.collision_type = COLLTYPE_DEFAULT
        self.app.space.add(self.shape)

    def draw(self):
        points = [self.app.jj(self.parent.position+self.slot_position)]
        for joint in (*self.joints, self.body):
            pv = joint.position
            pv = self.app.jj(pv)
            points.append(pv)
#            pygame.draw.circle(self.app.screen, (255,0,0), pv, 1, 2)
        pygame.draw.lines(self.app.screen, (0,0,0), False, points)

#        for c in self.jcs:
#            a = self.app.jj(c.a.position+c.anchor_a)
#            b = self.app.jj(c.b.position+c.anchor_b)
#            pygame.draw.line(self.app.screen, (0,0,0), a, b, 1)

        p = self.body.position + self.shape.offset.cpvrotate(self.body.rotation_vector)
        p = self.app.jj(p)

        pygame.draw.circle(self.app.screen, (0,0,0), p, int(self.r))
        #TODO if dmg:
        pygame.draw.circle(self.app.screen, (128,128,128), p, int(self.r), 1)


    def add_to_space(self, space):
        pass
    def remove_from_space(self, space):
        space.remove(self.body, self.shape)
        for c in self.jcs:
            space.remove(c)
        for joint in self.joints:
            space.remove(joint)

@register
class EulLntrn(Equipment):
    """
    its sees and knows
    """
    valid_slots = ['back_hand', 'front_hand']
    pickup = 'EulLntrnPickup'

    def __init__(self, app):
        super().__init__(app)
        self.last_hit = self.app.engine_time

        self.scale = 2

    def attach(self, parent, slot):
        self.parent=parent


        self.link = 1

        self.m = m = 25
        self.m = m = 420
        self.r = r = 0.5
        self.ro = ro = 3

        self.friction = self.m*-10
        self.gravity = self.m*480

        if slot == 'back_hand': #TODO retrieve slot positions throug hplayer
            self.slot_position = self.parent.back_hand_position
        else:
            self.slot_position = self.parent.front_hand_position

        self.connect_offset = Vec2d(0,-ro)

        root_pos = parent.position + self.slot_position
        pos = self.slot_position + Vec2d(0,+self.link)-self.connect_offset

        self.joints = []
        self.jcs = []

        self.moment = pm.moment_for_circle(m, 0, r)
        self.body = body = pm.Body(m, self.moment)
#        body.position = Vec2d(*pos)
        body.position = Vec2d(*self.app.camera.reference_position)
        self.shape = pm.Circle(self.body, self.r)
        self.shape.collision_type = COLLTYPE_DEFAULT
#        self.shape.sensor = True
        self.app.space.add(self.body, self.shape)

        c = pymunk.DampedSpring(self.parent.body, self.body, self.slot_position, (0,0), self.link, m*100, m*10)

        self.app.space.add(c)
        self.jcs.append(c)

        self.old_scale = self.app.camera.scale
        self.app.camera.parent = self
        self.app.camera.set_scale(self.scale)

    def update(self):
        friction = self.body.velocity*self.friction
        self.body.apply_force_at_local_point(Vec2d(0,self.gravity)+friction)


    def grow(self, amt):
        self.scale -= 1
        if self.scale < 1:
            self.scale = 1

        self.app.camera.set_scale(self.scale)

    def draw(self):

        p = self.body.position + self.shape.offset.cpvrotate(self.body.rotation_vector)
        p = self.app.jj(p)

        points = [self.app.jj(self.parent.position+self.slot_position), p+self.connect_offset]
        pygame.draw.lines(self.app.screen, (0,0,0), False, points)

        pygame.draw.circle(self.app.screen, (255,255,0), p, int(1))
        pygame.draw.circle(self.app.screen, (0,0,0), p, int(self.ro), 1)

    def add_to_space(self, space):
        pass
    def remove_from_space(self, space):
        if self.app.camera.parent is self:
            self.app.camera.parent = None
            self.app.camera.set_scale(self.old_scale)

        space.remove(self.body, self.shape)
        for c in self.jcs:
            space.remove(c)
        for joint in self.joints:
            space.remove(joint)

@register
class BrewPot(Equipment):
    """
    there is still some in it
    """
    valid_slots = ['back_hand', 'front_hand']
#    pickup = 'BrewPotPickup'

    def __init__(self, app):
        super().__init__(app)
        self.last_hit = self.app.engine_time

        self.sprites = self.app.get_images('brewpot')
        self.fill = 3

    def attach(self, parent, slot):
        self.parent=parent
        self.slot = slot

        self.w = w = 15
        self.h = h = 13

        self.body = None
        self.update_mass()
        m = self.m

        self.consumed = 0
        self.consume_interval = 0.3

        self.next_consume = self.app.engine_time+self.consume_interval

        xoff = 0
        if slot == 'back_hand': #TODO retrieve slot positions throug hplayer
            self.slot_position = self.parent.back_hand_position
            xoff = -self.w/2-2
        else:
            self.slot_position = self.parent.front_hand_position
            xoff = self.w/2+2

        root_pos = parent.position + self.slot_position
        pos = root_pos + self.slot_position + Vec2d(xoff,0)

        self.joints = []
        self.jcs = []

        self.body = body = pm.Body(m, math.inf)
        body.position = self.pckp.position
        self.shape = shape = pm.Poly.create_box(self.body, (self.w, self.h))
        self.app.space.add(self.body, self.shape)

        c = pymunk.PinJoint(self.parent.body, self.body, self.slot_position, Vec2d(-xoff, 0))

        self.app.space.add(c)
        self.jcs.append(c)

    def update_mass(self):
        self.m = 1e4 + 1e7*self.fill
        self.friction = -1*self.m
        if self.body is not None:
            self.body.mass = self.m

    def on_remove(self):
        self.parent.boost_speed(amt=self.consumed*2.5, dur=self.consumed*2.5)

    def update(self):
        if self.parent is None:
            return

        if self.app.engine_time > self.next_consume:

            self.fill -= 1
            self.consumed += 1

            if self.fill == 0:
                self.next_consume = self.app.engine_time+self.consume_interval/5
            else:
                self.next_consume = self.app.engine_time+self.consume_interval


            if self.fill < 0:
                self.parent.unequip(self.slot)

            else:
                self.update_mass()

        #TODO break if feet get too far away?
        #TODO something happens if you pull it too far away

        friction = self.body.velocity*self.friction
        self.body.apply_force_at_local_point(friction)

    def grow(self, amt):
        self.fill += amt
        self.fill = min(max(self.fill, 0), 3)

    def draw(self):
        points = []
        for j in self.jcs:
            a = self.app.jj(j.a.position+j.anchor_a)
            b = self.app.jj(j.b.position+j.anchor_b)
            pygame.draw.line(self.app.screen, (0,0,0), a,b)

        p = self.app.jj(self.position)
#        color = (0,0,255)
##        if self.player_on:
##            color = (255,0,0)
#
#        vertices = []
#        for v in self.shape.get_vertices():
#            pv = self.app.jj(v.rotated(self.body.angle)+self.position)
#            vertices.append(pv)
#        pygame.draw.polygon(self.app.screen, color, vertices, 1)

        self._draw_sprite(p)

    def _draw_sprite(self, p):
        i = max(0,min(self.fill, 3))
        sprite = self.sprites[f'brewpot{i}']
        w,h = sprite.get_size()
        self.app.screen.blit(sprite, p - Vec2d(w/2, h/2))



    def add_to_space(self, space):
        pass
    def remove_from_space(self, space):
        if self.app.camera.parent is self:
            self.app.camera.parent = None
            self.app.camera.set_scale(self.old_scale)

        space.remove(self.body, self.shape)
        for c in self.jcs:
            space.remove(c)
        for joint in self.joints:
            space.remove(joint)


