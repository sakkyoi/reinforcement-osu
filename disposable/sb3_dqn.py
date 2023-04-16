import pyautogui

from stable_baselines3 import DQN
from environment import ENV

from pynput.keyboard import Key, Listener

from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

pyautogui.FAILSAFE = False
IS_EXIT = False

def _exit(key):
    global IS_EXIT
    if key == Key.pause:
        IS_EXIT = True

listener = Listener(on_release=_exit)
listener.start()

# env = ENV(no_fail=True)
env = DummyVecEnv([lambda: Monitor(ENV(no_fail=True))])

model = DQN('CnnPolicy', env, verbose=2, buffer_size=100, gamma=0.99, batch_size=256, policy_kwargs=dict(normalize_images=False), device='cuda') # https://stable-baselines3.readthedocs.io/en/master/guide/custom_env.html
# , learning_rate=1

while True:
    # continue training
    try:
        model = DQN.load("dqn_osu", env=env)
    except:
        print('model not found')
        pass
    
    model.learn(total_timesteps=10_000)
    model.save("dqn_osu")
    print('model saved')
    del model
    if IS_EXIT:
        break

listener.stop()