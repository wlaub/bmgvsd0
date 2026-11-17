

import pygame
import pygame.mixer

import dsfxr

import objects

class AudioEvent:
    def __init__(self, sound = None, channel = None):
        self.channel = channel
        self.sound = sound

    def is_playing(self):
        return self.channel is not None and self.channel.get_sound() == self.sound


class AudioManager:
    def __init__(self, app, base_dir):
        self.app = app
        self.base_dir = base_dir
        self.sound_manager = dsfxr.SoundManager(base_dir)
        self.tracked_sounds = set()

    def play_sound(self, sound_name, volume=1, position=None, **play_kwargs):
        volume *= self.app.max_volume
        if sound_name is None: return
#        try:
#            sound_source = random.choice(self.sound_map[sound_name])
#        except KeyError as e:
#            print(f'failed to play sound {e}')
#            return
#        sound = pygame.mixer.Sound(sound_source)
        try:
            sound = self.sound_manager.get_sound(sound_name)
        except KeyError as e:
            print(f'failed to play sound {e}')
            return

        sound.set_volume(volume)
        channel = sound.play(**play_kwargs)
        event = AudioEvent(sound, channel)
        if channel is not None:
            if position is not None:
                l,r = self.get_2d_sound_panning(sound, position)
                channel.set_volume(l,r)
                self.tracked_sounds.add((channel, sound, position))
            else:
                channel.set_volume(1,1)
        return event

    def update(self):

        removals = set()
        for channel, sound, position in self.tracked_sounds:
            if channel.get_sound() != sound:
                removals.add((channel, sound, position))
                continue

            vols = self.get_2d_sound_panning(sound, position)
            if vols is not None:
                l,r = vols
                channel.set_volume(l,r)

        self.tracked_sounds -= removals

    def get_2d_sound_panning(self, sound, position):
        if isinstance(position, objects.Entity):
            position = position.position

        if (player := self.app.player) is None:
            return

        delta = position - player.get_slot_position('ears')
        dist = abs(delta)
        S = 14
        dx = (max(-S, min(S, max(0,delta.x-3)))/S+1) #0-2
        a = min(1,7/(max(0,dist-21)+7))
        r = a*min(1,dx)
        l = a*min(1,2-dx)
#            print(a,l,r)
        return l,r


