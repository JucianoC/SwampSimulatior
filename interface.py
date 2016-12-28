# -*- coding:utf-8 -*-
import pygame
import sysvars
import random

from datetime import datetime
from control import Control
from components import *
from threading import *


class Interface(object):
    def __init__(self):
        self.control   = None

        self.background = pygame.sprite.Group()
        self.buttons    = pygame.sprite.Group()
        self.frogs      = pygame.sprite.Group()
        self.flys       = pygame.sprite.Group()
        self.sugars     = pygame.sprite.Group()
        self.count_group = pygame.sprite.Group()

        self.sprites = [
            self.background, self.buttons, self.frogs, self.flys, self.sugars, self.count_group
        ]
        self.sem_sprites = Semaphore()

        self.labels = []

        self.screen = None

        self.time_count = None
        self.start_time = datetime.now()

        self.counts = dict(
            frog  = Count(
                value = 0,
                image = "empty_field_green.png",
                default_x = 26 * sysvars.SPRITE_SIZE,
                default_y = 1 * sysvars.SPRITE_SIZE
            ),
            fly = Count(
                value = 0,
                image = "empty_field_green.png",
                default_x = 26 * sysvars.SPRITE_SIZE,
                default_y = 2 * sysvars.SPRITE_SIZE
            ),
            sugar   = Count(
                value = 0,
                image = "empty_field_green.png",
                default_x = 26 * sysvars.SPRITE_SIZE,
                default_y = 3 * sysvars.SPRITE_SIZE
            ),
        )

        for value in self.counts.values():
            self.count_group.add(value)
            self.labels.append(value)

        self.end_game = False

    def set_control(self, control):
        self.control = control
        self.condition = control.condition
        self.condition.acquire()

    def sprites_op(self, instance, classe, action):
        with self.sem_sprites:
            sprite_group = None
            if classe == Fly:
                sprite_group = self.flys
            elif classe == Frog:
                sprite_group = self.frogs
            else:
                sprite_group = self.sugars

            if action < 0:
                sprite_group.remove(instance)
            else:
                sprite_group.add(instance)

    def count_op(self, classe, action):
        if classe == Fly:
            self.counts['fly'] += action
        elif classe == Frog:
            self.counts['frog'] += action
        else:
            self.counts['sugar'] += action

    def init_elements(self):
        self.background.add(Block('fundo.png'))
        self.background.add(Block('painel_lateral.png', default_x = 800))

        btn_frog = Button(
            image = 'button_frog.png',
            default_x = 27 * sysvars.SPRITE_SIZE,
            default_y = 1 * sysvars.SPRITE_SIZE,
            action = ((1,1), (0,1)),
            on_click = self.control.set_agent,
            on_click_args = [Frog],
        )
        self.buttons.add(btn_frog)

        btn_fly = Button(
            image = 'button_fly.png',
            default_x = 27 * sysvars.SPRITE_SIZE,
            default_y = 2 * sysvars.SPRITE_SIZE,
            action = ((1,1), (0,1)),
            on_click = self.control.set_agent,
            on_click_args = [Fly]
        )
        self.buttons.add(btn_fly)

        btn_sugar = Button(
            image = 'button_sugar.png',
            default_x = 27 * sysvars.SPRITE_SIZE,
            default_y = 3 * sysvars.SPRITE_SIZE,
            action = ((1,1), (0,1)),
            on_click = self.control.set_agent,
            on_click_args = [Sugar]
        )
        self.buttons.add(btn_sugar)

        btn_finish = Button(
            image = 'button_finish.png',
            default_x = 26 * sysvars.SPRITE_SIZE,
            default_y = 23 * sysvars.SPRITE_SIZE,
            action = ((0,2), (0,1)),
            on_click = self.control.finish_game,
            on_click_args = []
        )
        self.buttons.add(btn_finish)

        self.time_count = TextLabel(
            TextLabel.get_current_time(self.start_time),
            default_x = 26 * sysvars.SPRITE_SIZE,
            default_y = 22 * sysvars.SPRITE_SIZE
        )

        self.labels.append(self.time_count)

    def mouse_control(self, positon):
        for button in self.buttons:
            button.check(positon)

    def draw(self):
        with self.control.mtx_sem:
            self.screen.fill(sysvars.COLOR_BLACK)

            for group in self.sprites:
                group.draw(self.screen)

            self.time_count.reload(TextLabel.get_current_time(self.start_time))
            for label in self.labels:
                self.screen.blit(label.label, label.position)

    def start(self):
        pygame.init()
        pygame.display.set_caption(sysvars.TITLE_SCREEN)
        pygame.display.set_icon(pygame.image.load(sysvars.ICON))

        self.screen =  pygame.display.set_mode(sysvars.SCREEN_SIZE)

        self.init_elements()

        self.control.start_sugar_generator()

        self.end_game = False
        clock = pygame.time.Clock()


        for agent in self.control.get_agents():
            agent.calcula.set()
            agent.finish.clear()

        while not self.end_game:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.control.finish_game()


            pressed_buttons = pygame.mouse.get_pressed()
            if pressed_buttons[0]:
                self.mouse_control(pygame.mouse.get_pos())

            clock.tick(sysvars.FRAME_RATE)


            for agent in self.control.get_agents():
                agent.calcula.set()
                agent.finish.clear()


            for agent in self.control.get_agents():
                if agent.__class__ == Sugar:
                    continue

                agent.finish.wait(0.05)

            self.control.sugar_generator_ready.set()

            self.control.check_colisions()
            self.draw()

            pygame.display.flip()

        pygame.quit()
