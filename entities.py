import math
import random
import time
import enum

import pygame

import pymunk as pm
import pymunk.util
from pymunk import Vec2d

from registry import register, entity_registry

from objects import Controller, Entity, COLLTYPE_DEFAULT, BallEnemy
#from pickups import HealthPickup, LoreOrePickup, LengthPickup, BeanPickup, CoffeePotPickup

"""
need a debug console that can spawn enemies and stuff

and eye boss drops portable camera pickup
"""

@register
class Zippy(BallEnemy):
    """
    its eyes remain perpetually closed in a deep slumber, but if it gets
    enough beans it might wake up and open its eyes
    """

    track_as = {'Enemy'}
    def __init__(self, app, pos):
        super().__init__(app, pos, 3, 32*32/1.8, 3, 1200)
        self.direction = Vec2d(0,0)
        self.going = False
        self.cooldown = self.app.engine_time
        self.can_stop = False
        self.beans = 0

    def update(self):
        player = self.app.player
        if player is None: return
        self.hit_player(player)

        beans = self.app.tracker['BeanPickup']

        if not self.going and (self.app.engine_time-self.cooldown > 0 or self.app.camera.contains(self.position, 1)):
#            print('going')
            self.going = True
            self.can_stop = False


            target = player
            for bean in beans:
                if self.app.camera.contains(bean.position, 0):
                    self.say('bean')
                    target = bean
                    break

            delta = target.position-self.position
            delta /= abs(delta)
            self.direction = delta*self.speed
            self.friction = -10*self.m

        if self.going:

            for bean in beans:
                try:
                    hit = self.shape.shapes_collide(bean.shape)
                    self.say('bwned')
                    self.beans+= 1
                    self.app.remove_entity(bean)
                    if self.beans == 7:
                        self.app.remove_entity(self)
                        self.app.spawn_entity('Zeeky', self.position)
                        return

                except AssertionError: pass

            self.body.apply_force_at_local_point(self.direction)

            if not self.can_stop and self.app.camera.contains(self.position, 0):
                self.say('can stop')
                self.can_stop = True

            if self.can_stop and not self.app.camera.contains(self.position, 50):
                self.say('stopping')
                self.going = False
                self.cooldown = self.app.engine_time+5/(1+self.beans)
                self.friction = -100*self.m

        self.apply_friction(player)

    def get_drops(self):
        result = []
        if random.random() < 0.1 and  len(self.app.tracker['CoffeePotPickup']) == 0:
           result.append(self.app.create_entity('CoffeePotPickup', self.position))

        result.append(self.app.create_entity('BeanPickup', self.position))
        t = random.random()
        M = 7 + int(self.beans/7)*7
        N = int((M+1)*t)
        if N > 0:
            a = random.random()
            for i in range(N+1):
                aa = a+2*math.pi*i/M
                dx,dy = random.random()-0.5, random.random()-0.5
                r = 7+2*i%2
                result.append(self.app.create_entity('LoreOrePickup',
                    self.position + Vec2d(r*math.cos(aa)+dx, r*math.sin(aa)+dy)
                    ))

        return result


@register
class Zeeky(BallEnemy):
    track_as = {'Enemy'}
    def __init__(self, app, pos):
        super().__init__(app, pos, 3, 32*32/1.8, 3, 1200)
        self.direction = Vec2d(0,0)
        self.going = False
        self.cooldown = self.app.engine_time
        self.can_stop = False
        self.beans = 0
        self.target = None
        self.target_position = None

        self.zeek_radius = 90


    def update(self):
        player = self.app.player
        if player is None: return
        self.hit_player(player)

        beans = self.app.tracker['Zbln']
        if len(beans) == 0:
            beans = self.app.tracker['Zeeky']

        if self.target is None:
            self.target = player
            self.target_position = self.target.position

        if not self.going:
            self.say('going')
            self.going = True
            self.can_stop = False
            for bean in beans:
                if bean is not self and self.app.camera.contains(bean.position, 0):
                    self.say('hello there')
                    self.target = bean
                    break
            else:
                self.target = player

            self.target_position = self.target.position
            delta = self.target_position-self.position
            r = abs(delta)
            r2=r

            if r != 0:
                delta /= r
                self.direction = delta*self.speed
                self.friction = -10*self.m
            else:
                self.going = False
                self.direction = Vec2d(0,0)
        else:
            delta = self.target_position-self.position
            r = abs(delta)
            r2 = abs(self.target.position-self.position)


        if self.going:
            for bean in beans:
                if bean is self: continue
                try:
#                    hit = self.shape.shapes_collide(bean.shape)
                    bean.try_hit(self.shape)
                    if isinstance(bean, Zeeky):
                        self.say('blessed union')
                        #TODO merge into new enemy
                        #this is why body management needs unfucked
                        self.app.remove_entity(bean, preserve_physics = True)
                        self.app.remove_entity(self, preserve_physics = True)
                        body_map = {
                            bean.body: (bean.shape,),
                            self.body: (self.shape,),
                            }
                        #TODO someday
    #                    self.app.spawn_entity('Zbln', body_map)
                        return
                    else:
                        bean.absorb(self)
                        #TODO merge with zbln some day
                        pass
                except AssertionError: pass

            self.body.apply_force_at_local_point(self.direction)

            if not self.can_stop and min(r,r2) < self.zeek_radius-5:
                self.say('can stop')
                self.can_stop = True

            if self.can_stop and max(r,r2) > self.zeek_radius:
                self.say('stopping')
                self.going = False
                self.cooldown = self.app.engine_time+5
                self.friction = -100*self.m

        self.apply_friction(player)

    def get_drops(self):
        result = []
        #TODO
        return result


@register
class Zbln(BallEnemy):
    track_as = {'Enemy'}
    def __init__(self, app, body_map):
        super(BallEnemy,self).__init__(app)

        if isinstance(body_map, Vec2d):
            pos = body_map
            a = self.app.create_entity('Zeeky', pos+Vec2d(-1.5, 0))
            b = self.app.create_entity('Zeeky', pos+Vec2d(1.5, 0))

            a.add_to_space(self.app.space)
            b.add_to_space(self.app.space)

            body_map = {
                a.body: (a.shape,),
                b.body: (b.shape,),
                }

        self.health = 16
        self.last_hit = -10

        self.body_map = body_map

        my_list = list(body_map.items())
        self.joints = []
        for a,b in zip(my_list[:-1], my_list[1:]):
            c = pymunk.PinJoint(a[0],b[0])
            self.joints.append(c)

        self.base_speed = 100
        self.base_friction = -0.5

        self.m = 0
        self.shapes = []
        for body, shapes in self.body_map.items():
            self.shapes.extend(shapes)
            self.m += body.mass

        m = self.m
        self.speed = self.base_speed*m
        self.friction = self.base_friction*m

        self.get_position()
        self.my_velocity = Vec2d(0,0)

    def add_to_space(self, space):
#        for body, shapes in self.body_map.items():
#            space.add(body, *shapes)

        for c in self.joints:
            space.add(c)

    def remove_from_space(self, space):
        for body, shapes in self.body_map.items():
            space.remove(body, *shapes)

    def get_position(self):
        total = Vec2d(0,0)
        for body, shapes in self.body_map.items():
            total += body.position
        total /= len(self.body_map)
        self.my_position = total

    @property
    def position(self):
        return self.my_position

    @property
    def velocity(self):
        return self.my_velocity

    def absorb(self, other):
        self.app.remove_entity(other, preserve_physics = True)
        body, shape = other.body, other.shape
        self.body_map[body] = (shape,)
        c = pymunk.PinJoint(body, self.last_hit_body)
        self.joints.append(c)
        self.app.space.add(c)

#        self.m+=body.mass
#        m = self.m
#        self.speed = self.base_speed*m
#        self.friction = self.base_friction*m

    def hit_player(self, player, dmg=1):
        for shape in self.shapes:
            try:
                hit = shape.shapes_collide(player.shape)
                player.get_hit(dmg)
            except AssertionError: pass

    def try_hit(self, other_shape):
        for body, shapes in self.body_map.items():
            for shape in shapes:
                try:
                    hit = other_shape.shapes_collide(shape)
                    self.my_velocity = body.velocity
                    self.last_hit_body = body
                    break
                except AssertionError: pass
            else: continue
            break #i take it back this is the worst thing i have ever done
        else:
            raise AssertionError #This is the worst thing i have ever done

    def seek_player(self, player):
        delta = player.position-self.position
        delta /= abs(delta)
        for body in self.body_map.keys():
            body.apply_force_at_local_point(delta*self.speed)

    def apply_friction(self, player):
        vel = Vec2d(0,0)
        for body in self.body_map.keys():
            vel+= body.velocity
        vel/=len(self.body_map)

        friction = vel*self.friction
        for body in self.body_map.keys():
#            friction = body.velocity*self.friction

            body.apply_force_at_local_point(friction)



    def update(self):
        self.get_position()
        self.normal_update()

        #TODO spawn zeeky sometimes

    def draw(self):
        for body, shapes in self.body_map.items():
            for shape in shapes:
                p = body.position + shape.offset.cpvrotate(body.rotation_vector)
                p = self.app.jj(p)

                color = (0,0,255)
                if self.app.engine_time-self.last_hit < 0.08:
                    color = (255,0,0)

                pygame.draw.circle(self.app.screen, color, p, round(shape.radius), 2)



class BallState(enum.Enum):
    NORML = 0
    FGTFL = 1
    LSTFL = 2

@register
class Ball(BallEnemy):
    track_as = {'Enemy'}

    update_map = {
        BallState.NORML: BallEnemy.update,
        }

    def __str__(self):
        p = self.position
        return f'{super().__str__()} {self.state.name}'

    def __init__(self, app, pos, r = None, m = None, h = None):
        if r is None:
            r= 4+4*random.random()
            m = r*r/1.8
            h = r/4
        super().__init__(app, pos, r, m, h)
        self.last_aggro = 0
        self._going = True
        self.lores = 0

        if random.random() > 0.15:
            self.set_state(BallState.NORML)
        else:
            self.set_state(BallState.FGTFL)

    def set_state(self, state):
        self.state = state
        if state is BallState.NORML:
            self.update = self.normal_update
        elif state is BallState.FGTFL:
            self.update = self.forgetful_update
        elif state is BallState.LSTFL:
            self.update = self.lustful_update

    def forgetful_update(self):
        player = self.app.player
        if player is None: return
        self.hit_player(player)

        dt = self.app.engine_time-self.last_aggro
        delta = player.position-self.position
        r = abs(delta)

        if self._going and dt > 10:
            self._going = False
            lores = self.app.tracker['LoreOrePickup']
            for lore in lores:
                try:
                    hit = self.shape.shapes_collide(lore.shape)
                    self.say("what's this?")
                    self.app.remove_entity(lore)
                    self.set_state(BallState.LSTFL)
                    break
                except AssertionError: pass

        if not self._going and dt > 15:
            if r < 80:
                self.last_aggro = self.app.engine_time
                self._going = True

        if self._going:
            self.seek_player(player)

        self.apply_friction(player)

    def lustful_update(self):
        player = self.app.player
        if player is None: return
        self.hit_player(player)

        target = player
        lores = self.app.tracker['LoreOrePickup']

        if len(lores) > 0:
            target = lores[0]

            try:
                hit = self.shape.shapes_collide(target.shape)
                self.lores+= 1
                self.app.remove_entity(target)
                target = player
            except AssertionError: pass

        self.seek_player(target)

        self.apply_friction(player)

    def get_drops(self):
        if random.random() > 1-(self.r-5)/16: #heath drop
            return [self.app.create_entity('HealthPickup', self.position)]
        elif random.random() > 1-self.r/8: #lore/bean
            if random.random() > self.app.field_richness:
                return [self.app.create_entity('BeanPickup', self.position)]
            else:
                return [self.app.create_entity('LoreOrePickup', self.position)]
        elif random.random() > .75 and self.r > 7: #length pickup
            return [self.app.create_entity('LengthPickup', self.position)]
        elif random.random() > 0.97-0.03*self.app.beans:
            if len(self.app.tracker['CoffeePotPickup']) == 0:
                return [self.app.create_entity('CoffeePotPickup', self.position)]
        return []

@register
class Wall(Entity):
    def __init__(self, app, start, end):
        super().__init__(app)
        self.start = start
        self.end = end

        self.body = pm.Body(body_type=pm.Body.STATIC)
        self.shape = pm.Segment(self.body, Vec2d(*start), Vec2d(*end), 0)
        self.shape.friction = 1
        self.shape.collision_type = COLLTYPE_DEFAULT

    def draw(self):
#        pv1 = self.app.flipyv(self.body.position + self.shape.a.cpvrotate(self.body.rotation_vector))
#        pv2 = self.app.flipyv(self.body.position + self.shape.b.cpvrotate(self.body.rotation_vector))
        pv1 = self.body.position + self.shape.a.cpvrotate(self.body.rotation_vector)
        pv2 = self.body.position + self.shape.b.cpvrotate(self.body.rotation_vector)
        pv1 = self.app.jj(pv1)
        pv2 = self.app.jj(pv2)

        pygame.draw.lines(self.app.screen, (0,0,0), False, [pv1, pv2])

    def update(self):
        pass


