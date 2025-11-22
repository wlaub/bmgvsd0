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

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == ord('`'):
                self.active = not self.active
                self.app.run_physics = not self.active
                if self.active:
                    pygame.key.start_text_input()
                else:
                    pygame.key.stop_text_input()

        if not self.active:
            return

        mods = pygame.key.get_mods()

        if event.type == pygame.TEXTINPUT:
            if event.text != '`':
                self.cmd_buffer = self.cmd_buffer[:self.cursor] + event.text + self.cmd_buffer[self.cursor:]
                self.cursor+=len(event.text)
        if event.type == pygame.KEYDOWN:
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
        except Exception as e:
            print(e)


    def draw(self, screen):
        if not self.active:
            return

        screen = self.app.main_screen
        w,h = self.app.ws, self.app.hs
        m = 14

        pygame.gfxdraw.box(screen, pygame.Rect(0,0,w,h), (0,0,0,49))


        bg_color = (0,0,0,173)
        font_color = (255,255,255)

        dh = self.fs + 6
        pygame.gfxdraw.box(screen, pygame.Rect(m,h-m-dh,w-2*m,dh), bg_color)
        ypos = h-m-dh+3
        text = self.font.render(f'> {self.cmd_buffer}', True, font_color)
        screen.blit(text, (m+3,ypos))

        text = self.font.render(f'> {self.cmd_buffer[:self.cursor]}', True, font_color)
        xpos = m+3+text.get_width()
        pygame.gfxdraw.line(screen, xpos, ypos, xpos, ypos+19, font_color)


