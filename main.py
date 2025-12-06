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

from objects import Controller, Entity, COLLTYPE_DEFAULT, Camera, ControlType, Flags, Geography

from debug import DebugConsole

import player
import entities
import pickups
import guns
import feets
import spawnoliths

IS_DEBUG = bool(os.getenv('DEBUG', False))

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

        pygame.mouse.set_visible(False)

        self.font = pygame.font.Font(None, 14)

        self.big_font = pygame.font.Font(None, 14) #lol

        self.queue_reset = False
        self.redraw = False

        self.flags = Flags()

        self.reset()

    def get_fleshtime(self, now):
        return self.fleshtime

    def update_fleshtime(self, now):
        self.fleshtime = now-self.flags.getv('_startup_time')-datetime.timedelta(seconds=self.pause_duration)

    def pause(self):
        if self.paused:
            return
        self.pause_stamp = time.time()
        self.paused = True
        self.run_physics = False

    def unpause(self):
        if not self.paused:
            return
        self.pause_duration += time.time()-self.pause_stamp
        self.paused = False
        self.run_physics = True

    def reset(self):

        self.engine_time = 0

        loop = self.flags.getv('_loop')

        self.flags.volatile_flags = {}

        self.pause_duration = 0
        self.pause_stamp = None
        self.paused = False
        self.fleshtime = None
        self.flags.setv('_startup_time', datetime.datetime.now())
        self.flags.setv('_first_spawns', {})
        self.flags.setnv('_show_score', True) #TODO nv state and defaults
        self.flags.setnv('_show_title', True) #
        self.flags.setnv('_show_seed', True) #
        self.flags.setnv('_render_physics', False)
#        self.flags.setnv('_title_screen', True) #TODO

        if loop is not None:
            self.flags.setv('_loop')

        self.coroutines = set()

        self.field = Geography(self)

        self.forget_range = 2

        def _on_vocal(name, old_value, new_value, volatile):
            if new_value:
                for entity in self.entities:
                    entity.vocal = True
            else:
                for entity in self.entities:
                    entity.vocal = False
        self.flags.on_flag['_vocal'].append(_on_vocal)

        self.debug_console = DebugConsole(self)

        self.camera = Camera(self, None, (0,0), 4)

        self.controller = Controller(self)

        self.field.update(self.camera.position)

        ### Init pymunk and create space
        self.run_physics = True
        self.space = pm.Space()
#        self.space.gravity = (0.0, -900.0)

        self.eidhwm = 0
        self.entities = []
        self.entity_map = {}
        self.draw_layers = defaultdict(list)
        self.tracker = defaultdict(list)

        #TODO
        self.spawn_entity('BallSpnlþ', (-800, 000), layer=100)
        self.spawn_entity('ZippySpnlþ', (800, 000), layer=100)

        self.player = self.spawn_entity('Player', (0,0), layer=10)

        self.spawn_entity('SordPickup', (16,-4))


        self.last_spawn = self.engine_time

        self.lore_score = 0
        self.beans = 0

        self.running = True
        self.queue_reset = False

    def start_game(self):
        if not self.flags.getv('_game_start', False):
            self.flags.setv('_game_start')
            self.flags.setv('_startup_time', datetime.datetime.now())
            self.flags.setv('_startup_engine_time', self.engine_time)

    def get_eid(self):
        self.eidhwm+=1
        return self.eidhwm

    def create_entity(self, name, *args, **kwargs):
        first_spawns = self.flags.getv('_first_spawns')
        if not name in first_spawns.keys():
            first_spawns[name] = self.engine_time
        result = entity_registry.create_entity(name, self, *args, **kwargs)
        if self.flags.getv('_map_creation'):
            self.entity_map[result.eid] = result
        return result

    def spawn_entity(self, name, *args, **kwargs):
        layer = kwargs.pop('layer', 0) #TODO this is zoness???
        entity = self.create_entity(name, *args, **kwargs)
        self.add_entity(entity, layer=layer)
        return entity

    def add_entity(self, e, layer=0):
        e.add_to_space(self.space)
        self.entities.append(e)
        self.entity_map[e.eid] = e
        e.layer=layer #TODO this is awful
        self.draw_layers[layer].append(e)
        class_name = e.__class__.__name__
        for tag in entity_registry.name_tags[class_name]:
            self.tracker[tag].append(e)
        e.on_add()

    def remove_entity(self, e, preserve_physics = False):
        if not preserve_physics:
            e.remove_from_space(self.space)
        self.entities.remove(e)
        if not self.flags.getv('_preserve_ghosts'):
            self.entity_map.pop(e.eid)
        self.draw_layers[e.layer].remove(e)
        class_name = e.__class__.__name__
        for tag in entity_registry.name_tags[class_name]:
            self.tracker[tag].remove(e)
        e.on_remove()



    def spawn(self):
        new_entities = []
        for entity in self.tracker['Spnlþ']:
            new_entities.extend(entity.spawn())

        for new_entity in new_entities:
            self.add_entity(new_entity)

        if len(new_entities) > 0:
            self.last_spawn = self.engine_time

    def draw(self):

        for layer in sorted(self.draw_layers.keys()):
            for entity in self.draw_layers[layer]:
                entity.draw()

        if self.flags.getnv('_render_physics'):
            self.camera.draw_physics()


        if self.flags.getnv('_show_score'):
            header = self.font.render(f'{self.lore_score}', False, (0,0,128))
            self.screen.blit(header, (2,2))

        if not self.flags.getv('_game_start') and self.flags.getnv('_title_screen'):
            ypos = 20
            text = self.big_font.render(f'BLDNG MAN: GAIDN', False, (0,0,0))
            width = self.camera.w*0.8
            alpha = width/text.get_width()
            text = pygame.transform.scale_by(text, alpha)
            self.screen.blit(text, ((self.camera.w-width)/2,ypos))
            ypos += text.get_height()

            text = self.big_font.render(f"VLT'L STATE", False, (0,0,0))
#            alpha *=0.915
            alpha *=1.03
            text = pygame.transform.scale_by(text, alpha)
            self.screen.blit(text, (self.camera.w-(self.camera.w-width)/2-text.get_width(),ypos))
            ypos += text.get_height()
            text = self.big_font.render(f"DEMO 0", False, (0,0,0))
            alpha *=0.84
            text = pygame.transform.scale_by(text, alpha)
            self.screen.blit(text, (self.camera.w-(self.camera.w-width)/2-text.get_width(),ypos))
            ypos += text.get_height()




        ypos = self.camera.h-2
        if self.flags.getnv('_show_title'):
            text = self.font.render(f'{TITLE}', False, (128,128,0))
            ypos -= text.get_height()
            self.screen.blit(text, (2,ypos))

        if self.flags.getnv('_show_seed'):
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
        #TODO: if camera moved
        self.field.update(self.camera.position)
        #TODO update spawnoliths?

        dt = self.engine_time-self.last_spawn
        c = self.field.get('capacity')
        f = self.field.get('austerity')
        if len(self.tracker['EquipPckp']) == 0 and dt > f + len(self.tracker['Enemy'])/c:

            self.spawn()

        for entity in self.entities:
            entity.update()

        #TODO
        for entity in self.entities:
            self.try_forget(entity)


        removals = []
        for coro in self.coroutines:
            try:
                next(coro)
            except StopIteration:
                removals.append(coro)

        for coro in removals:
            self.coroutines.remove(coro)

    def try_forget(self, entity):
        dist = self.camera.get_distance(entity.position)
        mdist = self.camera.w*self.forget_range
        if dist > mdist:
            p = (dist-mdist)/abs(mdist)
            if random.random() < p:
                self.remove_entity(entity)


    def loop(self):
        if self.queue_reset:
            self.reset()

        tick = False
        self.keys = pygame.key.get_pressed()
        self.mpos_screen = pygame.mouse.get_pos()
        self.mpos = self.camera.s2w(self.mpos_screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif IS_DEBUG:
                self.debug_console.handle_event(event)

        self.controller.update()

        now = datetime.datetime.now()
        if self.controller.pause():
            if self.paused:
                self.unpause()
            else:
                self.pause()

        if self.run_physics or tick:
            self.screen.fill((255,255,255))
            self.update_fleshtime(now)

            self.do_updates()

            self.do_physics()

        if self.run_physics or self.redraw:
            self.draw()


        self.render_game()

        self.camera.update_scale()

        if self.redraw:
            self.screen.fill((255,255,255))
            self.draw()
            self.render_game()
            self.redraw = False

        if self.paused:
            w,h = self.ws, self.hs
            pygame.gfxdraw.box(self.main_screen, pygame.Rect(0,0,w,h), (0,0,0,49))

        self.debug_console.draw(self.main_screen)

        if (not self.run_physics or self.controller.last_kind is ControlType.key) and pygame.mouse.get_focused():
            pygame.draw.circle(self.main_screen, (0,0,0), self.mpos_screen, 2)

        pygame.display.flip()

        self.clock.tick(60)

#        pygame.display.set_caption(f"fps: {len(self.tracker['Ball'])}, {self.clock.get_fps():.2f}")

demo = PhysicsDemo()
demo.run()



























