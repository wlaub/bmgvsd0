import sys, os
import math
import random
import time
import datetime

from collections import defaultdict

import pygame
import pygame.gfxdraw

import pymunk as pm
import pymunk.util
from pymunk import pygame_util
from pymunk import Vec2d

from registry import register, entity_registry


class EntityButton:
    def __init__(self, console, entity, w, h):
        self.app = console.app
        self.console = console
        self.entity = entity
        self.w = w
        self.h = h

        self.l = 0
        self.r = 0
        self.t = 0
        self.b = 0

    def set_size(self, l,r,t,b):
        self.l, self.r, self.t, self.b = l,r,t,b

    def get_hit(self, pos):
        x,y = pos
        return x > self.l and x < self.r and y < self.b and y > self.t


class DebugConsole:

    def __init__(self, app):
        self.app = app
        self.active = False

        self.fs = 19
        self.font = pygame.font.SysFont('mono', self.fs, bold=True)

        self.cmd_buffer = ''
        self.history = []
        self.history_idx = -1
        self.stashed = ''
        self.cursor = 0

        self.entity_list = []
        self.hides = set()
        self.shows = set()

    def get_entity_list(self):
        result = []
        for entity in self.app.entities:
            tags = entity.get_tags()
            if self.hides & tags:
                continue
            if len(self.shows) == 0 or self.shows&tags:
                result.append(EntityButton(self, entity, 100, 20))

            if len(result) == 24:
                break
        return result

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == ord('`'):
                self.active = not self.active
                self.app.run_physics = not self.active
                if self.active:
                    pygame.key.start_text_input()
                    self.entity_list = self.get_entity_list()
                else:
                    pygame.key.stop_text_input()

        if not self.active:
            return

        self.hovered_button = None
        for button in self.entity_list:
            if button.get_hit(self.app.mpos_screen):
                self.hovered_button = button

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered_button is not None:
                e  = self.hovered_button.entity
                print(f'\n{e}:')
                print(e.inspect())

        mods = pygame.key.get_mods()

        if event.type == pygame.TEXTINPUT:
            if event.text != '`':
                self.cmd_buffer = self.cmd_buffer[:self.cursor] + event.text + self.cmd_buffer[self.cursor:]
                self.cursor+=len(event.text)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.cmd_buffer = self.cmd_buffer[:self.cursor-1]+self.cmd_buffer[self.cursor:]
                self.cursor -=1
            elif event.key == pygame.K_DELETE:
                self.cmd_buffer = self.cmd_buffer[:self.cursor]+self.cmd_buffer[self.cursor+1:]
            elif event.key == pygame.K_u and mods & (pygame.K_LCTRL|pygame.K_RCTRL):
                self.cmd_buffer = self.cmd_buffer[self.cursor:]
                self.cursor = 0
            elif event.key == pygame.K_RETURN:
                self.execute_cmd()
            elif event.key == pygame.K_LEFT:
                if self.cursor > 0:
                    self.cursor -=1
            elif event.key == pygame.K_RIGHT:
                if self.cursor < len(self.cmd_buffer):
                    self.cursor +=1
            elif event.key == pygame.K_END:
                self.cursor = len(self.cmd_buffer)
            elif event.key == pygame.K_HOME:
                self.cursor = 0

            elif event.key == pygame.K_UP:
                if self.history_idx < len(self.history)-1:
                    self.history_idx += 1
                    if self.history_idx == 0:
                        self.stashed = self.cmd_buffer
                    self.cmd_buffer = self.history[self.history_idx]

            elif event.key == pygame.K_DOWN:
                if self.history_idx > 0:
                    self.history_idx -= 1
                    self.cmd_buffer = self.history[self.history_idx]
                else:
                    self.cmd_buffer = self.stashed
                    self.history_idx = -1

    def execute_cmd(self):
        full_cmd = self.cmd_buffer
        if len(self.history) == 0 or full_cmd != self.history[0]:
            self.history.insert(0,full_cmd)
        self.history_idx = -1
        self.cmd_buffer = ''
        self.stashed = ''
        self.cursor = 0

        parts = full_cmd.split()
        cmd = parts[0]

        try:
            if cmd == 'spawn':
                name = parts[1]
                self.app.spawn_entity(name, self.app.mpos)
                self.entity_list = self.get_entity_list()
            elif cmd == 'equip':
                slot = parts[1]
                name = parts[2]
                self.app.player.equip(slot, name)
                self.entity_list = self.get_entity_list()
            elif cmd == 'drop':
                slot = parts[1]
                self.app.player.drop_equipment(slot)
                self.entity_list = self.get_entity_list()
            elif cmd == 'hide':
                self.hides = set()
                if len(parts) > 1:
                    name = parts[1]
                    self.hides.add(name)
                self.entity_list = self.get_entity_list()
            elif cmd == 'show':
                self.shows = set()
                if len(parts) > 1:
                    name = parts[1]
                    self.shows.add(name)
                self.entity_list = self.get_entity_list()
            elif cmd == 'give':
                what = parts[1].lower()
                if what == 'bean':
                    self.app.beans+=1
                elif what == 'lore':
                    self.app.lore_score+=1
            elif cmd == 'pain':
                self.app.player.can_get_hurt = not self.app.player.can_get_hurt
        except Exception as e:
            print(e)


    def draw(self, screen):
        if not self.active:
            return

        screen = self.app.main_screen
        w,h = self.app.ws, self.app.hs
        m = 11

        pygame.gfxdraw.box(screen, pygame.Rect(0,0,w,h), (0,0,0,49))


        bg_color = (0,0,0,173)
        font_color = (255,255,255)

        #command line

        dh = self.fs + 6
        pygame.gfxdraw.box(screen, pygame.Rect(m,h-m-dh,w-2*m,dh), bg_color)
        ypos = h-m-dh+3
        text = self.font.render(f'> {self.cmd_buffer}', True, font_color)
        screen.blit(text, (m+3,ypos))

        ## cursor
        text = self.font.render(f'> {self.cmd_buffer[:self.cursor]}', True, font_color)
        xpos = m+3+text.get_width()
        pygame.gfxdraw.line(screen, xpos, ypos, xpos, ypos+19, font_color)

        # entity listo

        dh = self.fs + 6

        dw = 0
        texts = []
        for button in self.entity_list:
            text = self.font.render(f'{button.entity}', True, font_color)
            dw = max(text.get_width()+6, dw)
            texts.append(text)

        r = w-m
        l = r-dw
        t = 0+m+1
        b = t+dh
        for text, button in zip(texts, self.entity_list):
            color = bg_color
            if button == self.hovered_button:
                color = (128,128,128,bg_color[3])

            button.set_size(l,r,t,b)

            pygame.gfxdraw.box(screen, pygame.Rect(l, t, dw, dh), color)

            screen.blit(text, (l+3, t+3))
            t += dh+3
            b = t+dh



        #infopane
        cpos = self.app.camera.reference_position
        health = 0
        if self.app.player is not None:
            health = self.app.player.health

        now = datetime.datetime.now()
        dt = now-self.app.startup_time

        info_text = f"""
{self.app.engine_time:7.2f} {int(self.app.engine_time*120):07} {dt}
{cpos.x:6.1f} {cpos.y:6.1f} {self.app.mpos.x:6.1f} {self.app.mpos.y:6.1f} {len(self.app.entities):05}
{health:03} {self.app.lore_score:05} {self.app.beans:05}
"""
        texts = []
        dw = 0
        for line in info_text.split('\n'):
            if len(line.strip()) == 0: continue
            text = self.font.render(line, True, font_color)
            dw = max(text.get_width()+6, dw)
            texts.append(text)

        ls = 0
        dh = self.fs*len(texts)+(ls*len(texts)-1) + 6

        l = m
        r = m+dw
        t = 0+m+1
        b = t+dh
        pygame.gfxdraw.box(screen, pygame.Rect(l, t, dw, dh), bg_color)
        for text in texts:

            screen.blit(text, (l+3, t+3))
            t += self.fs

        # entity indicator
        if self.hovered_button is not None:
            entity = self.hovered_button.entity
            p = self.app.camera.w2s(entity.position)
            r = 49
            x = round(min(max(p.x, -r/2), self.app.ws+r/2))
            y = round(min(max(p.y, -r/2), self.app.hs+r/2))
            pygame.gfxdraw.filled_circle(self.app.main_screen, x, y, r, (255,0,0,64))
            pygame.gfxdraw.filled_circle(self.app.main_screen, x, y, 1, (0,255,0))









