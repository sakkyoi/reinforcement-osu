"""Set of functions to inject into osu! process and read memory values from it."""
import sys
from pymem import pattern, Pymem
import subprocess
from time import sleep
import pyautogui

import win32api
import win32gui
import win32process
import win32con

from mss.windows import MSS as mss

import cv2
import numpy as np

import threading
import pyclick

class OSUInjector:
    def __init__(self, osu_path: str, no_fail: bool = False):
        self.no_fail = no_fail

        self.human_clicker = pyclick.HumanClicker()
        self.mss = mss()
        self.thread = None
        self.osu_path = osu_path
        proccess = subprocess.Popen(self.osu_path)
        sleep(5)
        self.pid = proccess.pid
        print('osu! started with PID: ' + str(self.pid))

        self._init_map_selection()
        pm = Pymem("osu!.exe")
        self.pm = pm
        self.base_sign = "F8 01 74 04 83 65"
        self.playcontainer_sign = "C7 86 48 01 00 00 01 00 00 00 A1" # Avaliable only when playing(OsuStatus=2 single mode)
        self.address_base = pattern.pattern_scan_all(self.pm.process_handle, self.pattern_converter(self.base_sign))
        self.address_play_container = pattern.pattern_scan_all(self.pm.process_handle, self.pattern_converter(self.playcontainer_sign))

    def get_osu_status(self) -> int:
        """Returns the current status of the osu! client."""
        return self.offset(self.address_base, offsets=[ -0x3c, 0x0 ], read='int') # the 0x0 offset is because it has offset of -0x3c and pointer offset of 0x0
    
    def get_play_container(self) -> dict:
        """Returns a dict with playing status. if not playing, returns None."""
        try:
            address_to_play_container = self.offset(self.address_play_container, offsets=[ 0xb, 0x4, 0x60 ], read='int')
            return {
                'score': self.offset(address_to_play_container, offsets=[ 0x38, 0x78 ], read='int'),
                'scorev2': self.offset(address_to_play_container, offsets=[ 0x4c, 0xc, 0x68, 0x4, 0xf8 ], read='int'),
                'accuracy': self.offset(address_to_play_container, offsets=[ 0x48, 0x14 ], read='double'),
                'combo': self.offset(address_to_play_container, offsets=[ 0x38, 0x94 ], read='ushort'),
                'combo_max': self.offset(address_to_play_container, offsets=[ 0x38, 0x68 ], read='ushort'),
                'hit300': self.offset(address_to_play_container, offsets=[ 0x38, 0x8a ], read='ushort'),
                'hit100': self.offset(address_to_play_container, offsets=[ 0x38, 0x88 ], read='ushort'),
                'hit50': self.offset(address_to_play_container, offsets=[ 0x38, 0x8c ], read='ushort'),
                'hitGeki': self.offset(address_to_play_container, offsets=[ 0x38, 0x8e ], read='ushort'),
                'hitKatsu': self.offset(address_to_play_container, offsets=[ 0x38, 0x90 ], read='ushort'),
                'hitMiss': self.offset(address_to_play_container, offsets=[ 0x38, 0x92 ], read='ushort'),
                'player_hp': self.offset(address_to_play_container, offsets=[ 0x40, 0x1c ], read='ushort'),
                'player_hp_smoothed': self.offset(address_to_play_container, offsets=[ 0x40, 0x14 ], read='ushort'),
            }
        except:
            return None
        
    def get_current_beatmap(self) -> dict:
        """Returns a dict with current beatmap info."""
        try:
            address_to_current_beatmap = self.offset(self.address_base, offsets=[ -0xc, 0x0 ], read='int')
            return {
                'id': self.offset(address_to_current_beatmap, offsets=[ 0xcc ], read='int'), # id of the single beatmap
                'set_id': self.offset(address_to_current_beatmap, offsets=[ 0xd0 ], read='int'), # id of the beatmapset
                'status': self.offset(address_to_current_beatmap, offsets=[ 0x130 ], read='short'), # beatmap ranked status: 1 = unknown, 2 = graveyard, 4 = ranked, 7 = loved
                'ar': self.offset(address_to_current_beatmap, offsets=[ 0x2c ], read='float'),
                'cs': self.offset(address_to_current_beatmap, offsets=[ 0x30 ], read='float'),
                'hp': self.offset(address_to_current_beatmap, offsets=[ 0x34 ], read='float'),
                'od': self.offset(address_to_current_beatmap, offsets=[ 0x38 ], read='float'),
                # there is some string stuff but can not be read by pymem
                # MapString +0x80
                # FolderName +0x78
                # OsuFileName +0x94
                # Md5 +0x6c
            }
        except:
            return None

    def pattern_converter(self, patt: str) -> bytes:
        """Converts a pattern string like 'F8 01 74 04 83 65' to a bytes object like b'\xf8\x01\x74\x04\x83\x65' that can be used by pymem.pattern.pattern_scan_all"""
        return bytes(r'\x' + patt.replace(' ', r'\x').replace(r'\x??', '.').lower(), 'utf-8')
    
    def read_int(self, address) -> int:
        return self.pm.read_int(address)
    
    def read_double(self, address) -> float:
        return self.pm.read_double(address)
    
    def read_ushort(self, address) -> int:
        return self.pm.read_ushort(address)
    
    def read_short(self, address) -> int:
        return self.pm.read_short(address)
    
    def read_float(self, address) -> float:
        return self.pm.read_float(address)
    
    def offset(self, address, offsets: list, read: str = None) -> int:
        """Returns the address of an offset from a base address."""
        for i, offset in enumerate(offsets):
            if i != (len(offsets) - 1):
                address = self.pm.read_int(address + offset)
            else:
                address = address + offset

        if read is not None:
            if read == 'int':
                return self.read_int(address)
            elif read == 'double':
                return self.read_double(address)
            elif read == 'ushort':
                return self.read_ushort(address)
            elif read == 'short':
                return self.read_short(address)
            elif read == 'float':
                return self.read_float(address)
            else:
                raise ValueError(f'Invalid read type: {read}')
        else:
            return address
        
    def _screen_shot(self):
        """Takes a screenshot of the osu! client."""
        # get the position of the osu! window
        hwnd = self._get_hwnd_by_pid()
        rect = win32gui.GetWindowRect(hwnd)
        # take the screenshot
        width, height = self._get_hwnd_size()
        mon = {'top': rect[1] + 25 + 25, 'left': rect[0] + 25, 'width': width - 50, 'height': height - 25 - 50}
        img = img = np.asarray(self.mss.grab(mon))
        img = cv2.resize(img, (0, 0), fx=0.1, fy=0.1)
        # convert to grayscale
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # apply Adaptive Gaussian Thresholding
        # img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        # get edges
        # img = cv2.Canny(img, 30, 200)
        # img = cv2.bitwise_not(img)
        # gaussian blur
        # img = cv2.GaussianBlur(img, (5, 5), 0)
        # normalize to 0-1
        img = cv2.normalize(img, None, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)

        return img
        
    def _get_hwnd_by_pid(self):
        """Returns the hwnd of a window by its pid."""
        def callback(hwnd, hwnds):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == self.pid:
                hwnds.append(hwnd)
            return True
        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        return hwnds[0]
    
    def _get_hwnd_size(self):
        """Returns the size of the osu! client."""
        hwnd = self._get_hwnd_by_pid()
        rect = win32gui.GetWindowRect(hwnd)
        return rect[2] - rect[0], rect[3] - rect[1]
    
    def _get_hwnd_pos(self):
        """Returns the position of the osu! client."""
        hwnd = self._get_hwnd_by_pid()
        rect = win32gui.GetWindowRect(hwnd)
        return rect[1] + 50, rect[0] + 25
    
    def _init_map_selection(self):
        sleep(1)
        self._focus_on_osu()
        # top, left = self._get_hwnd_pos()
        # pyautogui.moveTo(left, top, duration=0.5)
        pyautogui.keyDown('p')
        pyautogui.keyUp('p')
        pyautogui.keyDown('p')
        pyautogui.keyUp('p')
        pyautogui.keyDown('p')
        pyautogui.keyUp('p')
        sleep(2)
        pyautogui.keyDown('down')
        pyautogui.keyUp('down')
        sleep(1)
        pyautogui.keyDown('up')
        pyautogui.keyUp('up')
        sleep(1)
        pyautogui.keyDown('enter')
        pyautogui.keyUp('enter')
        sleep(1)
        if self.no_fail:
            self._toggle_no_fail()
        print('waiting for agent press f2 to random map')
        sleep(1)

    def _toggle_no_fail(self):
        self._focus_on_osu()
        sleep(1)
        pyautogui.keyDown('f1')
        pyautogui.keyUp('f1')
        sleep(2)
        pyautogui.keyDown('w')
        pyautogui.keyUp('w')
        sleep(2)
        pyautogui.keyDown('2')
        pyautogui.keyUp('2')
        sleep(2)

    def _random_map(self):
        self._focus_on_osu()
        sleep(0.5)
        while True:
            pyautogui.keyDown('f2')
            pyautogui.keyUp('f2')
            # waiting for map to be hovered
            while self.get_current_beatmap() is None:
                sleep(0.5)
            # the map must be ranked(4)
            if self.get_current_beatmap()['status'] == 4:
                break
        sleep(1)
        pyautogui.keyDown('enter')
        pyautogui.keyUp('enter')

    def _restart_map(self):
        self._focus_on_osu()
        sleep(0.5)
        pyautogui.keyDown('`')
        sleep(1)
        pyautogui.keyUp('`')

    def _back_to_map_select(self):
        self._focus_on_osu()
        sleep(0.5)
        pyautogui.keyDown('esc')
        pyautogui.keyUp('esc')
        sleep(3)
    
    def _focus_on_osu(self):
        """Focuses on the osu! client."""
        hwnd = self._get_hwnd_by_pid()
        win32gui.SetForegroundWindow(hwnd)

if __name__ == "__main__":
    pyautogui.FAILSAFE = False
    injector = OSUInjector(osu_path="./osu!/osu!.exe")
    while True:
        # pc = injector.get_play_container()
        # status = injector.get_current_beatmap()
        # sys.stdout.write(f'\rStatus: {status}')
        # sys.stdout.flush()

        
        # print(injector._screen_shot())
        cv2.imshow('capture', injector._screen_shot())
        cv2.waitKey(1)

        # if cv2.waitKey(25) & 0xFF == ord('b'):
        #     cv2.destroyAllWindows()
        #     break
