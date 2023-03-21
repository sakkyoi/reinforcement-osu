import pyautogui

import numpy as np
from stable_baselines3 import DDPG
from stable_baselines3.common.noise import NormalActionNoise, OrnsteinUhlenbeckActionNoise
from environment import ENV

from pynput.keyboard import Key, Listener

pyautogui.FAILSAFE = False
IS_EXIT = False

def _exit(key):
    global IS_EXIT
    if key == Key.pause:
        IS_EXIT = True

listener = Listener(on_release=_exit)
listener.start()

env = ENV(no_fail=True, action_space_type="box")

n_actions = env.action_space.shape[-1]
action_noise = NormalActionNoise(mean=np.zeros(n_actions), sigma=0.1 * np.ones(n_actions))

# model = DQN('CnnPolicy', env, verbose=2, buffer_size=100, learning_rate=0.0001, gamma=0.9999, batch_size=32, policy_kwargs=dict(normalize_images=False), device='cuda') # https://stable-baselines3.readthedocs.io/en/master/guide/custom_env.html
model = DDPG('CnnPolicy', env, verbose=2, buffer_size=100, learning_rate=0.001, gamma=0.99, batch_size=32, policy_kwargs=dict(normalize_images=False), device='cuda', action_noise=action_noise)

while True:
    # continue training
    try:
        model = DDPG.load("ddpg_osu", env=env, verbose=2, buffer_size=100, learning_rate=0.001, gamma=0.99, batch_size=32, policy_kwargs=dict(normalize_images=False), device='cuda', action_noise=action_noise)
    except:
        pass
    
    model.learn(total_timesteps=10_000)
    model.save("ddpg_osu")
    print('model saved')
    del model
    if IS_EXIT:
        break

listener.stop()