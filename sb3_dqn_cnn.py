import pyautogui

from stable_baselines3 import DQN
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

env = ENV(no_fail=True)

model = DQN('CnnPolicy', env, verbose=1, buffer_size=100, learning_rate=0.001, gamma=0.999, batch_size=32, policy_kwargs=dict(normalize_images=False), device='cuda') # https://stable-baselines3.readthedocs.io/en/master/guide/custom_env.html

while True:
    # continue training
    model = DQN.load("dqn_osu", env=env)

    # check if the model is already trained
    # 
    # try:
    # 
    #     model = DQN.load("dqn_osu")
    # 
    # except:
    # 
    #     pass

    model.learn(total_timesteps=10_000)
    model.save("dqn_osu")
    print('model saved')
    del model
    if IS_EXIT:
        break

listener.stop()