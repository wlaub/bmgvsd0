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

from registry import register, entity_registry

from objects import Controller, Entity, COLLTYPE_DEFAULT, Camera

from debug import DebugConsole

import player
import entities
import pickups
import guns
import feets

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
        e.add_to_space(self.space)
        self.entities.append(e)
        class_name = e.__class__.__name__
        for tag in entity_registry.name_tags[class_name]:
            self.tracker[tag].append(e)
        e.on_add()

    def remove_entity(self, e):
        e.remove_from_space(self.space)
        self.entities.remove(e)
        class_name = e.__class__.__name__
        for tag in entity_registry.name_tags[class_name]:
            self.tracker[tag].remove(e)
        e.on_remove()

    def connect_camera(self, entity):
        self.camera.parent = entity

    def disconnect_camera(self):
        self.camera.parent = None

    def __init__(self):
        self.seed = SEED
        self.title = TITLE

        pygame.init()

        self.ws = 1280
        self.hs = 720

        self.main_screen = pygame.display.set_mode((self.ws, self.hs))
        pygame.display.set_caption(f"BLDNG MAN: GAIDN VSD0")
        self.clock = pygame.time.Clock()
        self.startup_time = datetime.datetime.now()

        pygame.mouse.set_visible(False)

        self.font = pygame.font.Font(None, 14)

        self.engine_time = 0

        self.debug_console = DebugConsole(self)

        self.camera = Camera(self, None, (0,0), 4)

        self.controller = Controller(self)

        ### Init pymunk and create space
        self.run_physics = True
        self.render_physics = False
        self.space = pm.Space()
#        self.space.gravity = (0.0, -900.0)

        self.eidhwm = 0
        self.entities = []
        self.tracker = defaultdict(list)

        self.player = self.spawn_entity('Player', (0,0))

        self.last_spawn = self.engine_time
        for i in range(1):
            self.spawn()

        self.lore_score = 0
        self.beans = 0
        self.field_richness = 0.75

#        self.add_entity(Wall(self, (0, 0), (self.camera.w, 0)))
#        self.add_entity(Wall(self, (self.camera.w, 0), (self.camera.w, self.camera.h)))
#        self.add_entity(Wall(self, (0, self.camera.h), (self.camera.w, self.camera.h)))
#        self.add_entity(Wall(self, (0, self.camera.h), (0, 0)))

        self.running = True

    def get_eid(self):
        self.eidhwm+=1
        return self.eidhwm

    def create_entity(self, name, *args, **kwargs):
        return entity_registry.create_entity(name, self, *args, **kwargs)

    def spawn_entity(self, name, *args, **kwargs):
        entity = self.create_entity(name, *args, **kwargs)
        self.add_entity(entity)
        return entity

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
        if random.random() < 0.01 and len(self.tracker['Zippy']) == 0:
            new_entity = self.create_entity('Zippy', pos)
        else:
            new_entity = self.create_entity('Ball', pos)

        self.add_entity(new_entity)
        self.last_spawn = self.engine_time

    def draw(self):

        if self.render_physics:
            self.space.debug_draw(self.draw_options)

        for entity in self.entities:
            entity.draw()

        header = self.font.render(f'{self.lore_score}', False, (0,0,128))
        self.screen.blit(header, (2,2))


        ypos = self.camera.h-2
        text = self.font.render(f'{TITLE}', False, (128,128,0))
        ypos -= text.get_height()
        self.screen.blit(text, (2,ypos))

        text = self.font.render(f'{SEED}', False, (128,128,0))
        ypos -= text.get_height()
        self.screen.blit(text, (2,ypos))

    def render_game(self):
        hello = pygame.transform.scale(self.screen, (self.ws, self.hs))
        self.main_screen.blit(hello, (0,0))

    def do_physics(self):
        M = 1
        N = 1
        dt = 1/(120*N)
        for _ in range(N*M):
            self.space.step(dt)

        self.engine_time += dt*N*M

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
        self.mpos_screen = pygame.mouse.get_pos()
        self.mpos = self.camera.s2w(self.mpos_screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif False:
                self.debug_console.handle_event(event)

        if self.run_physics or tick:
            self.screen.fill((255,255,255))

            self.do_updates()

            self.do_physics()

            self.draw()

        self.render_game()

        self.camera.update_scale()

        self.debug_console.draw(self.main_screen)

        pygame.display.flip()

        self.clock.tick(60)

#        pygame.display.set_caption(f"fps: {len(self.tracker['Ball'])}, {self.clock.get_fps():.2f}")

demo = PhysicsDemo()
demo.run()



























