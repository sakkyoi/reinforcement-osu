import pyautogui

# from stable_baselines3 import PPO
from sb3_contrib import RecurrentPPO as PPO
from stable_baselines3.common.evaluation import evaluate_policy

from environment import ENV

from pynput.keyboard import Key, Listener

from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.monitor import Monitor

import torch as th

env = ENV(no_fail=True, auto_pilot=True, action_space_type="multi_discrete", frame_limit=30)
env_dummyvec = DummyVecEnv([lambda: Monitor(env)])
env._set_training_mode(-1) # set to no logging mode

model = PPO.load("./ppo2_osu", env=env_dummyvec, verbose=2)

obs = env.reset()
while True:
    action, _states = model.predict(obs, deterministic=True)
    obs, rewards, dones, info = env.step(action)
    #env.render()