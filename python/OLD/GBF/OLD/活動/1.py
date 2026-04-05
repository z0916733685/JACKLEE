import pyautogui, cv2, sys, os
from time import sleep, time
import keyboard
from IPython.display import clear_output
import threading
import cv2
import selenium


class goout:
    def __init__(self):
        print("yepp")
        do1 = threading.Thread(target=self.outtp)
        do2 = threading.Thread(target=self.gggo)
        do1.start()
        do2.start()

    def outtp(self):
        while True:
            print("2")
            self.riip()
            sleep(0.5)

    def gggo(self):
        while True:
            if keyboard.is_pressed("5"):
                os._exit(0)

    def riip(self):
        print("3")


if __name__ == "__main__":
    goout()
