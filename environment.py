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
    def __init__(self, osu_path="./osu!/osu!.exe", no_fail: bool = False, action_space_type = "discrete"):
        self.action_space_type = action_space_type
        self.no_fail = no_fail
        self.injector = OSUInjector(osu_path=osu_path, no_fail=self.no_fail)
        self.discrete_width = self.injector._screen_shot().shape[0]
        self.discrete_height = self.injector._screen_shot().shape[1]
        self.hwnd_top, self.hwnd_left = self.injector._get_hwnd_pos()

        self.observation_space = spaces.Box(low=0, high=1, shape=(1, self.discrete_width, self.discrete_height), dtype=np.float32)

        if self.action_space_type == "discrete":
            self.action_space = spaces.Discrete(self.discrete_width * self.discrete_height * 4)
        elif self.action_space_type == "box":
            self.action_space = spaces.Box(low=0, high=self.discrete_width * self.discrete_height * 4, shape=(1,), dtype=np.float32)
        else:
            raise ValueError("action_space must be either 'discrete' or 'box'")
        
        self.reward_range = (-5, 5)

        self.fps = 0
        self.fps_counter = 0
        self.fps_counter_last_time = datetime.now()

        self.last_play_container = None
        self.started = False

        self.action_thread = None
        self.human_clicker = HumanClicker()

    def reset(self):
        self.injector._focus_on_osu()

        """
        If the game is in map selection screen, press F2 to randomize the map.
        If the game is in the result screen, press escape to go back to map selection screen and press F2 to randomize the map.
        If the game is failed, press ` to restart the map.
        """
        print('\nreset')
        self.started = False

        # if self.injector.get_osu_status() == 5:
        #     self.injector._random_map()
        # elif self.injector.get_osu_status() == 7:
        #     self.injector._back_to_map_select()
        #     self.injector._random_map()
        # elif self.last_play_container is not None and self.injector.get_osu_status() == 2: # i need to think about this: if the agent breaks while playing, it must restart the map.
        #     self.injector._restart_map()
        # elif not self.no_fail and self.last_play_container is not None and self.injector.get_play_container()['player_hp'] == 0:
        #     self.injector._restart_map()
# 
        # self.last_play_container = self.injector.get_play_container()

        observation = self.injector._screen_shot()

        return observation

    def step(self, action):
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

            self.last_play_container = self.injector.get_play_container()

        self._perform_action(action)
        observation = self.injector._screen_shot()
        play_container = self.injector.get_play_container()
        
        reward = 0

        if play_container is None:
            done = True
        elif not self.no_fail and self.last_play_container is not None and play_container['player_hp'] < self.last_play_container['player_hp'] and play_container['player_hp'] == 0:
            done = True
            reward -= 5
        elif self.last_play_container is not None:
            reward += (play_container['hitGeki'] - self.last_play_container['hitGeki']) * 5
            reward += (play_container['hit300'] - self.last_play_container['hit300']) * 4
            reward += (play_container['hitKatsu'] - self.last_play_container['hitKatsu']) * 3
            reward += (play_container['hit100'] - self.last_play_container['hit100']) * 2
            reward += (play_container['hit50'] - self.last_play_container['hit50']) * 1
            reward += (play_container['hitMiss'] - self.last_play_container['hitMiss']) * -3

            done = False
        else:
            done = False

        self.last_play_container = play_container

        self.render(observation)
        if datetime.now() - self.fps_counter_last_time > timedelta(seconds=1):
            self.fps = self.fps_counter
            self.fps_counter = 0
            self.fps_counter_last_time = datetime.now()
        else:
            self.fps_counter += 1
        sys.stdout.write(f'\r{self.last_play_container} {action} fps: {self.fps}                           ')
        sys.stdout.flush()
            
        return observation, reward, done, {}
        
    def render(self, img, mode='human'):

        cv2.imshow('capture', img)

        cv2.waitKey(1)
        
        return None

    def close(self):
        pyautogui.keyUp('q')
        pyautogui.keyUp('w')
    
    def _action_thread(self, real_x, real_y, curve):
        self.human_clicker.move((real_x, real_y), 0.05, humanCurve=curve)
        return None

    def _perform_action(self, action):
        width, height = self.injector._get_hwnd_size()
        if self.action_space_type == "discrete":
            click, move = divmod(action, self.discrete_width * self.discrete_height)
            y, x = divmod(move, self.discrete_width)
            if click == 0:
                # pyautogui.mouseUp(button='left')
                # pyautogui.mouseUp(button='right')
                pyautogui.keyUp('q')
                pyautogui.keyUp('w')
            elif click == 1:
                # pyautogui.mouseDown(button='left')
                # pyautogui.mouseUp(button='right')
                pyautogui.keyDown('q')
                pyautogui.keyUp('w')
            elif click == 2:
                # pyautogui.mouseUp(button='left')
                # pyautogui.mouseDown(button='right')
                pyautogui.keyUp('q')
                pyautogui.keyDown('w')
            else:
                # pyautogui.mouseDown(button='left')
                # pyautogui.mouseDown(button='right')
                pyautogui.keyDown('q')
                pyautogui.keyDown('w')
        elif self.action_space_type == "box":
            click, move = divmod(action[0], self.discrete_width * self.discrete_height)
            y, x = divmod(move, self.discrete_width)
            if click == 0:
                # pyautogui.mouseUp(button='left')
                # pyautogui.mouseUp(button='right')
                pyautogui.keyUp('q')
                pyautogui.keyUp('w')
            elif click == 1:
                # pyautogui.mouseDown(button='left')
                # pyautogui.mouseUp(button='right')
                pyautogui.keyDown('q')
                pyautogui.keyUp('w')
            elif click == 2:
                # pyautogui.mouseUp(button='left')
                # pyautogui.mouseDown(button='right')
                pyautogui.keyUp('q')
                pyautogui.keyDown('w')
            else:
                # pyautogui.mouseDown(button='left')
                # pyautogui.mouseDown(button='right')
                pyautogui.keyDown('q')
                pyautogui.keyDown('w')
                
        top, left = self.hwnd_top, self.hwnd_left
        discrete_width_factor = (width - 50) / self.discrete_width
        discrete_height_factor = (height - 50 - 25) / self.discrete_height
        real_x = int(left + x * discrete_width_factor)
        real_y = int(top + y * discrete_height_factor)

        # pyautogui.moveTo(real_x, real_y)

        curve = HumanCurve(pyautogui.position(), (real_x, real_y), targetPoints=10)

        self.action_thread = threading.Thread(target=self._action_thread, args=(real_x, real_y, curve))
        self.action_thread.start()

        # hc = HumanClicker()
        # curve = HumanCurve(pyautogui.position(), (real_x, real_y), targetPoints=10)
        # hc.move((real_x, real_y), 0.01, humanCurve=curve)

if __name__ == "__main__":
    pass