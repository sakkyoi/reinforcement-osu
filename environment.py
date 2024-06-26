import numpy as np
import gym
from gym import spaces
from util.OSUInjector import OSUInjector
import sys
import pyautogui
from pyclick import HumanClicker, HumanCurve

from time import sleep
import cv2

from datetime import datetime, timedelta
import threading

class ENV(gym.Env):
    def __init__(self, osu_path="./osu!/osu!.exe", no_fail: bool = False, auto_pilot: bool = False, relax: bool = False, action_space_type = "discrete", frame_limit: int = 10):
        super(ENV, self).__init__()
        self.frame_limit = frame_limit
        self.action_space_type = action_space_type
        self.no_fail = no_fail
        self.auto_pilot = auto_pilot
        self.relax = relax
        self.injector = OSUInjector(osu_path=osu_path, no_fail=self.no_fail, auto_pilot=self.auto_pilot, relax=self.relax)
        self.discrete_width = self.injector._screen_shot().shape[0]
        self.discrete_height = self.injector._screen_shot().shape[1]
        self.hwnd_width, self.hwnd_height = self.injector._get_hwnd_size()
        self.hwnd_top, self.hwnd_left = self.injector._get_hwnd_pos()

        self.observation_space = spaces.Box(low=0, high=1, shape=(4, self.discrete_width, self.discrete_height), dtype=np.float32)

        if self.auto_pilot:
            if self.action_space_type == "discrete":
                self.action_space = spaces.Discrete(4)
            elif self.action_space_type == 'multi_discrete':
                self.action_space = spaces.MultiDiscrete([2, 2])
            elif self.action_space_type == 'multi_binary':
                self.action_space = spaces.MultiBinary(2)
            else:
                raise ValueError("action_space must be either 'discrete' or 'multi_discrete'")
        elif self.relax:
            if self.action_space_type == 'multi_discrete':
                self.action_space = spaces.MultiDiscrete([self.discrete_width + 1, self.discrete_height + 1])
            elif self.action_space_type == 'box':
                self.action_space = spaces.Box(low=np.array([0, 0]), high=np.array([1, 1]), dtype=np.float32)
            else:
                raise ValueError("action_space must be 'multi_discrete'")
        
        
        self.reward_range = (-5, 5)

        self.fps = 0
        self.fps_counter = 0
        self.fps_counter_last_time = datetime.now()

        self.last_play_container = None
        self.started = False

        self.action_thread = None
        self.human_clicker = HumanClicker()

        self.obs = np.ndarray((4, self.discrete_width, self.discrete_height), dtype=np.float32)
        for i in range(4):
            self.obs[i] = self.injector._screen_shot()

        print(self.obs)

        self.last_action = None
        self.time_last_action = datetime.now()

        self.play_counter = 0
        self.traing_mode = 0

    def reset(self):
        self.injector._focus_on_osu()

        """
        If the game is in map selection screen, press F2 to randomize the map.
        If the game is in the result screen, press escape to go back to map selection screen and press F2 to randomize the map.
        If the game is failed, press ` to restart the map.
        (This is moved to step function)
        """
        print('\nreset')

        self.started = False

        observation = self.obs

        return observation

    def step(self, action):
        datetime.now()
        if self.time_last_action + timedelta(seconds=1/self.frame_limit) > datetime.now():
            while self.time_last_action + timedelta(seconds=0.1) > datetime.now():
                sleep(0.1)
        self.time_last_action = datetime.now()

        if not self.started:
            self.started = True
            if self.injector.get_osu_status() == 5:
                self.injector._random_map()
            elif self.injector.get_osu_status() == 7:
                self.injector._back_to_map_select()
                self.injector._random_map()
            elif self.last_play_container is not None and self.injector.get_osu_status() == 2: # i need to think about this: if the agent breaks while playing, it must restart the map.
                self.injector._restart_map()
            elif not self.no_fail and self.last_play_container is not None and self.injector.get_play_container()['player_hp'] == 0:
                self.injector._restart_map()

            self.injector.recaculate_offsets() # recaculate offsets

        last_play_container = self.injector.get_play_container()
        
        self._perform_action(action)
        for i in range(3):
            self.obs[i] = self.obs[i + 1]

        self.obs[-1] = self.injector._screen_shot()

        observation = self.obs

        play_container = self.injector.get_play_container()
        
        reward = 0

        if play_container is None and self.injector.get_osu_status() != 2:
            done = True
        # current training is with no fail, so this is not needed
        elif not self.no_fail and last_play_container is not None and play_container['player_hp'] < last_play_container['player_hp'] and play_container['player_hp'] == 0:
            done = True
            reward -= 10
        elif last_play_container is not None and play_container is not None:
            
            reward += (play_container['hit300'] - last_play_container['hit300']) * 5
            reward += (play_container['hit100'] - last_play_container['hit100']) * -1
            reward += (play_container['hit50'] - last_play_container['hit50']) * -3
            reward += (play_container['hitMiss'] - last_play_container['hitMiss']) * -5

            # punishment for doing nothing
            if (action == self.last_action).all():
                if reward < 0:
                    reward = -5
                elif reward != 0:
                    reward = reward * 0.5

            # punishment for indolence(pressing both keys at the same time), to avoid the agent keep pressing one of the keys
            if action[0] and action[1] and self.auto_pilot:
                reward = reward * 0.1

            self.last_action = action

            done = False
        else:
            done = False

        self.render(observation[-1])
        if datetime.now() - self.fps_counter_last_time > timedelta(seconds=1):
            self.fps = self.fps_counter
            self.fps_counter = 0
            self.fps_counter_last_time = datetime.now()
        else:
            self.fps_counter += 1
        sys.stdout.write(f'\r{self.last_play_container} {action} fps: {self.fps}                           ')
        sys.stdout.flush()

        if done:
            # log play_container to file
            if self.auto_pilot:
                log_path = 'log_hit/'
            elif self.relax:
                log_path = 'log_movement'
            else:
                log_path = 'log_unknown'
            if self.traing_mode == 0:
                with open(log_path + 'play_training.txt', 'a') as f:
                    f.write(str(self.play_counter) + "," + str(self.last_play_container) + "\n")
            elif self.traing_mode == 1:
                with open(log_path + 'play_evaluation.txt', 'a') as f:
                    f.write(str(self.play_counter) + "," + str(self.last_play_container) + "\n")
            elif self.traing_mode != -1:
                raise ValueError("traing_mode must be 0, 1 or -1")
            
            self.play_counter += 1

        self.last_play_container = last_play_container
            
        return observation, reward, done, {}
        
    def render(self, img, mode='human'):

        img = cv2.resize(img, (0, 0), fx=10, fy=10)

        cv2.imshow('capture', img)

        cv2.waitKey(1)
        
        return None

    def close(self):
        pyautogui.keyUp('q')
        pyautogui.keyUp('w')

    def _set_training_mode(self, mode):
        if mode == 0:
            self.traing_mode = 0
        elif mode == 1:
            self.traing_mode = 1
        elif mode == -1:
            self.traing_mode = -1
        else:
            raise ValueError("traing_mode must be 0, 1 or -1")
    
    def _action_thread(self, real_x, real_y, curve):
        self.human_clicker.move((real_x, real_y), 0.05, humanCurve=curve)
        return None

    def _perform_action(self, action):
        if self.auto_pilot:
            if self.action_space_type == "discrete":
                if action == 0:
                    pyautogui.keyUp('q')
                    pyautogui.keyUp('w')
                elif action == 1:
                    pyautogui.keyDown('q')
                    pyautogui.keyUp('w')
                elif action == 2:
                    pyautogui.keyUp('q')
                    pyautogui.keyDown('w')
                elif action == 3:
                    pyautogui.keyDown('q')
                    pyautogui.keyDown('w')
                else:
                    raise ValueError(f'Action {action} is not valid')
            elif self.action_space_type == "multi_discrete":
                click1 = action[0]
                click2 = action[1]
                if click1 == 0:
                    pyautogui.keyUp('q')
                else:
                    pyautogui.keyDown('q')

                if click2 == 0:
                    pyautogui.keyUp('w')
                else:
                    pyautogui.keyDown('w')
            elif self.action_space_type == "multi_binary":
                click1 = action[0]
                click2 = action[1]
                if not click1:
                    pyautogui.keyUp('q')
                else:
                    pyautogui.keyDown('q')

                if not click2:
                    pyautogui.keyUp('w')
                else:
                    pyautogui.keyDown('w')
        elif self.relax:
            if self.action_space_type == "multi_discrete":
                discrete_x = action[0]
                discrete_y = action[1]
                width, height = self.hwnd_width, self.hwnd_height
                top, left = self.hwnd_top, self.hwnd_left
                discrete_width_factor = (width - 50) / self.discrete_width
                discrete_height_factor = (height - 50 - 25) / self.discrete_height
                real_x = int(left + discrete_x * discrete_width_factor)
                real_y = int(top + discrete_y * discrete_height_factor)

                pyautogui.moveTo(real_x, real_y)
            elif self.action_space_type == 'box':
                discrete_x = action[0] * self.discrete_width
                discrete_y = action[1] * self.discrete_height
                width, height = self.hwnd_width, self.hwnd_height
                top, left = self.hwnd_top, self.hwnd_left
                discrete_width_factor = (width - 50) / self.discrete_width
                discrete_height_factor = (height - 50 - 25) / self.discrete_height
                real_x = int(left + discrete_x * discrete_width_factor)
                real_y = int(top + discrete_y * discrete_height_factor)

                pyautogui.moveTo(real_x, real_y)

if __name__ == "__main__":
    raise NotImplementedError("This file is not meant to be run")