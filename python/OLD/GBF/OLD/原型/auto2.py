import pyautogui, cv2
from time import sleep, time
import keyboard
from IPython.display import clear_output
import cv2

# gg = pyautogui.position()

# print(gg)

i = 0

while i < 600:
    i = i + 1
    pyautogui.click(x=1665, y=740, clicks=2, interval=1, button="left")
    sleep(3)
    pyautogui.click(x=1415, y=590, clicks=1, button="left")
    sleep(0.3)
    pyautogui.click(x=1574, y=619, clicks=1, button="left")
    sleep(0.2)
    pyautogui.click(x=1682, y=474, clicks=1, button="left")
    sleep(4)
    pyautogui.hotkey("alt", "left")
    sleep(1.7)
    pyautogui.click(x=1575, y=512, clicks=2, interval=0.5, button="left")
    sleep(0.5)
    pyautogui.click(x=1486, y=515, clicks=1, button="left")
    sleep(1)
