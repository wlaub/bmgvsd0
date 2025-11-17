import math
import random
import time

import pygame

import pymunk as pm
import pymunk.util
from pymunk import Vec2d

from objects import Controller, Entity, COLLTYPE_DEFAULT
from entities import Ball, Wall
from pickups import HealthPickup

class Leg:
    def __init__(self, app, parent_body, pos, l, offset, m, r):
        self.app = app
        self.m = m
        self.r = r

        l*=r
        x,y = offset
        x*=r
        y*=r

        self.x = x
        self.y = y
        self.l = l
        self.parent_body = parent_body

#        self.foot_body = foot_body = pymunk.Body(self.m, float("inf"))
        self.foot_body = foot_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        foot_body.position = pos+Vec2d(x, l)
        self.foot_shape = foot_shape = pymunk.Poly.create_box(foot_body, (4*r,2*r))
        self.app.space.add(foot_body, foot_shape)

        self.knee_body = knee_body = pymunk.Body(1, math.inf)
        knee_body.position = pos+Vec2d(x,l/2)
        self.app.space.add(knee_body)

        self.thigh = c = pymunk.SlideJoint(self.parent_body, self.knee_body, (x,0), (0,0), l/2,l/2+1)
#        self.c = pymunk.SlideJoint(self.parent_body, self.foot_body, (x,0), (0,0), 0,l*2+1)
        self.app.space.add(c)
        self.c =c= pymunk.SlideJoint(self.foot_body, self.knee_body, (0,0), (0,0), l/2,l/2+1)
        self.app.space.add(c)
#        c = pymunk.DampedSpring(self.parent_body, self.foot_body, (x,0), (0,0), l, m*10000,100)
        c = pymunk.DampedSpring(self.parent_body, self.foot_body,
                                (0,-l), (0,0),
                                (l*l*4+x*x)**0.5,
                                m*10000,10000)
#        self.app.space.add(c)

        self.active = False
        self.active_position = Vec2d(*self.foot_body.position)
        self.offset = Vec2d(x,y)

        self.speed = 4

    def update(self):
        if self.active:
            dt = self.app.engine_time-self.active_time
            t = dt*self.speed

#            print(t, self.app.player.left_leg == self)
            if t >= 1:
                self.active = False
                t = 1

            self.foot_body.position = self.active_position+self.active_direction*t

#            pygame.draw.circle(self.app.screen, (0,128,0), self.active_position, 2)
#            pygame.draw.circle(self.app.screen, (128,0,128), self.active_position+self.active_direction, 2)


    def draw(self):

        p0 = self.parent_body.position+self.thigh.anchor_a
        p1 = self.foot_body.position

        pygame.draw.line(self.app.screen, (0,0,0), p0, p1)


#        if self.app.player.active_leg == self:
#            if self.app.player.left_leg == self:
#                pygame.draw.circle(self.app.screen, (0,0,128), p1, 2)
#            else:
#                pygame.draw.circle(self.app.screen, (128,0,0), p1, 2)

    def activate(self, dx, dy):
        self.active = True
        self.active_position = self.foot_body.position
        self.active_direction = self.l*1.5*Vec2d(dx,dy)
        self.active_time = self.app.engine_time

    def deactivate(self, other):
        self.speed = 7
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
    def __init__(self, app, pos, m, r):
        super().__init__()
        self.health = 3
        self.grace_time = 1
        r = 1
        self.app = app
        self.m = m
        self.r = r
        self.body = body = pm.Body(self.m, float("inf"))
        body.position = Vec2d(*pos)

        self.w =w= 10*r
        self.h =h= 17*r
        self.hips = r

        self.shape = pm.Poly(self.body, [
            (-w/2, -h+w),
            (-w/2, -h),
            (w/2, -h),
            (w/2, -h+w),
            ])

        self.sensor_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.sensor_body.position = self.body.position
        self.sensor_shape = pm.Poly(self.sensor_body, [
            (-w/2-1, -h+w+1),
            (-w/2-1, -h-1),
            (w/2+1, -h-1),
            (w/2+1, -h+w+1),
            ])
        self.sensor_shape.sensor=True
        self.sensor_shape.collision_type = COLLTYPE_DEFAULT
        self.app.space.add(self.sensor_body, self.sensor_shape)


#        self.shape = shape = pm.Poly.create_box(body, (10*r,20*r))
#        self.shape.mass = m
        self.shape.collision_type = COLLTYPE_DEFAULT

        self.feets = []

        self.leg = leg = 3*r

        self.left_leg = Leg(self.app, self.body, pos, leg, (-self.hips,0), m, 1)
        self.right_leg = Leg(self.app, self.body, pos, leg, (self.hips,0), m, 1)

        self.center_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.set_center_position()
        self.app.space.add(self.center_body)

        c = pymunk.DampedSpring(self.center_body, self.body, (0,0), (0,0), 0, m*1000,1000000)
        self.app.space.add(c)



        self.legs = [self.left_leg, self.right_leg]
        self.active_leg_idx = 0
        self.active_leg = self.legs[self.active_leg_idx]
        self.active_leg.activate(0,0)
        self.walking = False

        self.angle = 0

        self.guns = []
        self.guns.append(Sord(self.app, self, Vec2d(self.r*12,-5*self.r), self.r ))
#        self.guns.append(FaceGun(self.app, r))

    def set_center_position(self):
        left = self.left_leg.foot_body.position
        right = self.right_leg.foot_body.position

        dist = max(0,abs(left-right)-self.w)
        alpha = 1-min(1,dist/(self.leg*2))

        t = 5
        self.center_body.position = Vec2d(
#                ((left.x+right.x)/2+self.body.position.x)/2,
#                min(self.body.position.y-self.h/2, left.y-t, right.y-t)
                (left.x+right.x)/2, (left.y+right.y)/2-self.leg*alpha
                )

    def add_to_space(self, space):
        space.add(self.body, self.shape)
        for gun in self.guns:
            gun.add_to_space(space)

    def draw(self):


        body = self.body
        poly = self.shape
        v = body.position #+ self.shape.offset.cpvrotate(self.body.rotation_vector)
#            p = self.app.flipyv(v)
        p = v

#        ps = [p.rotated(body.angle) + body.position for p in poly.get_vertices()]
#        ps.append(ps[0])
#            ps = list(map(self.app.flipyv, ps))
#        color = (240,192,160)
#        pygame.draw.polygon(self.app.screen, color, ps)
#        pygame.draw.lines(self.app.screen, (0,0,0), False, ps)

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
            pygame.Rect(p+Vec2d(-self.w/2, -self.h), (self.r*5, self.r*self.health))
            )
        #eye
        pygame.draw.rect(self.app.screen, (0,0,128),
            pygame.Rect(p+Vec2d(self.r*4, -self.h+self.r*2), (self.r*2, self.r*2))
            )




        #body
        pygame.draw.line(self.app.screen, (0,0,0), p, p+Vec2d(0,-self.r*6))
        pygame.draw.line(self.app.screen, (0,0,0), p-Vec2d(-self.r,0), p-Vec2d(self.r,0))

        #arms
        pygame.draw.line(self.app.screen, (0,0,0),
                p+Vec2d(-self.r*2,-5*self.r),
                p+Vec2d(self.r*4,-5*self.r)
                )
        pygame.draw.line(self.app.screen, (0,0,0),
                p+Vec2d(-self.r*2,-5*self.r),
                p+Vec2d(-self.r*2,-5*self.r+1),
                )

        #sord
        pygame.draw.line(self.app.screen, (128,128,128),
                p+Vec2d(self.r*4,-5*self.r),
                p+Vec2d(self.r*12,-5*self.r)
                )
        pygame.draw.line(self.app.screen, (128,128,128),
                p+Vec2d(self.r*5,-6*self.r),
                p+Vec2d(self.r*5,-4*self.r),
                )


        #layugs
        for leg in self.legs:
            leg.draw()


        for gun in self.guns:
            gun.draw()

    def get_hit(self, dmg):
        self._basic_hit_spell(dmg)

    def update(self):
        self.friction = 0

        speed = abs(self.body.velocity)
        if speed > 0:
            new_angle = math.atan2(self.body.velocity.y, self.body.velocity.x)
            self.angle = new_angle

        self.friction -=10

        for gun in self.guns:
            gun.update()

        for ball in self.app.tracker[Ball]:
            try:
                hit = self.shape.shapes_collide(ball.shape)
                self.get_hit(1)
            except: AssertionError

#        for entity in self.app.tracker[HealthPickup]:
#            try:
#                hit = self.shape.shapes_collide(entity.shape)
#                if self.health < 3:
#                    self.health += 1
#                self.app.remove_entity(entity)
#            except: AssertionError



        controller = self.app.controller
        dx, dy = controller.get_left_stick()

        if controller.get_right_trigger():
            base_force = 6000
        else:
            base_force = 1500

        fast_walk = controller.get_button('x')

        v = Vec2d(dx, dy)*base_force*self.m
#        self.left_leg.foot_body.apply_force_at_local_point(v)



        stick_active = (dx*dx+dy*dy) > 0.5
        if stick_active:
#            self.active_leg.foot_body.position += Vec2d(dx,dy)*10
            if not self.active_leg.active:
                if self.walking:
                    if self.active_leg == self.left_leg:
                        self.active_leg = self.right_leg
                    else:
                        self.active_leg = self.left_leg

                left = self.left_leg.foot_body.position
                right = self.right_leg.foot_body.position

                aim = Vec2d(dx,dy)

                if left.dot(aim) < right.dot(aim):
                    self.active_leg = self.left_leg
                    other_leg = self.right_leg
                else:
                    self.active_leg = self.right_leg
                    other_leg = self.left_leg

                pos = self.active_leg.foot_body.position
                other_pos = other_leg.foot_body.position
                x1, y1 = pos - other_pos
                x2 = x1+dx
                y2 = y1+dy
                dr = abs(aim)
                dr2 = dr*dr
                D = x1*y2-x2*y1
                r = 2*self.leg
                dis = r*r*dr2-D*D
                if True:
                    """
                    select the position on a radius around the other foot that
                    maximizes the motion of their center of mass in the direction
                    of the stick
                    """
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

#                    pygame.draw.circle(self.app.screen, (255,0,0), other_pos, R, 1)

                    p0 = Vec2d(cx1, cy1)
                    p1 = Vec2d(cx2, cy2)


                    if (p0-pos).dot(aim) > (p1-pos).dot(aim):
                        self.active_leg.activate_target(p0)
                    else:
                        self.active_leg.activate_target(p1)

                else:
                    sgn = -1 if dy < 0 else 1
                    c1 = D*dy
                    c2 = sgn*dx*(dis)**0.5
                    c3 = -D*dx
                    c4 = abs(dy)*(dis)**0.5

                    cx1 = (c1+c2)/(dr2)
                    cy1 = (c3+c4)/(dr2)
                    cx2 = (c1-c2)/(dr2)
                    cy2 = (c3-c4)/(dr2)

                    p0 = Vec2d(cx1, cy1)+other_pos
                    p1 = Vec2d(cx2, cy2)+other_pos

                    if (p0-pos).dot(aim) > (p1-pos).dot(aim):
                        self.active_leg.activate_target(p0)
                    else:
                        self.active_leg.activate_target(p1)



                self.walking = True

        self.active_leg.update()

        if self.walking and not self.active_leg.active and not stick_active:
            self.walking = False

        if not self.walking and not stick_active and not self.active_leg.active:
            if self.active_leg == self.left_leg:
                self.right_leg.deactivate(self.left_leg)
                self.active_leg = self.right_leg
            elif self.active_leg == self.right_leg:
                self.left_leg.deactivate(self.right_leg)
                self.active_leg = self.left_leg


        self.set_center_position()

        if not fast_walk:
            self.body.apply_force_at_local_point(self.friction*self.body.velocity*self.m)

#        self.mouse_body.position += Vec2d(dx,dy)


class Sord(Entity):
    def __init__(self, app, parent, offset, r):
        self.app = app
        self.parent = parent
        self.last_hit = self.app.engine_time

        self.offset = offset*r
        x,y = self.offset

        self.body = pm.Body(body_type = pm.Body.KINEMATIC)
        self.body.position = parent.body.position + self.offset
        self.shape = pm.Circle(self.body, r/2)
        self.shape.sensor=True
        self.shape.collision_type = COLLTYPE_DEFAULT

    def update(self):
        controller = self.app.controller
        player = self.parent

        now = self.app.engine_time
        dt = now-self.last_hit

        self.body.position = player.body.position+self.offset
        for ball in self.app.tracker[Ball]:
            try:
                hit = self.shape.shapes_collide(ball.shape)
                dmg = 1
                dv = player.body.velocity.x - ball.body.velocity.x
#                print(dv)
                if dv > 31:
                    dmg = 2

                if dv > -5:
                    ball.get_hit(dmg)
#                    self.app.remove_entity(ball)
            except AssertionError: pass





class FaceGun:
    def __init__(self, app, r):
        self.app = app
        self.last_hit = self.app.engine_time

        self.body = pm.Body(body_type = pm.Body.KINEMATIC)
        self.shape = pm.Poly(self.body, [
            (-r/2, r),
            (-r/2, r+r),
            (r/2, r+r),
            (r/2, r),
            ])
        self.shape.sensor=True
        self.shape.collision_type = COLLTYPE_DEFAULT

        self.hit_angle = 0

    def add_to_space(self, space):
        space.add(self.body, self.shape)

    def draw(self):
        if self.fire :
            body = self.body
            poly = self.shape
            ps = [p.rotated(body.angle) + body.position for p in poly.get_vertices()]
            ps.append(ps[0])
#            ps = list(map(self.app.flipyv, ps))
            color = (0,128,0)
            pygame.draw.lines(self.app.screen, color, False, ps)
            pygame.draw.polygon(self.app.screen, color, ps)

    def update(self):
        controller = self.app.controller
        player = self.app.player

        now = self.app.engine_time

        dt = now-self.last_hit
        if now-self.last_hit > 2 and not controller.get_right_trigger():
            self.last_hit = now
            dt = 0
            self.hit_angle = player.angle

        self.fire = False
        self.body.position = player.body.position
        if dt < 1:
            t = math.sin(dt*math.pi)

            player.friction -= 25

            self.fire = True
            self.body.angle = self.hit_angle-t*3.14

            for ball in self.app.tracker[Ball]:
                try:
                    hit = self.shape.shapes_collide(ball.shape)
                    self.app.remove_entity(ball)
                except: pass
        else:
            self.body.angle = player.angle



