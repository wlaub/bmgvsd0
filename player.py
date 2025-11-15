import math
import random
import time

import pygame

import pymunk as pm
import pymunk.util
from pymunk import Vec2d

from objects import Controller, Entity, COLLTYPE_DEFAULT
from entities import Ball, Wall

class Player(Entity):
    def __init__(self, app, pos, m, r):
        self.app = app
        self.m = m
        self.r = r
        self.moment = pm.moment_for_circle(m, 0, r)
        self.body = body = pm.Body(m, self.moment)
        body.position = Vec2d(*pos)

        self.shape = shape = pm.Circle(body, r)
#        shape.friction = 1.5
        shape.collision_type = COLLTYPE_DEFAULT

        self.last_hit = time.time()

        self.gun_body = pm.Body(body_type = pm.Body.KINEMATIC)
        self.gun = pm.Poly(self.gun_body, [
            (-r/2, r),
            (-r/2, r+r),
            (r/2, r+r),
            (r/2, r),
            ])
#        self.app.space.add(self.gun)
        self.gun.sensor=True
        self.gun.collision_type = COLLTYPE_DEFAULT

        self.angle = 0
        self.hit_angle = 0

    def add_to_space(self, space):
        space.add(self.body, self.shape)
        space.add(self.gun_body, self.gun)

    def draw(self):
        v = self.body.position + self.shape.offset.cpvrotate(self.body.rotation_vector)
        p = self.app.flipyv(v)

        pygame.draw.circle(self.app.screen, pygame.Color("green"), p, int(self.r), 2)

        end = self.body.position + Vec2d(self.r*math.cos(self.angle), self.r*math.sin(self.angle))
        pygame.draw.line(self.app.screen, (0,255,0), p, self.app.flipyv(end), 1)

        if self.fire :
            body = self.gun_body
            poly = self.gun
            ps = [p.rotated(body.angle) + body.position for p in poly.get_vertices()]
            ps.append(ps[0])
            ps = list(map(self.app.flipyv, ps))
            color = (0,128,0)
            pygame.draw.lines(self.app.screen, color, False, ps)
            pygame.draw.polygon(self.app.screen, color, ps)


    def update(self):
        controller = self.app.controller
        dx, dy = controller.get_left_stick()

        if controller.get_right_trigger():
            base_force = 6000*self.m
        else:
            base_force = 1500*self.m

        v = Vec2d(dx, -dy)*base_force
        self.body.apply_force_at_local_point(v)
        friction = self.body.velocity*-10*self.m
        self.body.apply_force_at_local_point(friction)

        speed = abs(self.body.velocity)
        if speed > 0:
#            alpha = 0.9
#            if self.fire:
#                alpha= 0.99
            new_angle = math.atan2(self.body.velocity.y, self.body.velocity.x)
#            self.angle = (1-alpha)*new_angle + alpha*self.angle
            self.angle = new_angle

        if time.time()-self.last_hit > 2 and not controller.get_right_trigger():
            self.last_hit = time.time()
#            self.hit_angle = math.atan2(self.body.velocity.y, self.body.velocity.x)
            self.hit_angle = self.angle

        self.fire = False
        dt = time.time()-self.last_hit
        if dt < 1:
            t = math.sin(dt*math.pi)
            friction = self.body.velocity*-25*self.m
            self.body.apply_force_at_local_point(friction)


            self.fire = True
            self.gun_body.position = self.body.position
            self.gun_body.angle = self.hit_angle-t*3.14

            for ball in self.app.tracker[Ball]:
                try:
                    hit = self.gun.shapes_collide(ball.shape)
                    self.app.remove_entity(ball)
                except: pass
        else:
            self.gun_body.position = self.body.position
            self.gun_body.angle = self.angle


