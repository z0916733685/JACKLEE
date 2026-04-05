import pyautogui, cv2
from time import sleep, time
import keyboard
from IPython.display import clear_output
import cv2

i = 0

while i < 1:
    pyautogui.click(x=1660, y=690, clicks=2, interval=0.5, button="left")
    sleep(1)
    pyautogui.click(x=1680, y=475, clicks=2, interval=1, button="left")
    sleep(0.3)
    pyautogui.hotkey("alt", "left")
    sleep(0.3)
    pyautogui.click(x=1680, y=475, button="left")
    sleep(0.3)
    pyautogui.hotkey("alt", "left")
    sleep(0.3)
