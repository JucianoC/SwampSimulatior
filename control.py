import sysvars
from components import *
from threading import Thread, Condition, Semaphore
import pygame

import time

class Control(object):
    def __init__(self, start_calories, frog_number, fly_number, sugar_number, interface = None):
        self.interface = interface
        self.start_calories = start_calories
        self.contadores = dict(
            frog = frog_number,
            fly  = fly_number,
            sugar = sugar_number
        )
        self.condition = Condition()
        self.sem_contadores = Semaphore()
        self.t_list = []
        self.agents = []

        self.matrix = [
                        [
                            Slot() for i in range(sysvars.MATRIX_SIZE)
                        ]
                        for i in range(sysvars.MATRIX_SIZE)
        ]

        self.mtx_sem = Semaphore()
        self.t_sem = Semaphore()
        self.agents_sem = Semaphore()
        self.agents_sem.release()

        self.sugar_generator_ready = Event()
        self.sugar_generator_ready.clear()
        self.sugar_generator_end = False

    def push_threads(self, t):
        with self.t_sem:
            self.t_list.append(t)

    def get_agents(self):
        ret = None
        with self.agents_sem:
            ret = self.agents[:]
        return ret

    def push_agents(self, agent):
        with self.agents_sem:
            self.agents.append(agent)

    def pop_agents(self, agent):
        with self.agents_sem:
            self.agents.remove(agent)


    def push_matrix(self, instance, x, y):
        with self.matrix[x][y].semaphore:
            self.matrix[x][y].sprite_group.add(instance)

    def pop_matrix(self, instance, x, y):
        with self.matrix[x][y].semaphore:
            self.matrix[x][y].sprite_group.remove(instance)

    def exchange(self, instance, oldx, oldy, newx, newy):
        self.pop_matrix(instance, oldx, oldy)
        self.push_matrix(instance, newx, newy)

    def check_colisions(self):
        with self.mtx_sem:
            for i in range(sysvars.MATRIX_SIZE):
                for j in range(sysvars.MATRIX_SIZE):

                    sprites = self.matrix[i][j].get_sprites()

                    frogs   = [sprite for sprite in sprites if sprite.__class__ == Frog]
                    flys    = [sprite for sprite in sprites if sprite.__class__ == Fly]
                    sugars  = [sprite for sprite in sprites if sprite.__class__ == Sugar]


                    if frogs:
                        frog_alpha = frogs[0]
                        # frog_alpha.calories += len(flys)
                        for fly in flys:
                            frog_alpha.calories += fly.calories

                        if frog_alpha.calories > self.start_calories:
                            frog_alpha.calories = self.start_calories

                        if flys:
                            for fly in flys:
                                fly.die(self, self.interface)
                        continue

                    if flys:
                        fly_alpha = flys[0]
                        # fly_alpha.calories += len(sugars)
                        for sugar in sugars:
                            fly_alpha.calories += sugar.calories


                        if fly_alpha.calories > self.start_calories:
                            fly_alpha.calories = self.start_calories
                            self.set_agent(Fly, (i,j))

                        if sugars:
                            for sugar in sugars:
                                sugar.die(self, self.interface)
                        continue
        # time.sleep(5)

    def set_interface(self, interface):
        self.interface = interface

        for i in range(self.contadores['frog']):
            self.set_agent(Frog, control_cont = False)
        for i in range(self.contadores['fly']):
            self.set_agent(Fly, control_cont = False)
        for i in range(self.contadores['sugar']):
            self.set_agent(Sugar, control_cont = False)

    def avaliable(self, x, y):
        avaliable = []

        for i in range(-1, 2):
            if x+i < 0 or x+i > sysvars.MATRIX_SIZE -1:
                continue
            for j in range(-1, 2):
                if i == x and j == y:
                    continue
                if y+j < 0 or y+j > sysvars.MATRIX_SIZE -1:
                    continue
                if i == 0 and j == 0:
                    continue
                avaliable.append((x+i, y+j))

        return avaliable

    def count_op(self, classe, action):
        with self.sem_contadores:
            if classe == Fly:
                self.contadores['fly']   += action
            elif classe == Frog:
                self.contadores['frog']  += action
            else:
                self.contadores['sugar'] += action

    def set_agent(self, classe, position = None, control_cont = True):
        instance = None
        if classe == Sugar:
            instance = Sugar(self.start_calories)
        else:
            instance = classe(self.start_calories)

        self.interface.sprites_op(instance, classe, 1)
        self.interface.count_op(classe, 1)

        if control_cont:
            self.count_op(classe, 1)

        if position is None:
            position = instance.get_position(in_matrix = True)
        else:
            instance.set_position(position[0], position[1], in_matrix = True)

        self.push_agents(instance)

        self.push_matrix(instance, position[0], position[1])

        if classe != Sugar:
            t = Thread(target =  instance.get_alive, args=(self, self.interface))
            t.start()
            self.push_threads(t)

    def sugar_generator_function(self):
        while not self.sugar_generator_end:
            self.sugar_generator_ready.wait()
            self.set_agent(Sugar)
            self.sugar_generator_ready.clear()

    def start_sugar_generator(self):
        t = Thread(target = self.sugar_generator_function)
        t.start()
        self.push_threads(t)

    def finish_game(self):
        self.sugar_generator_end = True
        self.interface.end_game = True

        for agent in self.get_agents():
            agent.die(self, self.interface)


class Slot(object):
    def __init__(self):
        self.semaphore = Semaphore()
        self.sprite_group = pygame.sprite.Group()

    def get_sprites(self):
        with self.semaphore:
            return self.sprite_group.sprites()
