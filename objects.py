import random
import math
import enum
from collections import defaultdict

import pygame

from pygame.locals import *

import pymunk as pm
import pymunk.util
from pymunk import pygame_util
from pymunk import Vec2d

from registry import register, entity_registry

COLLTYPE_DEFAULT = 0

class ControlType(enum.Enum):
    joy = 0
    key = 1

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

    def pause(self):
#        if pygame.mouse.get_pressed()[0]:
#            self.last_kind = ControlType.key
#            return True
        if self.get_button('start'):
            self.last_kind = ControlType.joy
            if not self.last_pause:
                self.last_pause = True
                return True
            return False
        else:
            self.last_pause = False
            return False

    def __init__(self, app):
        self.app = app
        self.joystick = pygame.joystick.Joystick(0)
        self.last_kind = ControlType.joy

        self.last_stick = (0,0)
        self.last_mpos = (0,0)

        self.last_pause = False

    def update(self):
        if self.last_mpos != self.app.mpos_screen:
            self.last_mpos =  self.app.mpos_screen
            self.last_kind = ControlType.key

        xpos = self.joystick.get_axis(self.axis_map['lx'])
        ypos = self.joystick.get_axis(self.axis_map['ly'])
        if (xpos, ypos) != self.last_stick:
            self.last_kind = ControlType.joy
            self.last_stick = (xpos, ypos)

    def get_left_stick(self):
        if self.last_kind == ControlType.joy:
            return self.last_stick
        else:
            result = Vec2d(*self.app.mpos)-self.app.player.position
            if not self.get_right_trigger() and result.get_length_sqrd() < 64:
                return Vec2d(0,0)
            else:
                return result

    def get_right_trigger(self):
        if pygame.mouse.get_pressed()[0]:
            self.last_kind = ControlType.key
            return True
        if self.joystick.get_axis(self.axis_map['rt']) > 0.5:
            self.last_kind = ControlType.joy
            return True
        return False

    def equip(self):
        if pygame.mouse.get_pressed()[2]:
            self.last_kind = ControlType.key
            return True
        if self.joystick.get_axis(self.axis_map['lt']) > 0.5:
            self.last_kind = ControlType.joy
            return True
        return False

    def get_button(self, name):
        return self.joystick.get_button(self.button_map[name])

class Camera:
    def __init__(self, app, parent, position, scale):
        self.app = app
        self.parent = parent

        self.reference_position = position
        self.set_scale(scale)
        self.update_scale()
        self.update_position(position)

    def s2w(self, pos):
        pos = Vec2d(*pos)/self.scale
        pos += self.half_off
        return pos

    def w2s(self, pos):
        pos -= self.half_off
        pos *= self.scale
        return pos

    def set_scale(self, scale):
        self.pending_scale = scale

    def update_scale(self):
        if self.pending_scale is not None:
            self.scale = scale = self.pending_scale
            self.w = self.app.ws/scale
            self.h = self.app.hs/scale

            self.half_off = Vec2d(-self.w/2, -self.h/2)
            self.screen = pygame.Surface((self.w, self.h))
            self.physics_screen = pygame.Surface((self.w, self.h), flags=pygame.SRCALPHA)

            self.app.screen = self.screen
            self.app.draw_options = draw_options = pygame_util.DrawOptions(self.physics_screen)

            self.pending_scale = None

            self.update_position(self.reference_position)

    def update_position(self, position = None):
        if position is None and self.parent is None:
            return

        if self.parent is not None:
            self.reference_position = self.parent.body.position

        elif position is not None:
            self.reference_position = Vec2d(*position)
        self.position = self.reference_position+self.half_off

        self.left = self.position.x
        self.right = self.position.x+self.w
        self.up = self.position.y
        self.down = self.position.y+self.h

        self.lrud = (self.left, self.right, self.up, self.down)

        draw_options = self.app.draw_options
        draw_options.transform = pymunk.Transform.translation(*(self.reference_position-self.half_off))

    def draw_physics(self):
        self.physics_screen.fill((0,0,0,0))
        self.app.space.debug_draw(self.app.draw_options)
        self.physics_screen.set_alpha(128)
        self.screen.blit(self.physics_screen, (0,0), special_flags=pygame.BLEND_ALPHA_SDL2)

    def update(self):
        self.update_position()

    def contains(self, pos, margin=0):
        x,y = pos
        return x > self.left-margin and x < self.right+margin and y > self.up-margin and y < self.down+margin

    def get_distance(self, pos):
        x,y = pos

        if self.contains(pos):
            result = max(a for a in (self.left-x, x-self.right, self.up-y, y-self.down) if a < 0)
            return result
        else:
            result = min(a for a in (self.left-x, x-self.right, self.up-y, y-self.down) if a > 0)
            return result

    def draw_boundary(self, zoom_level, margin=0):

        w = self.app.ws/zoom_level+2*margin
        h = self.app.hs/zoom_level+2*margin

        left = (self.w-w)/2
        top = (self.h-h)/2

        rect = pygame.Rect(left, top, w, h)

        pygame.draw.rect(self.screen, (0,255,0), rect, 1)


    def get_boundary_point(self, t, margin=0):
        l,r,u,d = self.lrud
        l-=margin
        r+=margin
        u-=margin
        d+=margin
        if t < 0.25:
            x = l
            y = t       *4*(d-u)+u
        elif t < 0.5:
            x = r
            y = (t-0.25)*4*(u-d)+d
        elif t < 0.75:
            y = u
            x = (t-0.5) *4*(r-l)+l
        else:
            y = d
            x = (t-0.75)*4*(l-r)+r
        return Vec2d(x,y)


class Entity:
    track_as = set()

    def inspect(self):
        d = dict(self.__dict__)
        for k in {'debug_log', 'app'}:
            d.pop(k)
        lines = []
        for key, val in d.items():
            lines.append(f'  {key}: {val}')
        return '\n'.join(lines)

    def __str__(self):
        p = self.position
        name = self.__class__.__name__
        return f'E{self.eid:05} {p.x:6.1f} {p.y:6.1f} {name}'

    @property
    def ename(self):
        return self.__class__.__name__

    def __init__(self, app, parent = None, layer=None):
        self.app = app
        self.parent = parent
        self.last_hit = -100
        self.grace_time = 0.2
        self.spawn_engine_time = self.app.engine_time
        self.health = 1
        self.vocal = self.app.flags.getv('_vocal', False)
        self.eid = self.app.get_eid()
        self.layer = layer
        self.debug_log = []

    def get_tags(self):
        name = self.__class__.__name__
        return set(entity_registry.name_tags.get(name, set()))

    def __hash__(self):
        return self.eid

    def say(self, text):
        self.debug_log.append(text)
        if self.vocal:
            print(text)

    @property
    def position(self):
        return self.body.position

    @property
    def velocity(self):
        return self.body.velocity

    def draw(self):
        pass
    def update(self):
        pass
    def add_to_space(self, space):
        space.add(self.body, self.shape)
    def remove_from_space(self, space):
        space.remove(self.body, self.shape)

    def on_add(self):
        pass

    def on_remove(self):
        pass

    def get_hit(self, dmg):
      pass


    def _basic_hit_spell(self, dmg):
        if self.app.engine_time - self.last_hit > self.grace_time:
            self.health -= dmg
            self.last_hit = self.app.engine_time
            if self.health <= 0:
                self.app.remove_entity(self)
                return True
        return False

    def _advanced_hit_spell(self, dmg):
        if self.app.engine_time - self.last_hit > self.grace_time:
            self.health -= dmg
            self.last_hit = self.app.engine_time
            if self.health <= 0 and self.app.flags.getv('_death', True) is not False:
                self.app.remove_entity(self)
                return True
        return False



class Equipment(Entity):
    valid_slots = []
    is_feets = False
    pickup = None

class Enemy(Entity):
    def __init__(self, app):
        super().__init__(app)
        self.drops = []

    def get_hit(self, dmg):
        dead = self._basic_hit_spell(dmg)
        if dead:
            for drop in self.get_drops():
                drop.set_position(self.position + drop.position)
                self.app.add_entity(drop)
            self.app.remove_entity(self)

    def get_drops(self):
        return self.drops



class BallEnemy(Enemy):
    def __init__(self, app, pos, r, m, health, speed=150, friction =-10):
        super().__init__(app)
        self.r = r
        self.m = m
        self.speed = speed*m
        self.friction = friction*m

        self.moment = pm.moment_for_circle(m, 0, r)
        self.body = body = pm.Body(m, self.moment)
        body.position = Vec2d(*pos)

        self.shape = shape = pm.Circle(body, r)
#        shape.friction = 1.5
        shape.collision_type = COLLTYPE_DEFAULT

        self.health = health

    def draw(self):
        p = self.body.position + self.shape.offset.cpvrotate(self.body.rotation_vector)
        p = self.app.jj(p)

        color = (0,0,255)
        if self.app.engine_time-self.last_hit < 0.08:
            color = (255,0,0)

        pygame.draw.circle(self.app.screen, color, p, int(self.r), 2)


    def hit_player(self, player, dmg=1):
        try:
            hit = self.shape.shapes_collide(player.shape)
            player.get_hit(dmg)
        except AssertionError: pass

    def seek_player(self, player):
        delta = player.position-self.position
        delta /= abs(delta)
        self.body.apply_force_at_local_point(delta*self.speed)

    def apply_friction(self, player):
        friction = self.body.velocity*self.friction
        self.body.apply_force_at_local_point(friction)

    def update(self):
        self.normal_update()

    def normal_update(self):
        player = self.app.player
        if player is None: return
        self.hit_player(player)
        self.seek_player(player)
        self.apply_friction(player)

    def try_hit(self, shape):
        self.shape.shapes_collide(shape)

    def basic_ball_drops(self):
        if random.random() > 1-(self.r-5)/16: #heath drop
            return [self.app.create_entity('HealthPickup', Vec2d(0,0))]
        elif random.random() > 0.97-0.03*self.app.beans:
            if len(self.app.tracker['CoffeePotPickup']) == 0:
                return [self.app.create_entity('CoffeePotPickup', Vec2d(0,0))]
        else:
            return [self.app.field.make_lore_drop(Vec2d(0,0))]
        return []




class Pickup(Entity):
    def __init__(self, app, pos, r):
        super().__init__(app)
        self.body = body = pm.Body(body_type = pymunk.Body.STATIC)
        body.position = Vec2d(*pos)

        self.r = r
        self.shape = shape = pm.Circle(body, self.r)
        shape.sensor = True
        shape.collision_type = COLLTYPE_DEFAULT

    def set_position(self, pos):
        self.body.position = Vec2d(*pos)

    def draw(self):
        p = self.app.jj(self.body.position)
        color = (0,0,255)
        pygame.draw.circle(self.app.screen, color, p, int(self.r), 2)

    def update(self):
        player = self.app.player
        if player is None: return
        try:
            hit = self.shape.shapes_collide(player.shape)
            self.on_player(player)

        except AssertionError: pass

    def on_player(self, player):
        self.app.remove_entity(self)


class Geography:
    def __init__(self, app):
        self.app = app
        self.current_props = {
            'richness': 1.0,
            'fidelity': 0.5,
            'capacity': 50,
            'austerity': 0.2,
            }

        self.prev_props = {}

    def update(self, pos):
        self.prev_props = self.current_props
        #TODO update current props?

    def get(self, name, default=None):
        return self.current_props.get(name, default)

    def make_lore_drop(self, pos):
        #TODO: tune deviancy coefficient
        deviancy = self.get('richness') - self.get('fidelity')
        #positive needs bias down
        #negative needs bias up
        if random.random() > self.get('richness'):
            self.current_props['richness'] += 0.01 * min(math.exp(-deviancy),1)
#            print(f"bean {deviancy:.2f} {self.current_props['richness']:.3f}")
            return self.app.create_entity('BeanPickup', pos)
        else:
            self.current_props['richness'] -= 0.01 * min(math.exp(deviancy),1)
#            print(f"lore {deviancy:.2f} {self.current_props['richness']:.3f}")
            return self.app.create_entity('LoreOrePickup', pos)



class Flags:
    def __init__(self):
        self.flags = {}
        self.volatile_flags = {}

        self.on_set = []
        self.on_flag = defaultdict(list)

    def getnv(self, name, default = None):
        return self.flags.get(name, default)

    def getv(self, name, default = None):
        return self.volatile_flags.get(name, default)


    def setnv(self, name, value=True):
        old_value = self.flags.get(name, None)
        self.flags[name] = value
        self.run_on_set(name, old_value, value, volatile=False)

    def setv(self, name, value=True):
        old_value = self.volatile_flags.get(name, None)
        self.volatile_flags[name] = value
        self.run_on_set(name, old_value, value, volatile=True)


    def clearnv(self, name):
        old_value = self.flags.pop(name, None)
        self.run_on_set(name, old_value, None, volatile=False)

        return old_value

    def clearv(self, name):
        old_value = self.volatile_flags.pop(name, None)
        self.run_on_set(name, old_value, None, volatile=True)

        return old_value



    def run_on_set(self, name, old_value, new_value, volatile):
        for cb in self.on_set:
            try:
                cb(name, old_value, new_value, volatile)
            except Exception as e:
                print(f'exception in Flags.on_set cb {cb} {name=} {old_value=} {new_value=} {volatile=}')
                print(str(e))
        for cb in self.on_flag[name]:
            try:
                cb(name, old_value, new_value, volatile)
            except Exception as e:
                print(f'exception in Flags.on_flag({name}) cb {cb} {name=} {old_value=} {new_value=}, volatile=')
                print(str(e))


