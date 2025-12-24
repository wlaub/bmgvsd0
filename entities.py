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

"""
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
            for bean in beans[6-self.beans:]:
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

            if not self.can_stop and not self.app.camera.contains(self.position, 100):
                self.say('wtf where am i')
                self.can_stop = True

            if self.can_stop and not self.app.camera.contains(self.position, 50):
                self.say('stopping')
                self.going = False
                self.cooldown = self.app.engine_time+5/(1+self.beans)
                self.friction = -100*self.m

        self.apply_friction(player)

    def get_drops(self):
        result = []
        if random.random() < 0.1 and  len(self.app.tracker['BrewPotPckp']) == 0:
           result.append(self.app.create_entity('BrewPotPckp', Vec2d(0,0)))

        result.append(self.app.create_entity('BeanPickup', Vec2d(0,0)))
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
                    Vec2d(r*math.cos(aa)+dx, r*math.sin(aa)+dy)
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

        first_time = False
        if self.target is None:
            first_time = True
            self.target = player
            self.target_position = self.target.position

        if not self.going:
            self.say('going')
            self.going = True
            self.can_stop = False
            if not first_time:
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
                    bean.try_hit(self.shape)
                    if isinstance(bean, Zeeky):
                        self.say('blessed union')
                        #this is why body management needs unfucked
                        self.app.remove_entity(bean, preserve_physics = True)
                        self.app.remove_entity(self, preserve_physics = True)
                        if self.app.flags.geta('_zbln', False):
                            body_map = {
                                bean.body: (bean.shape,),
                                self.body: (self.shape,),
                                }
                            self.app.spawn_entity('Zbln', body_map)
                        else:
                            raise NotImplementedError('it is not ready yet')
                        return
                    else:
                        bean.absorb(self)
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


@register
class Zbln(BallEnemy):
    track_as = {'Enemy'}
    def __init__(self, app, body_map):
        super(BallEnemy,self).__init__(app)

        self.health = 16
        self.last_hit = -10

        self.base_speed = 25
        self.base_friction = -0.1

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

        self.body_map = body_map

        center = Vec2d(0,0)
        avg_vel = Vec2d(0,0)
        total_mass = 0
        for body in body_map.keys():
            center += body.position
            avg_vel += body.velocity
            total_mass += body.mass
        center /= len(body_map)

        self.m = m = total_mass*10

        self.body = body = pm.Body(m, moment=math.inf)
        body.position = Vec2d(*center)
        body.velocity = avg_vel
        self.app.space.add(body)

        self.camera_body = pm.Body(body_type=pymunk.Body.KINEMATIC)
        self.camera_body.position = self.app.camera.reference_position
        self.app.space.add(self.camera_body)

        self.joints = []
        for body in body_map.keys():
            c = self.get_joints(self.body, body)
            self.joints.extend(c)

        self.shapes = []
        for body, shapes in self.body_map.items():
            self.shapes.extend(shapes)

        self.speed = self.base_speed*self.m
        self.friction = self.base_friction*self.m

        self.get_position()
        self.last_hit_velocity = Vec2d(0,0)

        self.spawn_interval = 5
        self.next_spawn = self.app.engine_time+self.spawn_interval

        self.merge_interval = 0.1
        self.next_merge = self.app.engine_time#+self.merge_interval

    def add_to_space(self, space):
#        for body, shapes in self.body_map.items():
#            space.add(body, *shapes)

        for c in self.joints:
            space.add(c)

        self.burst(self.body.position, self.m)

    def remove_from_space(self, space):
        for body, shapes in self.body_map.items():
            space.remove(body, *shapes)
        space.remove(self.body)
        space.remove(self.camera_body)

    def get_position(self):
        self.my_position = self.body.position
        return

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
        return self.body.velocity

    def get_joints(self, a, b):
#        r = abs(a.position-b.position)
#        return pymunk.DampedSpring(a,b,(0,0),(0,0), r,2000000, 1000)
        return [
                pymunk.PinJoint(a,b),
#                pymunk.DampedSpring(a, self.camera_body,(0,0),(0,0), 0, 1000, 1000),
                ]

    def burst(self, position, force):
        force *= 500
        for entity in self.app.tracker['TrueBalls']:
            delta = entity.position-position
            delta /= (4+delta.length_squared)
            entity.body.apply_force_at_local_point(force*delta)
        #TODO also push back player
        #TODO maybe it's based on center of mass and has a radius?
        #TODO maybe it's based on speed of collision

    def absorb(self, other):
        self.app.remove_entity(other, preserve_physics = True)
        body, shape = other.body, other.shape
        self.body_map[body] = (shape,)
        c = self.get_joints(body, self.last_hit_body)
#        c = self.get_joint(body, self.body)
        self.joints.extend(c)
        self.app.space.add(*c)

        self.burst(body.position, self.m*(1+len(self.body_map)/7))

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
                    self.last_hit_velocity = body.velocity
                    self.last_hit_body = body
                    break
                except AssertionError: pass
            else: continue
            break #i take it back this is the worst thing i have ever done
        else:
            raise AssertionError #This is the worst thing i have ever done

    def seek_player(self, player_position):
        delta = player_position-self.position
        delta /= abs(delta)

        speed = self.speed
        if not self.app.camera.contains(self.position, 2):
            speed = self.speed*10

        self.body.apply_force_at_local_point(delta*speed)

    def apply_friction(self, player):
        vel = Vec2d(0,0)
        for body in self.body_map.keys():
            vel+= body.velocity
        vel/=len(self.body_map)

        friction = vel*self.friction

        self.body.apply_force_at_local_point(friction)

    def update(self):
        self.get_position()
        self.normal_update()

    def try_absorb_ball(self):
        if self.app.engine_time < self.next_merge:
            return

        #or maybe you require some minimum total angular speed

        for other in self.app.tracker['TrueBalls']:
            try:
                self.try_hit(other.shape)
                #TODO maybe require some relative speed thresold so it has to hit hard enough to stick
                self.absorb(other)
                self.say('blessed union')
                self.next_merge = self.app.engine_time+self.merge_interval
                return
            except AssertionError: pass



    def normal_update(self):
        player = self.app.player
        if player is None: return
        self.hit_player(player)

        self.try_absorb_ball()

        #TODO
#        a = (len(self.body_map)/7 + 0.75)/2
#        ia = 1-a
#        target_position = player.position*ia + self.app.camera.reference_position*a
        target_position = player.position
        self.seek_player(target_position)

        for body in self.body_map.keys():
            delta = self.camera_body.position - body.position
            dist = abs(delta)
            if dist > 0:
                dir_ = delta/dist
                g = 1*100000*body.mass*dir_/delta.length_squared
                body.apply_force_at_local_point(g)




#        if False and len(self.body_map) < 7:
#            self.seek_player(player.position)
#        else:
#            self.seek_player(self.app.camera.reference_position)

        self.apply_friction(player)

#        if len(self.body_map) >= 7:
#            self.spin(player)

        if self.app.engine_time >= self.next_spawn and False: #TODO
            self.next_spawn += self.spawn_interval

            if len(self.app.tracker['Zeeky']) + len(self.body_map) < 7:
                delta = player.position-self.position
                delta /= (abs(delta)/20)

                entity = self.app.spawn_entity('Zeeky', self.position+delta)

    def draw(self):
        for body, shapes in self.body_map.items():
            for shape in shapes:
                p = body.position + shape.offset.cpvrotate(body.rotation_vector)
                p = self.app.jj(p)

                color = (0,0,255)
                if self.app.engine_time-self.last_hit < 0.08:
                    color = (255,0,0)

                pygame.draw.circle(self.app.screen, color, p, int(shape.radius), 2)

    def spin(self, player):

        avg_vel = Vec2d(0,0)
        for body in self.body_map.keys():
            avg_vel += body.velocity
        avg_vel /= len(self.body_map.keys())

        ang = 0
        for body in self.body_map.keys():
            bvel = body.velocity - avg_vel
            rpos = body.position-self.position
            tan = Vec2d(-rpos.y, rpos.x)

            aspeed = bvel.dot(tan)/tan.length_squared

            ang+=aspeed

        print(ang)

        avg_speed = 0
        for body in self.body_map.keys():
            bvel = body.velocity - avg_vel
            rpos = body.position-self.position

            if ang > 0:
                tan = Vec2d(-rpos.y, rpos.x)
            else:
                tan = Vec2d(rpos.y, -rpos.x)

            error = tan*bvel.dot(tan)/abs(tan)#.length_squared
            error*=0.15

#            bvel dot rpos / abs(rpos)
            error -= rpos*bvel.dot(rpos)/rpos.length_squared
#            body.apply_force_at_local_point(error*body.mass/10)

#            friction = body.velocity*(-self.friction/20)
#            avg_speed+=abs(body.velocity)

            delta = self.app.camera.reference_position - body.position
            delta = self.position-body.position
            delta *= body.mass*200
#                print(f'{delta=} {friction=}')
            friction = delta

            body.apply_force_at_local_point(friction)

        avg_speed/=len(self.body_map)

        """
        maybe what happens is you break all the links but you also like
        push the player away when it happens to prevent foot collisions
        apply a backward velocity on the player's feet that scales as you get closer to the thing
        can you just put a big ring around it that keeps everything inside?
        can you put like slide join constraints between the balls and the center?
        maybe make the center a kinematic object that seeks the camera
        """

        #TODO don't give zeeky boost to spawning zippy if zbl'n
        #TODO apply outward wind at max size
        #TODO sometimes it doesn't really start spinning?
#            wind_force = self.speed/10
        avg_speed = abs(ang)
        if avg_speed > 100:
            wind_force = avg_speed*100
            print(avg_speed, wind_force)
            for entity in self.app.tracker['Enemy']:
                if entity is self: continue
                try:
                    body = entity.body
                    delta = body.position - self.position
                    delta /= abs(delta)
                    body.apply_force_at_local_point(delta*wind_force)

                except Exception as e:
                    print(e)

            body = player.body
            delta = body.position - self.position
            delta /= abs(delta)
            body.apply_force_at_local_point(delta*wind_force)



        #TODO: when max velocity exceeds threshold, become camera pickup
        #TODO: or just duration withing range of center?
        #TODO: different pickups based on topology?
        #TODO: different zoom level based on topology?



class BallState(enum.Enum):
    NORML = 0
    FGTFL = 1
    LSTFL = 2

@register
class Ball(BallEnemy):
    track_as = {'Enemy', 'TrueBalls'}

    def __init__(self, app, pos, r = None, m = None, h = None):
        if r is None:
            r= 4+4*random.random()
            m = r*r/1.8
            h = r/4
        super().__init__(app, pos, r, m, h)
        self.update = self.normal_update
        self.drops = self.basic_ball_drops()

        self.sprites = self.app.get_images('ball')


    def on_remove(self):
        scale = self.r/4.5
        draw_args = {
            'scale': scale,
            'flip_x': self.facing.x>0,
            }
        self.app.spawn_entity('Remnant', self.position-scale*Vec2d(0,3), 'ball', 'die', draw_args)

    def draw_sprite(self):
        p = self.app.jj(self.position)
        if self.damage_taken == 0:
            sprite = self.sprites[f'ball0']
        else:
            sprite = self.sprites['ball_hurt0']

        scale = self.r/4.5
        sprite = pygame.transform.scale_by(sprite, scale) #this is not the most ideal
        if self.facing.x > 0:
            sprite = pygame.transform.flip(sprite, True, False)

        w,h = sprite.get_size()
        self.app.screen.blit(sprite, p - scale*Vec2d(8, 11))



@register
class FgtflBall(BallEnemy):
    track_as = {'Enemy', 'TrueBalls'}

    def __init__(self, app, pos, r = None, m = None, h = None):
        if r is None:
            r= 4+4*random.random()
            m = r*r/1.8
            h = r/4
        super().__init__(app, pos, r, m, h)
        self.last_aggro = 0
        self._going = True

        if random.random() > 0.5:
            self.drops = self.basic_ball_drops()

    def update(self):
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
                    self.app.remove_entity(self)
                    self.app.spawn_entity('LstflBall', self.position, self.r, self.m, 1)
#                    self.set_state(BallState.LSTFL)
                    break
                except AssertionError: pass

        if not self._going and dt > 15:
            if r < 80:
                self.last_aggro = self.app.engine_time
                self._going = True

        if self._going:
            self.seek_player(player)

        self.apply_friction(player)


@register
class LstflBall(BallEnemy):
    track_as = {'Enemy', 'TrueBalls'}

    def __init__(self, app, pos, r = None, m = None, h = None):
        if r is None:
            r= 4+4*random.random()
            m = r*r/1.8
            h = r/4
        super().__init__(app, pos, r, m, h)
        self.last_aggro = 0
        self._going = True
        self.lores = 0
        self.drops = self.basic_ball_drops()
        self.target = self.app.player

    def update(self):
        player = self.app.player
        if player is None: return

        lores = self.app.tracker['LoreOrePickup']

        if self.target != player and not self.target in lores:
            self.target = player
        elif self.target == player:
            dist = 1000000
            for lore in lores:
                r = self.position.get_dist_sqrd(lore.position)
                if r < dist:
                    dist = r
                    self.target = lore

        self.hit_player(player)
        if self.target != player:
            try:
                hit = self.shape.shapes_collide(self.target.shape)
                self.lores+= 1
                self.app.remove_entity(self.target)
                self.target = player
            except AssertionError: pass

        self.seek_player(self.target)

        self.apply_friction(player)

    def get_drops(self):
        if self.lores > 0:
            return [self.app.create_entity('LengthPickup', Vec2d(0,0))]
        else:
            return self.drops


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


