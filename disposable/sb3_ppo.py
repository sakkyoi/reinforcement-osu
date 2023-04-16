import pyautogui

# from stable_baselines3 import PPO
from sb3_contrib import RecurrentPPO as PPO
from stable_baselines3.common.evaluation import evaluate_policy

from environment import ENV

from pynput.keyboard import Key, Listener

from stable_baselines3.common.vec_env import DummyVecEnv

pyautogui.FAILSAFE = False
IS_EXIT = False

def _exit(key):
    global IS_EXIT
    if key == Key.pause:
        IS_EXIT = True

listener = Listener(on_release=_exit)
listener.start()

# env = ENV(no_fail=True, action_space_type="multi_discrete")
env = DummyVecEnv([lambda: ENV(no_fail=True, action_space_type="multi_discrete")])

model = PPO('CnnLstmPolicy', env, verbose=2, learning_rate=1e-4, gamma=0.99, batch_size=32, policy_kwargs=dict(normalize_images=False), device='cuda')

while True:
    # continue training
    try:
        model = PPO.load("ppo_osu", env=env)
    except:
        pass
    
    model.learn(total_timesteps=10_000)

    mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=10)
    print(f"mean_reward:{mean_reward:.2f} +/- {std_reward:.2f}")

    model.save("ppo_osu")
    print('model saved')
    del model
    if IS_EXIT:
        break

listener.stop()