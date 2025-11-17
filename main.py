import sys, os
import math
import random
import time

from collections import defaultdict

import pygame

import pymunk as pm
import pymunk.util
from pymunk import pygame_util
from pymunk import Vec2d

from objects import Controller, Entity, COLLTYPE_DEFAULT
from entities import Ball, Wall
from player import Player

os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"

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
        self.w, self.h = 400, 300
        self.screen = pygame.display.set_mode((self.w*2, self.h*2))
        self.clock = pygame.time.Clock()

        self.engine_time = 0

        self.draw_options = pygame_util.DrawOptions(self.screen)

        self.controller = Controller()

        ### Init pymunk and create space
        self.run_physics = True
        self.space = pm.Space()
#        self.space.gravity = (0.0, -900.0)

        self.entities = []
        self.tracker = defaultdict(list)

        self.player = Player(self, (self.w/2, self.h/2), 10000, 32)

        self.add_entity(self.player)

        self.last_spawn = self.engine_time
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

        r = 4+4*random.random()
        m = r*r/1.8

        self.add_entity(Ball(self, (x,y), m, r) )
        self.last_spawn = self.engine_time

    def draw(self):
        self.screen.fill((255,255,255))

#        self.space.debug_draw(self.draw_options)

        for entity in self.entities:
            entity.draw()

        hello = pygame.transform.scale(self.screen, (self.w*4, self.h*4))
        self.screen.blit(hello, (0,0))

        pygame.display.flip()

    def do_physics(self):
        N = 2
        dt = 1/(60*N)
        for _ in range(N):
            self.space.step(dt)

        self.engine_time += dt

    def do_updates(self):

        dt = self.engine_time-self.last_spawn
        if dt > 0.1 + 0.01*len(self.tracker[Ball]):
            self.spawn()


        for entity in self.entities:
            entity.update()

    def loop(self):
        tick = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.run_physics = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                tick = True

        self.do_updates()

        if self.run_physics or tick:
            self.do_physics()

        self.draw()

        self.clock.tick(60)
        pygame.display.set_caption(f"fps: {len(self.entities)}, {self.clock.get_fps():.2f}")

demo = PhysicsDemo()
demo.run()



























