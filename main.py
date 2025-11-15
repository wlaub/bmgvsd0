import sys, os
import math
import random
import time

from collections import defaultdict

import pygame

import pymunk as pm
import pymunk.util
from pymunk import Vec2d

os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"

COLLTYPE_DEFAULT = 0
COLL_TYPE_MOUSE = 1

class Controller:
    button_map = {
    'a': 0,
    'b': 1,
    'x': 2,
    'y': 3,
    'rb': 5,
    'lb': 4,
    'select': 6,
    'start': 7,
    'xbox': 8,
    'l3': 9,
    'r3': 10,
    }

    axis_map = {
    'lx': 0,
    'ly': 1,
    'lt': 2,
    'rx': 3,
    'ry': 4,
    'rt': 5,
    }

    def __init__(self):

        self.joystick = pygame.joystick.Joystick(0)

    def get_left_stick(self):
        xpos = self.joystick.get_axis(self.axis_map['lx'])
        ypos = self.joystick.get_axis(self.axis_map['ly'])
        return (xpos, ypos)

    def get_right_trigger(self):
        return self.joystick.get_axis(self.axis_map['rt']) > 0.5

class Entity:
    def draw(self):
        pass
    def update(self):
        pass
    def add_to_space(self, space):
        space.add(self.body, self.shape)
    def remove_from_space(self, space):
        space.remove(self.body, self.shape)

class Ball(Entity):
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

    def draw(self):
        v = self.body.position + self.shape.offset.cpvrotate(self.body.rotation_vector)
        p = self.app.flipyv(v)

        pygame.draw.circle(self.app.screen, pygame.Color("blue"), p, int(self.r), 2)

    def update(self):

        player = self.app.player

        delta = player.body.position-self.body.position
        delta /=abs(delta)
#        self.body.velocity = delta*70
        self.body.apply_force_at_local_point(delta*1000*self.m)

        friction = self.body.velocity*-10*self.m
        self.body.apply_force_at_local_point(friction)

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



class Wall(Entity):
    def __init__(self, app, start, end):
        self.app = app
        self.start = start
        self.end = end

        self.body = pm.Body(body_type=pm.Body.STATIC)
        self.shape = pm.Segment(self.body, Vec2d(*start), Vec2d(*end), 0)
        self.shape.friction = 1
        self.shape.collision_type = COLLTYPE_DEFAULT

    def draw(self):
        pv1 = self.app.flipyv(self.body.position + self.shape.a.cpvrotate(self.body.rotation_vector))
        pv2 = self.app.flipyv(self.body.position + self.shape.b.cpvrotate(self.body.rotation_vector))
        pygame.draw.lines(self.app.screen, (0,0,0), False, [pv1, pv2])

    def update(self):
        pass

class PhysicsDemo:
    def flipyv(self, v):
        return int(v.x), int(-v.y + self.h)

    def run(self):
        while self.running:
            self.loop()

    def add_entity(self, e):
#        self.space.add(e.body, e.shape)
        e.add_to_space(self.space)
        self.entities.append(e)
        self.tracker[e.__class__].append(e)

    def remove_entity(self, e):
        e.remove_from_space(self.space)
        self.entities.remove(e)
        self.tracker[e.__class__].remove(e)


    def __init__(self):

        pygame.init()
        self.w, self.h = 800, 600
        self.screen = pygame.display.set_mode((self.w, self.h))
        self.clock = pygame.time.Clock()

        self.controller = Controller()

        ### Init pymunk and create space
        self.space = pm.Space()
#        self.space.gravity = (0.0, -900.0)

        self.entities = []
        self.tracker = defaultdict(list)

        self.player = Player(self, (self.w/2, self.h/2), 10000, 32)

        self.add_entity(self.player)

        self.last_spawn = time.time()
        for i in range(1):
            self.spawn()


#        self.add_entity(Wall(self, (0, 0), (self.w, 0)))
#        self.add_entity(Wall(self, (self.w, 0), (self.w, self.h)))
#        self.add_entity(Wall(self, (0, self.h), (self.w, self.h)))
#        self.add_entity(Wall(self, (0, self.h), (0, 0)))

        self.running = True

    def spawn(self):
        t = random.random()
        margin = 50
        if t < 0.25:
            x = -margin
            y = t*4*(self.h+2*margin)-margin
        elif t < 0.5:
            x = self.w+margin
            y = (t-0.25)*4*(self.h+2*margin)-margin
        elif t < 0.75:
            y = -margin
            x = (t-0.5)*4*(self.w+2*margin)-margin
        else:
            y = self.h+margin
            x = (t-0.75)*4*(self.w+2*margin)-margin

        r = 8+8*random.random()
        m = r*r/1.8

        self.add_entity(Ball(self, (x,y), m, r) )
        self.last_spawn = time.time()

    def draw(self):
        self.screen.fill((255,255,255))

        for entity in self.entities:
            entity.draw()

        pygame.display.flip()

    def do_physics(self):
        N = 2
        dt = 1/(60*N)
        for _ in range(N):
            self.space.step(dt)

    def do_updates(self):

        dt = time.time()-self.last_spawn
#        if dt > 0.1 + 0.01*len(self.tracker[Ball]):
        self.spawn()


        for entity in self.entities:
            entity.update()

    def loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

        self.do_updates()

        self.do_physics()

        self.draw()

        self.clock.tick(60)
        pygame.display.set_caption(f"fps: {len(self.entities)}, {self.clock.get_fps():.2f}")

demo = PhysicsDemo()
demo.run()



























