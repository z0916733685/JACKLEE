import pyautogui, cv2, sys
from time import sleep, time
import keyboard
from IPython.display import clear_output
import multiprocessing
import cv2
import selenium


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
            self.other()

            while j < 1:
                k = k + 1
                try:
                    (x0_1, y0_1) = pyautogui.locateCenterOnScreen(
                        "0_1.png", confidence=0.8
                    )
                    sleep(0.1)
                except:
                    try:
                        (x0_2, y0_2) = pyautogui.locateCenterOnScreen(
                            "0_2.png", confidence=0.8
                        )
                        sleep(0.1)
                    except:
                        try:
                            (x0_3, y0_3) = pyautogui.locateCenterOnScreen(
                                "0_3.png", confidence=0.8
                            )
                            sleep(0.1)
                        except:
                            try:
                                (xifno, yifno) = pyautogui.locateCenterOnScreen(
                                    "ifno.png", confidence=0.8
                                )
                                sleep(0.1)
                            except:
                                if k > 10:
                                    self.reload()
                                if keyboard.is_pressed("5"):
                                    sys.exit(0)
                                pass
                            else:
                                pyautogui.click(
                                    x=xifno, y=yifno, clicks=1, button="left"
                                )
                                k = 0
                                sleep(0.1)
                                break
                        else:
                            pyautogui.click(x=x0_3, y=y0_3, clicks=1, button="left")
                            k = 0
                            sleep(0.1)
                            break
                    else:
                        pyautogui.click(x=x0_2, y=y0_2, clicks=1, button="left")
                        k = 0
                        sleep(0.1)
                        break
                else:
                    pyautogui.click(x=x0_1, y=y0_1, clicks=1, button="left")
                    k = 0
                    sleep(0.1)
                    break

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    sleep(1)
                    (x1, y1) = pyautogui.locateCenterOnScreen("1.png", confidence=0.9)
                except:
                    pass
                else:
                    pyautogui.click(x=x1, y=y1, clicks=1, button="left")
                    k = 0
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (xin, yin) = pyautogui.locateCenterOnScreen(
                        "in.png", confidence=0.7
                    )
                except:
                    pass
                else:
                    k = 0
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x2, y2) = pyautogui.locateCenterOnScreen("2.png", confidence=0.9)
                except:
                    pass
                else:
                    sleep(0.5)
                    pyautogui.click(x=x2, y=y2, clicks=1, button="left")
                    k = 0
                    try:
                        (x3_1, y3_1) = pyautogui.locateCenterOnScreen(
                            "3_1.png", confidence=0.9
                        )
                    except:
                        pass
                    else:
                        break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x3_1, y3_1) = pyautogui.locateCenterOnScreen(
                        "3_1.png", confidence=0.9
                    )
                except:
                    pass
                else:
                    pyautogui.click(x=x3_1, y=y3_1, clicks=1, button="left")
                    k = 0
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x3_2, y3_2) = pyautogui.locateCenterOnScreen(
                        "3_2.png", confidence=0.9
                    )
                except:
                    pass
                else:
                    pyautogui.click(x=x3_2, y=y3_2, clicks=1, button="left")
                    k = 0
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x4_1, y4_1) = pyautogui.locateCenterOnScreen(
                        "4.png", confidence=0.9
                    )
                except:
                    pass
                else:
                    sleep(0.2)
                    pyautogui.click(x=x4_1, y=y4_1, clicks=1, button="left")
                    k = 0
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (xready1_1, yready1_1) = pyautogui.locateCenterOnScreen(
                        "ready1.png", confidence=0.8
                    )
                except:
                    try:
                        (xready2_1, yready2_1) = pyautogui.locateCenterOnScreen(
                            "ready2.png", confidence=0.7
                        )
                    except:
                        pass
                    else:
                        sleep(0.5)
                        pyautogui.hotkey("alt", "left")
                        k = 0
                        break
                else:
                    sleep(0.5)
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
                    (x6, y6) = pyautogui.locateCenterOnScreen("6.png", confidence=0.95)
                except:
                    try:
                        (x4_2, y4_2) = pyautogui.locateCenterOnScreen(
                            "4.png", confidence=0.9
                        )
                    except:
                        pass
                    else:
                        while j < 1:
                            l = l + 1
                            try:
                                (x4_3, y4_3) = pyautogui.locateCenterOnScreen(
                                    "4.png", confidence=0.9
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
                                pyautogui.click(x=x4_2, y=y4_2, clicks=1, button="left")
                                sleep(0.5)
                            if l > 1000:
                                self.reload()
                else:
                    pyautogui.click(x=x6, y=y6, clicks=1, button="left")
                    k = 0
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x7, y7) = pyautogui.locateCenterOnScreen("7.png", confidence=0.9)
                except:
                    self.rankup()
                    self.classup()
                    self.OK()
                    self.other()
                    pass
                else:
                    pyautogui.click(x=x7, y=y7, clicks=1, button="left")
                    k = 0
                    break
                if k >= 1000:
                    self.reload()

    def OK(self):
        try:
            (xrankok1, yrankok1) = pyautogui.locateCenterOnScreen(
                "okok.png", confidence=0.95
            )
        except:
            pass
        else:
            pyautogui.click(x=xrankok1, y=yrankok1, clicks=1, button="left")

    def other(self):
        try:
            (xother, yother) = pyautogui.locateCenterOnScreen(
                "other.png", confidence=0.85
            )
        except:
            pass
        else:
            pyautogui.click(x=xother, y=yother, clicks=1, button="left")

    def classup(self):
        try:
            (xclassup0, yclassup0) = pyautogui.locateCenterOnScreen(
                "classup0.png", confidence=0.8
            )
        except:
            pass
        else:
            sleep(0.5)
            pyautogui.click(x=xclassup0, y=yclassup0, clicks=1, button="left")

        try:
            (xclassup1, yclassup1) = pyautogui.locateCenterOnScreen(
                "classup1.png", confidence=0.8
            )
        except:
            pass
        else:
            sleep(0.5)
            pyautogui.click(x=xclassup1, y=yclassup1, clicks=1, button="left")

        try:
            (xclassup2, yclassup2) = pyautogui.locateCenterOnScreen(
                "classup2.png", confidence=0.8
            )
        except:
            pass
        else:
            sleep(0.5)
            pyautogui.click(x=xclassup2, y=yclassup2, clicks=1, button="left")

        try:
            (xclassup3, yclassup3) = pyautogui.locateCenterOnScreen(
                "classup3.png", confidence=0.8
            )
        except:
            pass
        else:
            sleep(0.5)
            pyautogui.click(x=xclassup3, y=yclassup3, clicks=1, button="left")

        try:
            (xclassup4, yclassup4) = pyautogui.locateCenterOnScreen(
                "classup4.png", confidence=0.8
            )
        except:
            pass
        else:
            sleep(0.5)
            pyautogui.click(x=xclassup4, y=yclassup4, clicks=1, button="left")

        try:
            (xclassup5, yclassup5) = pyautogui.locateCenterOnScreen(
                "classup5.png", confidence=0.8
            )
        except:
            pass
        else:
            sleep(0.5)
            pyautogui.click(x=xclassup5, y=yclassup5, clicks=1, button="left")

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
        pass
        # try:
        #     (xmypage, ymypage) = pyautogui.locateCenterOnScreen(
        #         "mypage.png", confidence=0.9
        #     )
        # except:
        #     pass
        # else:
        #     pyautogui.click(x=xmypage, y=ymypage, clicks=1, button="left")
        # sleep(0.5)
        # for m1 in range(0, 25):
        #     pyautogui.press("down")
        #     sleep(0.2)
        # sleep(0.5)
        # try:
        #     (xreload1, yreload1) = pyautogui.locateCenterOnScreen(
        #         "reload1.png", confidence=0.9
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
        #         "reload2.png", confidence=0.9
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
        #         "reload3.png", confidence=0.9
        #     )
        # except:
        #     pass
        # else:
        #     pyautogui.click(x=xreload3, y=yreload3, clicks=1, button="left")
        # self.realdo()


if __name__ == "__main__":
    doit()
