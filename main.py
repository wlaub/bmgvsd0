import sys, os
import math
import random
import time
import datetime

from collections import defaultdict

import pygame

import pymunk as pm
import pymunk.util
from pymunk import pygame_util
from pymunk import Vec2d

from objects import Controller, Entity, COLLTYPE_DEFAULT, Camera
from entities import Ball, Wall, ForgetfulBall
from player import Player

os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"

SEED = random.randrange(1000000,4207852)
random.seed(SEED)

print(SEED)
if len(sys.argv) > 1:
    TITLE = ' '.join(sys.argv[1:])
    print(TITLE)

class PhysicsDemo:

    def jj(self, pos):
        return pos - self.camera.position
        return pos

    def run(self):
        while self.running:
            try:
                self.loop()
            except Exception as e:
                print(e)
                raise


    def add_entity(self, e):
#        self.space.add(e.body, e.shape)
        e.add_to_space(self.space)
        self.entities.append(e)
        self.tracker[e.__class__.__name__].append(e)
        for name in e.track_as:
            self.tracker[name].append(e)
        e.on_add()

    def remove_entity(self, e):
        e.remove_from_space(self.space)
        self.entities.remove(e)
        self.tracker[e.__class__.__name__].remove(e)
        for name in e.track_as:
            self.tracker[name].remove(e)
        e.on_remove()

    def connect_camera(self, entity):
        self.camera.parent = entity

    def disconnect_camera(self):
        self.camera.parent = None

    def __init__(self):
        self.seed = SEED
        self.title = TITLE

        pygame.init()
        self.scale = 4
        self.w, self.h = 1280/self.scale, 720/self.scale
        self.ws = self.w*self.scale
        self.hs = self.h*self.scale

        self.main_screen = pygame.display.set_mode((self.ws, self.hs))
        pygame.display.set_caption(f"BLDNG MAN: GAIDN VSD0")
        self.clock = pygame.time.Clock()
        self.startup_time = datetime.datetime.now()

        pygame.mouse.set_visible(False)

        self.screen = pygame.Surface((self.w, self.h))

        self.font = pygame.font.Font(None, 14)

        self.engine_time = 0

        self.draw_options = pygame_util.DrawOptions(self.screen)

        self.camera = Camera(self, None, (-self.w/2,-self.h/2))

        self.controller = Controller(self)

        ### Init pymunk and create space
        self.run_physics = True
        self.render_physics = False
        self.space = pm.Space()
#        self.space.gravity = (0.0, -900.0)

        self.entities = []
        self.tracker = defaultdict(list)

        self.player = Player(self, (0,0))

#        self.connect_camera(self.player)

        self.add_entity(self.player)

        self.last_spawn = self.engine_time
        for i in range(1):
            self.spawn()

        self.lore_score = 0
        self.beans = 0
        self.field_richness = 0.75

#        self.add_entity(Wall(self, (0, 0), (self.w, 0)))
#        self.add_entity(Wall(self, (self.w, 0), (self.w, self.h)))
#        self.add_entity(Wall(self, (0, self.h), (self.w, self.h)))
#        self.add_entity(Wall(self, (0, self.h), (0, 0)))

        self.running = True

    def spawn(self):
        t = random.random()
        margin = 50
        l,r,u,d = self.camera.lrud
        if t < 0.25:
            x = l-margin
            y = t*4*(d-u)+u
        elif t < 0.5:
            x = r+margin
            y = (t-0.25)*4*(u-d)+d
        elif t < 0.75:
            y = u-margin
            x = (t-0.5)*4*(r-l)+l
        else:
            y = d+margin
            x = (t-0.75)*4*(l-r)+r

        pos = Vec2d(x,y)
        if random.random() < 0.1:
            new_entity = ForgetfulBall(self, pos)
        else:
            new_entity = Ball(self, pos)

        self.add_entity(new_entity)
        self.last_spawn = self.engine_time

    def draw(self):

        if self.render_physics:
            self.space.debug_draw(self.draw_options)

        for entity in self.entities:
            entity.draw()

        header = self.font.render(f'{self.lore_score}', False, (0,0,128))
        self.screen.blit(header, (2,2))


        ypos = self.h-2
        text = self.font.render(f'{TITLE}', False, (128,128,0))
        ypos -= text.get_height()
        self.screen.blit(text, (2,ypos))

        text = self.font.render(f'{SEED}', False, (128,128,0))
        ypos -= text.get_height()
        self.screen.blit(text, (2,ypos))



        hello = pygame.transform.scale(self.screen, (self.ws, self.hs))
        self.main_screen.blit(hello, (0,0))

        pygame.display.flip()
        self.screen.fill((255,255,255))

    def do_physics(self):
        N = 1
        dt = 1/(120*N)
        for _ in range(N):
            self.space.step(dt)

        self.engine_time += dt*N

    def do_updates(self):
        self.camera.update()

        dt = self.engine_time-self.last_spawn
        if dt > 0.2 + 0.02*len(self.tracker['Ball']):
            self.spawn()


        for entity in self.entities:
            entity.update()

    def loop(self):
        tick = False
        self.keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.run_physics = not self.run_physics
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                tick = True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                self.render_physics = not self.render_physics


        if self.run_physics or tick:
            self.do_updates()

            self.do_physics()

            self.draw()

        self.clock.tick(60)
#        pygame.display.set_caption(f"fps: {len(self.tracker['Ball'])}, {self.clock.get_fps():.2f}")

demo = PhysicsDemo()
demo.run()



























