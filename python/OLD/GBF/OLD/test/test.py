import pyautogui, cv2, sys
from time import sleep, time
import keyboard
from IPython.display import clear_output
import cv2, os
import threading
import multiprocessing
import selenium

i = 0
j = 0
outok = 0


# def b():
#     m = 0
#     while True:
#         m = m + 1
#         print(m)
#         if keyboard.is_pressed("5"):
#             b1.terminate()
#         sleep(0.5)


# if __name__ == "__main__":
#     b1 = multiprocessing.Process(target=b)
#     b1.start()

# gg = pyautogui.position()

# print(gg)

# try:
#     (xclassup1, yclassup1) = pyautogui.locateCenterOnScreen(
#         "classup1.png", confidence=0.9
#     )
# except:
#     pass
# else:
#     pyautogui.click(x=xclassup1, y=yclassup1, clicks=1, button="left")

# print("ok")

x1, y1 = pyautogui.locateCenterOnScreen("mypage.png", confidence=0.8)
pyautogui.click(x1, y1, button="left")
sleep(1)
try:
    x2, y2 = pyautogui.locateCenterOnScreen("reload1.png", confidence=0.8)
except:
    pass
sleep(1)
for i in range(0, 7):
    pyautogui.press("down")

print(x2, y2)
pyautogui.moveTo(x2, y2)

# while i < 1:
#     try:
#         (x1, y1) = pyautogui.locateCenterOnScreen("2.png", confidence=0.7)
#         break
#     except:
#         pass
