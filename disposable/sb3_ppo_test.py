import pyautogui

from stable_baselines3 import PPO
from environment import ENV

env = ENV(no_fail=True, action_space_type="multi_discrete")

model = PPO.load("ppo2_osu", env=env)

obs = env.reset()
while True:
    action, _states = model.predict(obs.reshape(1, 55, 76))
    obs, rewards, dones, info = env.step(action)
    env.render(obs)

