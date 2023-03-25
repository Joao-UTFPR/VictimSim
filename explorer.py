## EXPLORER AGENT
### @Author: Tacla, UTFPR
### It walks randomly in the environment looking for victims.

import sys
import os
import random
from abstract_agent import AbstractAgent
from physical_agent import PhysAgent
import traceback
from abc import ABC, abstractmethod


class Explorer(AbstractAgent):
    def __init__(self, env, config_file, resc):
        """ Construtor do agente random on-line
        @param env referencia o ambiente
        @config_file: the absolute path to the explorer's config file
        @param resc referencia o rescuer para poder acorda-lo
        """

        super().__init__(env, config_file)

        # Specific initialization for the rescuer
        self.resc = resc  # reference to the rescuer agent
        self.rtime = self.TLIM  # remaining time to explore
        self.current_position = (0, 0)
        self.visited_positions = [(0, 0)]
        self.walled_positions = []
        self.path_to_pase = []

        self.dfs_result = {}
        self.dfs_untried = {}
        self.dfs_unbacktracked = {}
        self.dfs_s = None
        self.dfs_a = None

        # self.possible_moves = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]

    def deliberate(self) -> bool:
        """ The agent chooses the next action. The simulator calls this
        method at each cycle. Must be implemented in every agent"""

        # No more actions, time almost ended
        if self.rtime < 10.0:
            # time to wake up the rescuer
            # pass the walls and the victims (here, they're empty)
            print(f"{self.NAME} I believe I've remaining time of {self.rtime:.1f}")
            self.resc.go_save_victims([], [])
            return False

        # if self.rtime>25:
        #     self.path_to_pase = self.plan_path_to_base()

        next_position, dx, dy = self.get_next_pos_rand()

        # Moves the body to another position

        result = self.body.walk(dx, dy) ## noqa
        if result != PhysAgent.BUMPED:
            self.current_position = next_position
            self.visited_positions.append(self.current_position)
        # print(self.visited_positions)

        # Update remaining time
        if dx != 0 and dy != 0:
            self.rtime -= self.COST_DIAG
        else:
            self.rtime -= self.COST_LINE

        # Test the result of the walk action
        if result == PhysAgent.BUMPED:
            walls = 1  # build the map- to do
            self.walled_positions.append(next_position)
            # print(self.name() + ": wall or grid limit reached")

        if result == PhysAgent.EXECUTED:
            # check for victim returns -1 if there is no victim or the sequential
            # the sequential number of a found victim
            seq = self.body.check_for_victim()
            if seq >= 0:
                vs = self.body.read_vital_signals(seq)
                self.rtime -= self.COST_READ
                # print("exp: read vital signals of " + str(seq))
                # print(vs)

        return True

    def get_next_pos_rand(self):
        possible_moves = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]
        already_tried_moves = []

        if self.rtime<20:
            print("voltando")
            dx, dy = self.plan_path_to_base()
            next_position = (self.current_position[0] + dx, self.current_position[1] + dy)
            return next_position, dx, dy

        next_position = self.current_position
        while next_position in self.visited_positions or next_position in self.walled_positions:
            dx = random.choice([-1, 0, 1])
            if dx == 0:
                dy = random.choice([-1, 1])
            else:
                dy = random.choice([-1, 0, 1])
            next_position = (self.current_position[0] + dx, self.current_position[1] + dy)
            already_tried_moves.append((dx,dy))
            if set(already_tried_moves) == set(possible_moves):
                print("desistiu")
                return next_position, dx, dy
        return next_position, dx, dy

    def plan_path_to_base(self):
        posx = self.current_position[0]
        posy = self.current_position[1]
        dx = int(-1*posx/abs(posx)) if posx != 0 else 0
        dy = int(-1*posy/abs(posy)) if posy != 0 else 0

        if (posx+dx, posy+dy) in self.walled_positions:
            dx = random.choice([-1, 0, 1])
            if dx == 0:
                dy = random.choice([-1, 1])
            else:
                dy = random.choice([-1, 0, 1])


        return dx, dy
        # return path_to_base

    def dfs_search_action(self, target_state):
        for action, result in self.dfs_result[self.current_position]:
            if result == target_state:
                return action

    def get_next_pos_dfs_online(self):
        possible_moves = [(0, -1), (1, 0), (0, 1), (-1, 0), (-1, -1), (-1, 1), (1, 1), (1, -1)]
        # possible_moves.reverse()
        if self.current_position not in self.dfs_untried:
            self.dfs_untried[self.current_position] = possible_moves
        if self.dfs_s is not None:
            ind = 1
            if self.dfs_s not in self.dfs_result.keys():
                self.dfs_result[self.dfs_s] = [(self.dfs_a, self.current_position)]
            else:
                if (self.dfs_a, self.current_position) not in self.dfs_result[self.dfs_s]:
                    self.dfs_result[self.dfs_s].append((self.dfs_a, self.current_position))
                    ind = 0
            if self.dfs_s != self.current_position and ind == 0:
                if self.current_position not in self.dfs_unbacktracked.keys():
                    self.dfs_unbacktracked[self.current_position] = [self.dfs_s]
                else:
                    self.dfs_unbacktracked[self.current_position].append(self.dfs_s)

        if len(self.dfs_untried[self.current_position]) == 0:
            if len(self.dfs_unbacktracked[self.current_position]) == 0:
                self.dfs_s = self.current_position
                print("cabo")
                return self.current_position, 0, 0
            else:
                expected_state = self.dfs_unbacktracked[self.current_position].pop()
                self.dfs_a = self.dfs_search_action(expected_state)
        else:
            self.dfs_a = self.dfs_untried[self.current_position].pop()

        next_position = (self.current_position[0] + self.dfs_a[0], self.current_position[1] + self.dfs_a[1])
        self.dfs_s = self.current_position
        return next_position, self.dfs_a[0], self.dfs_a[1]



