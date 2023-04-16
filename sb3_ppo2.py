"""
This is to train for clicking task
"""

import pyautogui

# from stable_baselines3 import PPO
from sb3_contrib import RecurrentPPO as PPO
from stable_baselines3.common.evaluation import evaluate_policy

from environment2 import ENV

from pynput.keyboard import Key, Listener

from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.monitor import Monitor

pyautogui.FAILSAFE = False
IS_EXIT = False

def _exit(key):
    global IS_EXIT
    if key == Key.pause:
        IS_EXIT = True

listener = Listener(on_release=_exit)
listener.start()

# env = ENV(no_fail=True, action_space_type="multi_discrete")
env = ENV(no_fail=True, auto_pilot=True, action_space_type="multi_discrete")
env_dummyvec = DummyVecEnv([lambda: Monitor(env)])
env._set_training_mode(0) # set to training mode

while True:
    # continue training
    try:
        model = PPO.load("ppo2_osu", env=env_dummyvec, verbose=2)
        print('model loaded')
    except:
        model = PPO('CnnLstmPolicy', env_dummyvec, verbose=2, learning_rate=2.5e-4, gamma=0.99, batch_size=256, n_steps=1280, policy_kwargs=dict(normalize_images=False), device='cuda')
        print('model not found, create it')
    
    model.learn(total_timesteps=10_000)

    env._set_training_mode(1) # set to evaluation mode

    mean_reward, std_reward = evaluate_policy(model, env_dummyvec, n_eval_episodes=3)
    # print(f"mean_reward:{mean_reward:.2f} +/- {std_reward:.2f}")
    print(f"mean_reward:{mean_reward:.2f}")
    print(f"std_reward:{std_reward:.2f}")

    with open('evaluations.txt', 'a') as f:
        f.write(f"mean_reward:{mean_reward:.2f} +/- {std_reward:.2f}" + "\n")

    env._set_training_mode(0) # set to training mode

    model.save("ppo2_osu")
    print('model saved')
    del model
    if IS_EXIT:
        break

listener.stop()