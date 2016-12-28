import pygame
import sysvars
import random

from datetime import datetime
from threading import *
import time

pygame.font.init()

class TextLabel(object):
    def __init__(self, text, color = (0,0,0), default_x = 0, default_y = 0, font = "arialblack", font_size = 18):
        self.myfont = pygame.font.SysFont(font, font_size)
        self.label = self.myfont.render(text, 1, color)
        self.color = color
        self.font  = font
        self.font_size = font_size
        self.position = (default_x, default_y)

    def reload(self, text, reload_font = False):
        if reload_font is True:
            self.myfont = pygame.font.SysFont(self.font, self.font_size)
        self.label = self.myfont.render(text, 1, self.color)

    @classmethod
    def get_current_time(cls, start_time):
        total_seconds = (datetime.now() - start_time).total_seconds()
        hour = int(total_seconds // 3600)
        total_seconds -= hour * 3600
        minute = int(total_seconds // 60)
        total_seconds -= minute * 60
        second = int(total_seconds)
        return "%02d:%02d:%02d" % (hour, minute, second)

class Block(pygame.sprite.Sprite):
    def __init__(self, image, default_x = None, default_y = None):
        super(Block, self).__init__()
        self.image = pygame.image.load(sysvars.SPRITE_PATH.format(image))
        self.rect  = self.image.get_rect()
        if default_x is not None:
            self.rect.x = default_x
        if default_y is not None:
            self.rect.y = default_y

    def set_randon_position(self):
        self.rect.x = random.randrange(sysvars.MATRIX_SIZE) * sysvars.SPRITE_SIZE
        self.rect.y = random.randrange(sysvars.MATRIX_SIZE) * sysvars.SPRITE_SIZE

    def get_position(self, in_matrix = False):
        if in_matrix:
            return (self.rect.x // sysvars.SPRITE_SIZE, self.rect.y // sysvars.SPRITE_SIZE)
        return (self.rect.x, self.rect.y)

    def set_position(self, x, y, in_matrix = False):
        if not in_matrix:
            self.rect.x = x
            self.rect.y = y
        else:
            self.rect.x = x * sysvars.SPRITE_SIZE
            self.rect.y = y * sysvars.SPRITE_SIZE

class Agent(Block):
    def __init__(self, calories, image):
        super(Agent, self).__init__(image)
        self.calories = calories
        self.alive = True

        self.calcula = Event()
        # self.calcula.clear()
        self.calcula.set()

        self.finish  = Event()
        self.finish.set()

    def subtrai_caloria(self):
        self.calories -= 1
        if self.calories == 0:
            return False
        return True

    def die(self, control, interface):
        self.alive = False

        x, y = self.get_position(in_matrix = True)
        control.pop_matrix(self, x, y)
        interface.sprites_op(self, self.__class__, -1)
        interface.count_op(self.__class__, -1)
        control.count_op(self.__class__, -1)
        control.pop_agents(self)

        self.calcula.set()
        self.finish.set()


    def get_alive(self, control, interface):
        while self.alive:
            self.calcula.wait()

            if not self.alive:
                continue

            x, y = self.get_position(in_matrix = True)

            if not self.subtrai_caloria():
                self.die(control, interface)
                continue

            avaliable = control.avaliable(x, y)
            next_pos  = random.choice(avaliable)
            self.set_position(next_pos[0], next_pos[1], in_matrix = True)
            control.exchange(self, x, y, next_pos[0], next_pos[1])

            self.calcula.clear()
            self.finish.set()

class Fly(Agent):
    def __init__(self, calories):
        super(Fly, self).__init__(calories, "fly.png")
        self.set_randon_position()
        self.name = 'Fly'

class Frog(Agent):
    def __init__(self, calories):
        super(Frog, self).__init__(calories, "frog.png")
        self.set_randon_position()
        self.name = 'Frog'

class Sugar(Agent):
    def __init__(self, calories):
        super(Sugar, self).__init__(calories, "sugar.png")
        self.set_randon_position()
        self.name = 'Sugar'
        self.finish.set()

class Button(Block):
    def __init__(self, image, default_x = 0, default_y = 0, action = ((0,1), (0,1)), on_click = None, on_click_args = []):
        super(Button, self).__init__(image, default_x, default_y)
        self.action = dict(
            x = (
                default_x + (sysvars.SPRITE_SIZE * action[0][0]),
                (default_x + (sysvars.SPRITE_SIZE * action[0][0]))+ (sysvars.SPRITE_SIZE * action[0][1])
            ),
            y = (
                default_y + (sysvars.SPRITE_SIZE * action[1][0]),
                (default_y + (sysvars.SPRITE_SIZE * action[1][0]))+ (sysvars.SPRITE_SIZE * action[1][1])
            )
        )
        self.on_click = on_click
        self.on_click_args = on_click_args

    def inside(self, position = (0, 0)):
        if position[0] > self.action['x'][0] and position[0] < self.action['x'][1]:
            if position[1] > self.action['y'][0] and position[1] < self.action['y'][1]:
                return True
        return False

    def perform(self):
        if self.on_click is not None:
            return self.on_click(*self.on_click_args)
        return False

    def check(self, position = (0, 0)):
        if self.inside(position):
            return self.perform()
        return False

class Count(TextLabel, Block):
    def __init__(self, value, image, n_digest = 2, color = (0,150,0), default_x = 0, default_y = 0, font = "arialblack", font_size = 18):
        TextLabel.__init__(self, "%0{}d".format(n_digest) % value, color, default_x + 4, default_y + 4, font, font_size)
        Block.__init__(self, image, default_x, default_y)
        self.value = value
        self.n_digest = n_digest
        self.sem = Semaphore()

    def check_digest(self):
        if self.value > 99:
            self.n_digest = 3
        elif self.value > 999:
            self.n_digest = 4

    def __add__(self, value):
        with self.sem:
            self.value +=  value
            old_n_digest = self.n_digest
            self.check_digest()

            reload_font = False
            if old_n_digest != self.n_digest:
                self.font_size = int(self.font_size * 0.7)
                reload_font = True

            self.reload(("%0{}d".format(self.n_digest)) % self.value, reload_font = reload_font)
        return self

    def __sub__(self, value):
        with self.sem:
            self.value -=  value

            old_n_digest = self.n_digest
            self.check_digest()

            reload_font = False
            if old_n_digest != self.n_digest:
                self.font_size = int(self.font_size * 1.3)
                reload_font = True

            self.reload(("%0{}d".format(self.n_digest)) % self.value, reload_font = reload_font)
        return self
