import math

import pygame

from pymunk import Vec2d

class MenuOption:
    def __init__(self, app, text, xpos, ypos, height, font = None, center=True):
        self.app = app
        self.text = text
        self.xpos = xpos
        self.ypos = ypos
        self.height = height
        self.active_color = (0,0,255)
        self.norml_color = (0,0,0)
        self.font = font or self.app.big_font
        self.center = center

        self.on_select = None

        self.render_screens()

        self.directions = {}

    def render_text(self, color):
        text = self.font.render(self.text, False, color)
        text = pygame.transform.scale_by(text, self.height/text.get_height())
        return text


    def render_screens(self):
        self.active_text = self.render_text(self.active_color)
        self.normal_text = self.render_text(self.norml_color)

        if self.center:
            self.xpos -= self.normal_text.get_width()/2

    def render(self, screen, active):
        text = self.active_text if active else self.normal_text
        x = self.xpos
        y = self.ypos

        screen.blit(text, (x,y))



class Menu:
    def __init__(self, app):
        self.app = app

        self.active = None

        self.options = []

        self.stick_state = False

        self.debounce = False

    def make_vertical_menu(self, labels, font_size, default=None, callbacks = None, offset = 0, looping = True):
        xpos = self.app.ws/2
        ypos = self.app.hs/2-font_size*(len(labels)+offset)/2+offset*font_size

        for idx, label in enumerate(labels):
            m = MenuOption(self.app, label, xpos,ypos,font_size)
            if callbacks is not None:
                m.on_select = callbacks.get(idx, callbacks.get(label, None))
            if idx > 0:
                m.directions['up'] = self.options[-1]
                self.options[-1].directions['down'] = m

            self.options.append(m)
            ypos += font_size
            if default == idx or default == label:
                self.active = m

        if looping:
            self.options[-1].directions['down'] = self.options[0]
            self.options[0].directions['up'] = self.options[-1]

        if self.active is None:
            self.active = self.options[0]

    def make_question_menu(self, query, answers, font_size, default=None, callbacks = None, offset = 0):
        lines = query.split('\n')
        xpos = self.app.ws/2
        ypos = self.app.hs/2-font_size*len(lines)

        for line in lines:
            m = MenuOption(self.app, line, xpos, ypos, font_size)
            self.options.append(m)
            ypos += font_size

        for idx, answer in enumerate(answers):
            x = xpos - self.app.ws/4
            if idx%2 == 1:
                x += self.app.ws/2
            m = MenuOption(self.app, answer, x,ypos,font_size)
            if callbacks is not None:
                m.on_select = callbacks.get(idx, callbacks.get(answer, None))
            if idx > 0:
                if idx%2 == 0: #left side
                    pass
                else: #right side
                    m.directions['left'] = self.options[-1]
                    self.options[-1].directions['right'] = m
                if idx > 1:
                    m.directions['up'] = self.options[-2]
                    self.options[-2].directions['down'] = m

            self.options.append(m)
            if idx%2 == 1:
                ypos += font_size
            if default == idx or default == answer:
                self.active = m

        if self.active is None:
            self.active = self.options[0]



    def render(self, screen):
        for option in self.options:
            option.render(screen, option == self.active)


    def update(self):
        if self.app.controller.equip() or self.app.controller.get_right_trigger() or self.app.controller.get_button('a'):
            if self.debounce and self.active.on_select is not None:
                self.active.on_select()
        else:
            self.debounce = True

        stick = Vec2d(*self.app.controller.get_left_stick())
        dist = abs(stick)

        if self.stick_state and dist < 0.5:
            self.stick_state = False
        elif not self.stick_state and dist > 0.75:
            self.stick_state=True
            angle = stick.angle*4/math.pi
            if angle < -1:
                angle += 8

            if angle > -1 and angle <= 1:
                d = 'right'
            elif angle > 1 and angle <= 3:
                d = 'down'
            elif angle > 3 and angle <= 5:
                d = 'left'
            elif angle > 5 and angle <= 7:
                d = 'up'
            elif angle > 7 and angle < 9:
                d = 'right'

            if d in self.active.directions.keys():
                self.active = self.active.directions[d]






