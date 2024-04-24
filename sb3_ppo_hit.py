"""
This is to train for hit task
"""

import pyautogui

# from stable_baselines3 import PPO
from sb3_contrib import RecurrentPPO as PPO
from stable_baselines3.common.evaluation import evaluate_policy

from environment import ENV

from pynput.keyboard import Key, Listener

from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.monitor import Monitor

import torch as th

pyautogui.FAILSAFE = False
IS_EXIT = False

def _exit(key):
    global IS_EXIT
    if key == Key.pause:
        IS_EXIT = True

listener = Listener(on_release=_exit)
listener.start()

# env = ENV(no_fail=True, action_space_type="multi_discrete")
env = ENV(no_fail=True, auto_pilot=True, action_space_type="multi_discrete", frame_limit=30)
env_dummyvec = DummyVecEnv([lambda: Monitor(env)])
env._set_training_mode(0) # set to training mode

policy_kwargs = dict(
    normalize_images=False,
    activation_fn=th.nn.LeakyReLU,
    features_extractor_kwargs=dict(features_dim=512),
    # ortho_init=False,
    lstm_hidden_size=64,
    enable_critic_lstm=True,
    # net_arch=dict(pi=[64, 64], vf=[64, 64]),
)

while True:
    # continue training
    try:
        model = PPO.load("ppo_osu_hit", env=env_dummyvec, verbose=2)
        print('model loaded')
        model.set_parameters("ppo_osu_hit")
        print('parameters set')
        print('================================')
    except:
        model = PPO('CnnLstmPolicy', env_dummyvec, verbose=2, learning_rate=1e-2, gamma=0.99, batch_size=256, n_steps=1280, n_epochs=4, policy_kwargs=policy_kwargs, device='cuda') # 2.5e-4
        print('model not found, create it')
        print('================================')
    
    model.learn(total_timesteps=10_000)

    env._set_training_mode(1) # set to evaluation mode

    mean_reward, std_reward = evaluate_policy(model, env_dummyvec, n_eval_episodes=3, deterministic=True)
    # print(f"mean_reward:{mean_reward:.2f} +/- {std_reward:.2f}")
    print(f"mean_reward:{mean_reward:.2f}")
    print(f"std_reward:{std_reward:.2f}")

    with open('log_hit/evaluations.txt', 'a') as f:
        f.write(f"mean_reward:{mean_reward:.2f} +/- {std_reward:.2f}" + "\n")

    env._set_training_mode(0) # set to training mode

    model.save("ppo_osu_hit")
    print('model saved')
    del model
    if IS_EXIT:
        break

listener.stop()