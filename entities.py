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

ZBLN_COLLIDE=0b011

@register
class Zippy(BallEnemy):
    """
    its eyes remain perpetually closed in a deep slumber, but if it gets
    enough beans it might wake up and open its eyes
    """

    #TODO: different remnant?

    track_as = {'Enemy'}
    def __init__(self, app, pos):
        super().__init__(app, pos, 3, 32*32/1.8, 3, 1200)
        self.direction = Vec2d(0,0)
        self.going = False
        self.cooldown = self.app.engine_time
        self.can_stop = False
        self.beans = 0

        self.sprites = self.app.get_images('zippy')

    def on_remove(self):
        self.app.spawn_entity('Remnant', self.position, 'zippy', 'die', layer=-100)

    def draw_sprite(self):
        p = self.app.jj(self.position)
        if self.damage_taken == 0:
            sprite = self.sprites[f'zippy0']
        else:
            sprite = self.sprites[f'zippy_hurt0']

        w,h = sprite.get_size()
        self.app.screen.blit(sprite, p-Vec2d(w/2,h/2))

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

        self.sprites = self.app.get_images('zippy')

    #TODO drop pupil as NormlEyesPckp

    def on_remove(self):
        self.app.spawn_entity('Remnant', self.position, 'zippy', 'die', layer=-100)

    def draw_sprite(self):
        p = self.app.jj(self.position)
        if self.damage_taken == 0:
            sprite = self.sprites[f'zeeky0']
        else:
            sprite = self.sprites[f'zeeky_hurt0']

        w,h = sprite.get_size()
        self.app.screen.blit(sprite, p-Vec2d(w/2,h/2))


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
    #TODO draw sprites
    #TODO ball remnants for conversion to zbln
    #TODO take damage? show damage?

    track_as = {'Enemy'}
    def __init__(self, app, body_map):
        super(BallEnemy,self).__init__(app)

        self.health = 16
        self.last_hit = -10

#        self.base_speed = 25
        self.base_friction = -0.1
        self.base_speed = 50
        self.base_friction = -0.2

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

        self.m = m = total_mass*10*7

        self.body = body = pm.Body(m, moment=math.inf)
        body.position = Vec2d(*center)
        body.velocity = avg_vel
        self.app.space.add(body)

        self.camera_body = pm.Body(body_type=pymunk.Body.KINEMATIC)
        self.camera_body.position = self.app.camera.reference_position
        self.app.space.add(self.camera_body)

        self.joints = []
        for body in body_map.keys():
            c = self.get_joints(body, self.body)
            self.joints.extend(c)

        self.shapes = []
        for body, shapes in self.body_map.items():
            self.shapes.extend(shapes)
            for shape in shapes:
                shape.filter=pm.ShapeFilter(categories=ZBLN_COLLIDE)
                shape.collision_type=ZBLN_COLLIDE

        self.speed = self.base_speed*self.m
        self.friction = self.base_friction*self.m

        self.get_position()
        self.last_hit_velocity = Vec2d(0,0)

        self.spawn_interval = 5
        self.next_spawn = self.app.engine_time+self.spawn_interval

        self.merge_interval = 0.05
        self.next_merge = self.app.engine_time#+self.merge_interval

        self.angular_speed = 0
        self.affinity = 0

        self.sprites = self.app.get_images('zippy')

        self.app.space.on_collision(0,ZBLN_COLLIDE,post_solve=self.post_solve)
        self.absorb_targets = []

    def post_solve(self, arbiter, space, data):
        if not arbiter.is_first_contact:
            return

        if self.app.engine_time < self.next_merge:
            return





        imp = arbiter.total_impulse.length_squared
        print(f'>{imp:04.2g}, {arbiter.total_ke:04.2g}')

        # imp >1.5e6, 3.5e6, 2.9e6
        # imp <1.6e7, 4.2e6,

        # ke > 1.1e5, 1.6e5, 2.9e5
        # ke < 1.1e6, 4.5e6, 4.2e5

        if arbiter.total_ke > 4e5:
            self.absorb_targets.append(arbiter.bodies)

            other_body = arbiter.bodies[0]
            self.last_hit_body = arbiter.bodies[1]

            for entity in self.app.tracker['TrueBalls']:
                if entity.body is other_body:
                    self.absorb(entity)
                    self.app.pause()
                    break
            else:
                print('not that')


#        if imp >

        pass



#    def on_remove(self):
#        self.app.spawn_entity('Remnant', self.position, 'zippy', 'die')

    def draw_sprite(self):
        for body, shapes in self.body_map.items():
            for shape in shapes:
                p = body.position + shape.offset.cpvrotate(body.rotation_vector)
                p = self.app.jj(p)

                sprite = self.sprites['zbln0']
                scale = shape.radius/4.5
                sprite = pygame.transform.scale_by(sprite, scale) #this is not the most ideal

                w,h = sprite.get_size()
                self.app.screen.blit(sprite, p-Vec2d(w/2,h/2))


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
        return self.body.position

    @property
    def velocity(self):
        return self.body.velocity

    def get_joints(self, a, b):
#        r = abs(a.position-b.position)
#        return pymunk.DampedSpring(a,b,(0,0),(0,0), r,2000000, 1000)
        return [
#                pymunk.PinJoint(a,b),
                pymunk.PinJoint(a,self.body),
#                pymunk.DampedSpring(a, self.camera_body,(0,0),(0,0), 0, 1000, 1000),
                ]

    def burst(self, position, force):
#        force *= 500
        force *= 100
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

        shape.filter=pm.ShapeFilter(categories=ZBLN_COLLIDE)
        shape.collision_type=ZBLN_COLLIDE

        self.burst(body.position, self.m*(1+len(self.body_map)/7))
        self.next_merge = self.app.engine_time+self.merge_interval


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
                    a = hit.normal.dot(body.velocity)
                    #print(a)
                    self.last_hit_velocity = body.velocity
                    self.last_hit_body = body
                    self.affinity = a
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
#        if not self.app.camera.contains(self.position, 2):
#            speed = self.speed*10

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
        self.absorb_targets = []

    def try_absorb_ball(self):
        if self.app.engine_time < self.next_merge:
            return

        return

#        self.next_merge = self.app.engine_time+self.merge_interval

#        self.affinity += self.velocity.length_squared
        current_affinity = self.affinity

#        if len(self.absorb_targets) > 0:
#            print('pausing')
#            self.app.pause()

        #or maybe you require some minimum total angular speed
        for other in self.app.tracker['TrueBalls']:
            try:
                self.try_hit(other.shape)
#                hit_speed = abs(self.last_hit_velocity)
#                print(hit_speed)
#                if hit_speed > 300:
#                print(current_affinity)
#                if current_affinity > 100000:
                print(self.affinity, current_affinity)
                if self.affinity < -75:
                #TODO maybe require some relative speed thresold so it has to hit hard enough to stick
                    self.absorb(other)
                    print('absorb')
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

        self.gravitate_bodies()

        self.spin(player)


#        if False and len(self.body_map) < 7:
#            self.seek_player(player.position)
#        else:
#            self.seek_player(self.app.camera.reference_position)

#        self.apply_friction(player)

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

        p = self.body.position
        p = self.app.jj(p)
        pygame.draw.circle(self.app.screen, (0,255,0), p, 2)

    def gravitate_bodies(self):
        total_force = Vec2d(0,0)
        total_mass = 0
        for body in self.body_map.keys():
            total_mass += body.mass
            delta = self.camera_body.position - body.position
            dist = abs(delta)+20
#            if dist > 0:
            dir_ = delta/dist
#            g = 10*100000*body.mass*dir_/(dist*dist)
#            g = 10*10000*body.mass*dir_/(dist)
            g = 10*10000*body.mass*dir_/(dist)

            total_force += g
#            body.apply_force_at_local_point(g)



        delta = self.camera_body.position - self.body.position
        dist = abs(delta)+20
        dir_ = delta/dist

#        mass = self.body.mass
        mass = 70*total_mass+self.body.mass
        g = mass*dir_*(abs(self.angular_speed)**0.5)*.2
#        print(f'{abs(g):02.4g} {self.speed:02.4g} {abs(self.angular_speed):02.4g}')
#        g *= self.body.mass
        self.body.apply_force_at_local_point(g)

        friction = -10*self.body.velocity*self.body.mass/(dist-18)
        self.body.apply_force_at_local_point(friction)

        l,r,u,d = self.app.camera.lrud
        x,y = self.body.position

        if x < l or x > r or y < u or y > d:
            self.body.position = Vec2d(
                max(min(x, r),l),
                max(min(y, d),u),
                )
            self.body.velocity = Vec2d(0,0)

        #TODO !!!!!!!!!!!!!!!!!!!1 xa
        #TODO okay so i think what you're gonna need to do is put walls around the border of the camera that only this can hit
        #or maybe even just clamp the main body inside the camera area that seems easier
        # also maybe individual healths?


    def get_average_velocity(self):
        avg_vel = Vec2d(0,0)
        for body in self.body_map.keys():
            avg_vel += body.velocity
        avg_vel /= len(self.body_map.keys())
        return avg_vel

    def get_angular_speed(self, avg_vel):
        avg_vel = self.get_average_velocity()

        ang = 0
        for body in self.body_map.keys():
            bvel = body.velocity - avg_vel
            rpos = body.position-self.position
            tan = Vec2d(-rpos.y, rpos.x)

            aspeed = bvel.dot(tan)/tan.length_squared

            dist = abs(rpos)
            aspeed *= dist*body.mass

            ang+=aspeed

#        ang /= len(self.body_map)
        a = 0.01
        self.angular_speed = ang*(a) + self.angular_speed*(1-a)
#        print(self.angular_speed)
        return ang

    def spin(self, player):

        avg_vel = self.get_average_velocity()

        self.get_angular_speed(avg_vel)

        ang = self.angular_speed

        for body in self.body_map.keys():
            bvel = body.velocity - avg_vel
            rpos = body.position-self.position

            if ang > 0:
                tan = Vec2d(-rpos.y, rpos.x)
            else:
                tan = Vec2d(rpos.y, -rpos.x)

            #tangent force around center body
            error = tan*bvel.dot(tan)/abs(tan)#.length_squared
#            error*=0.15
            body.apply_force_at_local_point(error)


            #inward force toward center body
#            bvel dot rpos / abs(rpos)
            error -= rpos*bvel.dot(rpos)/rpos.length_squared
#            body.apply_force_at_local_point(error*body.mass/10)

#            friction = body.velocity*(-self.friction/20)

            #inward force toward camera
#            delta = self.app.camera.reference_position - body.position

            #scaling inward force toward center body
#            delta = self.position-body.position
#            delta *= body.mass*self.angular_speed
#                print(f'{delta=} {friction=}')
#            friction = delta

#            body.apply_force_at_local_point(friction)


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
        avg_speed = abs(self.angular_speed)
        thresh = 7e4
        if avg_speed > thresh:
            wind_force = (avg_speed-thresh)*.4 #TODO still tune this xb
            print(avg_speed, wind_force)
            targets = self.app.tracker['Enemy']

            self.app.forget_range = min(max(1,2-avg_speed/100e4), self.app.forget_range)

            if len(targets) <= 1:
                print('!!!!!!!!!!!!!!')
                self.app.space.remove(*self.joints)
                self.joints = []
                self.app.pause()
            for entity in targets:
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
#            body.apply_force_at_local_point(delta*wind_force)



        #TODO: when max velocity exceeds threshold, become camera pickup
        #TODO: or just duration withing range of center?
        #TODO: different pickups based on topology?
        #TODO: different zoom level based on topology?



class TrueBalls(BallEnemy):
    def spawn_remnant(self):
        scale = self.r/4.5
        draw_args = {
            'scale': scale,
            'flip_x': self.facing.x>0,
            }
        self.app.spawn_entity('Remnant', self.position-scale*Vec2d(0,3), 'ball', 'die', draw_args,layer =-100)

    def _draw_sprite(self, sprite, p):
        scale = self.r/4.5
        sprite = pygame.transform.scale_by(sprite, scale) #this is not the most ideal
        if self.facing.x > 0:
            sprite = pygame.transform.flip(sprite, True, False)

        w,h = sprite.get_size()
        self.app.screen.blit(sprite, p - scale*Vec2d(16, 11))


@register
class Ball(TrueBalls):
    track_as = {'Enemy'}

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
        self.spawn_remnant()

    def draw_sprite(self):
        p = self.app.jj(self.position)
        if self.damage_taken == 0:
            sprite = self.sprites[f'ball0']
        else:
            sprite = self.sprites['ball_hurt0']

        self._draw_sprite(sprite, p)


@register
class FgtflBall(TrueBalls):
    track_as = {'Enemy'}

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

        self.sprites = self.app.get_images('ball')

    def on_remove(self):
        self.spawn_remnant()

    def draw_sprite(self):
        p = self.app.jj(self.position)
        if self.damage_taken == 0:
            if self._going:
                sprite = self.sprites[f'ball0']
            else:
                sprite = self.sprites['ball_4got0']
        else:
            if self._going:
                sprite = self.sprites['ball_hurt0']
            else:
                sprite = self.sprites['ball_4got_hurt0']

        self._draw_sprite(sprite, p)

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
class LstflBall(TrueBalls):
    track_as = {'Enemy'}

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

        self.sprites = self.app.get_images('ball')

    def on_remove(self):
        self.spawn_remnant()

    def draw_sprite(self):
        p = self.app.jj(self.position)
        if self.damage_taken == 0:
            sprite = self.sprites[f'ball0']
        else:
            sprite = self.sprites['ball_hurt0']

        self._draw_sprite(sprite, p)



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


