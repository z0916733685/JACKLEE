import pyautogui, cv2
from time import sleep, time
import keyboard
from IPython.display import clear_output
import cv2

i = 0

while i < 1:
    i = i + 1
    try:
        (x1, y1) = pyautogui.locateCenterOnScreen("1.png", confidence=0.9)
    except:
        pass

    pyautogui.click(x=x1, y=y1, clicks=2, interval=1, button="left")
    sleep(3)

    try:
        (x2, y2) = pyautogui.locateCenterOnScreen("2.png", confidence=0.9)
    except:
        pass

    pyautogui.click(x=x2, y=y2, clicks=1, button="left")
    sleep(0.3)

    try:
        (x3, y3) = pyautogui.locateCenterOnScreen("3.png", confidence=0.9)
    except:
        pass

    pyautogui.click(x=x3, y=y3, clicks=1, button="left")
    sleep(0.2)

    try:
        (x4, y4) = pyautogui.locateCenterOnScreen("4.png", confidence=0.9)
    except:
        pass

    pyautogui.click(x=x4, y=y4, clicks=1, button="left")
    sleep(4)

    try:
        (x5, y5) = pyautogui.locateCenterOnScreen("5.png", confidence=0.95)
    except:
        pass

    pyautogui.hotkey("alt", "left")
    sleep(1.7)

    try:
        (x6, y6) = pyautogui.locateCenterOnScreen("6.png", confidence=0.95)
    except:
        pass

    pyautogui.click(x=x6, y=y6, clicks=2, interval=0.5, button="left")
    sleep(0.5)

    try:
        (x7, y7) = pyautogui.locateCenterOnScreen("7.png", confidence=0.9)
    except:
        pass

    pyautogui.click(x=x7, y=y7, clicks=1, button="left")
    sleep(1)
