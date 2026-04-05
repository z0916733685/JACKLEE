import pyautogui, cv2, sys
from time import sleep, time
import keyboard
from IPython.display import clear_output
import multiprocessing
import cv2


class doit:
    def __init__(self):
        do1 = multiprocessing.Process(target=self.realdo)
        do1.start()
        do1.join()

    def realdo(self):
        i = 0
        j = 0
        while True:
            k = 0
            l = 0
            i = i + 1
            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                sleep(1)
                try:
                    (x1, y1) = pyautogui.locateCenterOnScreen("1.png", confidence=0.8)
                except:
                    pass
                else:
                    pyautogui.click(x=x1, y=y1, clicks=1, button="left")
                    k = 0
                    sleep(0.4)
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (xin, yin) = pyautogui.locateCenterOnScreen(
                        "in.png", confidence=0.8
                    )
                except:
                    pass
                else:
                    k = 0
                    sleep(1.2)
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x2, y2) = pyautogui.locateCenterOnScreen("2.png", confidence=0.8)
                except:
                    pass
                else:
                    pyautogui.click(x=x2, y=y2, clicks=1, button="left")
                    k = 0
                    sleep(0.4)
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x3, y3) = pyautogui.locateCenterOnScreen("3.png", confidence=0.8)
                except:
                    pass
                else:
                    pyautogui.click(x=x3, y=y3, clicks=1, button="left")
                    k = 0
                    sleep(0.4)
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (xgoright1, ygoright1) = pyautogui.locateCenterOnScreen(
                        "goright.png", confidence=0.8
                    )
                except:
                    pass
                else:
                    pyautogui.click(x=xgoright1, y=ygoright1, clicks=1, button="left")
                    k = 0
                    sleep(0.4)
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x4, y4) = pyautogui.locateCenterOnScreen("4.png", confidence=0.8)
                except:
                    pass
                else:
                    pyautogui.click(x=x4, y=y4, clicks=1, button="left")
                    k = 0
                    sleep(0.4)
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x5, y5) = pyautogui.locateCenterOnScreen("5.png", confidence=0.8)
                except:
                    pass
                else:
                    pyautogui.click(x=x5, y=y5, clicks=1, button="left")
                    k = 0
                    sleep(0.4)
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (xgoright2, ygoright2) = pyautogui.locateCenterOnScreen(
                        "goright.png", confidence=0.8
                    )
                except:
                    pass
                else:
                    pyautogui.click(x=xgoright2, y=ygoright2, clicks=1, button="left")
                    k = 0
                    sleep(0.4)
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x6, y6) = pyautogui.locateCenterOnScreen("6.png", confidence=0.8)
                except:
                    pass
                else:
                    pyautogui.click(x=x6, y=y6, clicks=1, button="left")
                    k = 0
                    sleep(0.4)
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (xgoright3, ygoright3) = pyautogui.locateCenterOnScreen(
                        "goright.png", confidence=0.8
                    )
                except:
                    pass
                else:
                    pyautogui.click(x=xgoright3, y=ygoright3, clicks=1, button="left")
                    k = 0
                    sleep(0.4)
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x7, y7) = pyautogui.locateCenterOnScreen("7.png", confidence=0.8)
                except:
                    pass
                else:
                    pyautogui.click(x=x7, y=y7, clicks=1, button="left")
                    k = 0
                    sleep(0.4)
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x8, y8) = pyautogui.locateCenterOnScreen("8.png", confidence=0.8)
                except:
                    pass
                else:
                    pyautogui.click(x=x8, y=y8, clicks=1, button="left")
                    k = 0
                    sleep(0.4)
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (xgoleft, ygoleft) = pyautogui.locateCenterOnScreen(
                        "goleft.png", confidence=0.8
                    )
                except:
                    pass
                else:
                    pyautogui.click(x=xgoleft, y=ygoleft, clicks=1, button="left")
                    k = 0
                    sleep(0.4)
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x9, y9) = pyautogui.locateCenterOnScreen("9.png", confidence=0.8)
                except:
                    pass
                else:
                    pyautogui.click(x=x9, y=y9, clicks=1, button="left")
                    k = 0
                    sleep(0.4)
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (xgoleft1, ygoleft1) = pyautogui.locateCenterOnScreen(
                        "goleft.png", confidence=0.8
                    )
                except:
                    pass
                else:
                    pyautogui.click(x=xgoleft1, y=ygoleft1, clicks=1, button="left")
                    k = 0
                    sleep(0.4)
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x10, y10) = pyautogui.locateCenterOnScreen(
                        "10.png", confidence=0.8
                    )
                except:
                    pass
                else:
                    pyautogui.click(x=x10, y=y10, clicks=1, button="left")
                    k = 0
                    sleep(0.4)
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x11_1, y11_1) = pyautogui.locateCenterOnScreen(
                        "11.png", confidence=0.8
                    )
                except:
                    pass
                else:
                    pyautogui.click(x=x11_1, y=y11_1, clicks=1, button="left")
                    k = 0
                    sleep(0.4)
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (xready1_1, yready1_1) = pyautogui.locateCenterOnScreen(
                        "ready1.png", confidence=0.85
                    )
                except:
                    try:
                        (xready2_1, yready2_1) = pyautogui.locateCenterOnScreen(
                            "ready2.png", confidence=0.7
                        )
                    except:
                        pass
                    else:
                        sleep(0.4)
                        pyautogui.hotkey("alt", "left")
                        k = 0
                        break
                else:
                    sleep(0.4)
                    pyautogui.hotkey("alt", "left")
                    k = 0
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x12, y12) = pyautogui.locateCenterOnScreen(
                        "12.png", confidence=0.85
                    )
                except:
                    try:
                        (x11_2, y11_2) = pyautogui.locateCenterOnScreen(
                            "11.png", confidence=0.85
                        )
                    except:
                        pass
                    else:
                        while j < 1:
                            l = l + 1
                            try:
                                (x11_3, y11_3) = pyautogui.locateCenterOnScreen(
                                    "11.png", confidence=0.85
                                )
                            except:
                                try:
                                    (xready1_2, yready1_2) = (
                                        pyautogui.locateCenterOnScreen(
                                            "ready1.png", confidence=0.8
                                        )
                                    )
                                except:
                                    try:
                                        (xready2_2, yready2_2) = (
                                            pyautogui.locateCenterOnScreen(
                                                "ready2.png", confidence=0.8
                                            )
                                        )
                                    except:
                                        pass
                                    else:
                                        pyautogui.click(
                                            x=xready2_2,
                                            y=yready2_2,
                                            clicks=1,
                                            button="left",
                                        )
                                        sleep(0.4)
                                        pyautogui.hotkey("alt", "left")
                                        l = 0
                                        break
                                else:
                                    pyautogui.click(
                                        x=xready1_2,
                                        y=yready1_2,
                                        clicks=1,
                                        button="left",
                                    )
                                    sleep(0.4)
                                    pyautogui.hotkey("alt", "left")
                                    l = 0
                                    break
                            else:
                                pyautogui.click(
                                    x=x11_2, y=y11_2, clicks=1, button="left"
                                )
                                sleep(0.5)
                            if l > 1000:
                                sys.exit(0)
                else:
                    pyautogui.click(x=x12, y=y12, clicks=1, button="left")
                    k = 0
                    sleep(0.4)
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x13, y13) = pyautogui.locateCenterOnScreen(
                        "13.png", confidence=0.8
                    )
                except:
                    self.rankup()
                    self.classup()
                    pass
                else:
                    pyautogui.click(x=x13, y=y13, clicks=1, button="left")
                    k = 0
                    sleep(0.4)
                    break
                if k >= 1000:
                    self.reload()

    def classup(self):
        try:
            (xclassup1, yclassup1) = pyautogui.locateCenterOnScreen(
                "classup6.png", confidence=0.8
            )
        except:
            pass
        else:
            sleep(0.5)
            pyautogui.click(x=xclassup1, y=yclassup1, clicks=1, button="left")

    def rankup(self):
        try:
            (xrankup, yrankup) = pyautogui.locateCenterOnScreen(
                "rankup.png", confidence=0.8
            )
            (xrankok, yrankok) = pyautogui.locateCenterOnScreen(
                "rankok.png", confidence=0.8
            )
        except:
            pass
        else:
            sleep(0.5)
            pyautogui.click(x=xrankok, y=yrankok, clicks=1, button="left")

    def reload(self):
        1
        # try:
        #     (xmypage, ymypage) = pyautogui.locateCenterOnScreen(
        #         "mypage.png", confidence=0.8
        #     )
        # except:
        #     pass
        # else:
        #     pyautogui.click(x=xmypage, y=ymypage, clicks=1, button="left")
        # sleep(0.5)
        # for m1 in range(0, 9):
        #     pyautogui.press("down")
        #     sleep(0.2)
        # sleep(0.5)
        # try:
        #     (xreload1, yreload1) = pyautogui.locateCenterOnScreen(
        #         "reload1.png", confidence=0.8
        #     )
        # except:
        #     pass
        # else:
        #     pyautogui.click(x=xreload1, y=yreload1, clicks=1, button="left")
        # sleep(0.5)
        # for m2 in range(0, 3):
        #     pyautogui.press("down")
        #     sleep(0.2)
        # try:
        #     (xreload2, yreload2) = pyautogui.locateCenterOnScreen(
        #         "reload2.png", confidence=0.8
        #     )
        # except:
        #     pass
        # else:
        #     pyautogui.click(x=xreload2, y=yreload2, clicks=1, button="left")
        # sleep(0.5)
        # for m3 in range(0, 3):
        #     pyautogui.press("down")
        #     sleep(0.2)
        # sleep(0.5)
        # try:
        #     (xreload3, yreload3) = pyautogui.locateCenterOnScreen(
        #         "reload3.png", confidence=0.8
        #     )
        # except:
        #     pass
        # else:
        #     pyautogui.click(x=xreload3, y=yreload3, clicks=1, button="left")
        


if __name__ == "__main__":
    doit()
