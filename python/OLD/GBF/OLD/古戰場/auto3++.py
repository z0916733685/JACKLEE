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
        while True:  # 次數
            k = 0
            i = i + 1
            while j < 1:
                k = k + 1
                try:
                    (x1_1, y1_1) = pyautogui.locateCenterOnScreen(
                        "1_1.png", confidence=0.8
                    )
                    sleep(0.1)
                except:
                    try:
                        (x1_2, y1_2) = pyautogui.locateCenterOnScreen(
                            "1_2.png", confidence=0.8
                        )
                        sleep(0.1)
                    except:
                        try:
                            (x1_3, y1_3) = pyautogui.locateCenterOnScreen(
                                "1_3.png", confidence=0.8
                            )
                            sleep(0.1)
                        except:
                            try:
                                (xifno, yifno) = pyautogui.locateCenterOnScreen(
                                    "ifno.png", confidence=0.8
                                )
                                sleep(0.1)
                            except:
                                if k > 1000:
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
                            pyautogui.click(x=x1_3, y=y1_3, clicks=1, button="left")
                            k = 0
                            sleep(0.1)
                            break
                    else:
                        pyautogui.click(x=x1_2, y=y1_2, clicks=1, button="left")
                        k = 0
                        sleep(0.1)
                        break
                else:
                    pyautogui.click(x=x1_1, y=y1_1, clicks=1, button="left")
                    k = 0
                    sleep(0.1)
                    break

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x2, y2) = pyautogui.locateCenterOnScreen("2.png", confidence=0.9)
                except:
                    pass
                else:
                    pyautogui.click(x=x2, y=y2, clicks=1, button="left")
                    k = 0
                    sleep(0.1)
                    break
                if k >= 5000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x2_1, y2_1) = pyautogui.locateCenterOnScreen(
                        "2_1.png", confidence=0.9
                    )
                except:
                    pass
                else:
                    sleep(2.5)
                    pyautogui.click(x=x2_1, y=y2_1, clicks=1, button="left")
                    k = 0
                    break
                if k >= 5000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x2_2, y2_2) = pyautogui.locateCenterOnScreen(
                        "2_2.png", confidence=0.9
                    )
                except:
                    pass
                else:
                    pyautogui.click(x=x2_2, y=y2_2, clicks=1, button="left")
                    k = 0
                    sleep(0.1)
                    break
                if k >= 5000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x2_3, y2_3) = pyautogui.locateCenterOnScreen(
                        "2_3.png", confidence=0.9
                    )
                except:
                    pass
                else:
                    pyautogui.click(x=x2_3, y=y2_3, clicks=1, button="left")
                    k = 0
                    sleep(0.1)
                    break
                if k >= 5000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x2_4, y2_4) = pyautogui.locateCenterOnScreen(
                        "2_4.png", confidence=0.9
                    )
                except:
                    pass
                else:
                    pyautogui.click(x=x2_4, y=y2_4, clicks=1, button="left")
                    k = 0
                    sleep(0.1)
                    break
                if k >= 5000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x2_5, y2_5) = pyautogui.locateCenterOnScreen(
                        "2_5.png", confidence=0.9
                    )
                except:
                    pass
                else:
                    pyautogui.click(x=x2_5, y=y2_5, clicks=1, button="left")
                    k = 0
                    sleep(0.1)
                    break
                if k >= 5000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x2_6, y2_6) = pyautogui.locateCenterOnScreen(
                        "2_6.png", confidence=0.9
                    )
                except:
                    pass
                else:
                    pyautogui.click(x=x2_6, y=y2_6, clicks=1, button="left")
                    k = 0
                    sleep(0.1)
                    break
                if k >= 5000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x2_7, y2_7) = pyautogui.locateCenterOnScreen(
                        "2_7.png", confidence=0.9
                    )
                except:
                    pass
                else:
                    pyautogui.click(x=x2_7, y=y2_7, clicks=1, button="left")
                    k = 0
                    sleep(0.1)
                    break
                if k >= 5000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (x3, y3) = pyautogui.locateCenterOnScreen("3.png", confidence=0.9)
                except:
                    pass
                else:
                    pyautogui.click(x=x3, y=y3, clicks=1, button="left")
                    k = 0
                    break
                if k >= 1000:
                    self.reload()

            while j < 1:
                if keyboard.is_pressed("5"):
                    sys.exit(0)
                k = k + 1
                try:
                    (xready1, yready1) = pyautogui.locateCenterOnScreen(
                        "ready1.png", confidence=0.85
                    )
                except:
                    try:
                        (xready2, yready2) = pyautogui.locateCenterOnScreen(
                            "ready2.png", confidence=0.7
                        )
                    except:
                        pass
                    else:
                        sleep(0.2)
                        pyautogui.hotkey("alt", "left")
                        k = 0
                        break
                else:
                    sleep(0.2)
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
                    try:
                        (xrankup, yrankup) = pyautogui.locateCenterOnScreen(
                            "rankup.png", confidence=0.8
                        )
                    except:
                        pass
                    else:
                        self.rankup
                    (x4, y4) = pyautogui.locateCenterOnScreen("4.png", confidence=0.9)
                except:
                    pass
                else:
                    pyautogui.click(x=x4, y=y4, clicks=1, button="left")
                    pyautogui.hotkey("alt", "left")
                    k = 0
                    break
                if k >= 1000:
                    self.reload()

    def classup(self):
        try:
            (xclassup1, yclassup1) = pyautogui.locateCenterOnScreen(
                "classup1.png", confidence=0.6
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
        # sleep(1)
        # try:
        #     (xreload1, yreload1) = pyautogui.locateCenterOnScreen(
        #         "reload1.png", confidence=0.9
        #     )
        # except:
        #     pass
        # else:
        #     pyautogui.click(x=xreload1, y=yreload1, clicks=1, button="left")
        # sleep(1)
        # try:
        #     (xreload2, yreload2) = pyautogui.locateCenterOnScreen(
        #         "reload2.png", confidence=0.9
        #     )
        # except:
        #     pass
        # else:
        #     pyautogui.click(x=xreload2, y=yreload2, clicks=1, button="left")
        # sleep(1)
        # try:
        #     (xreload3, yreload3) = pyautogui.locateCenterOnScreen(
        #         "reload3.png", confidence=0.9
        #     )
        # except:
        #     pass
        # else:
        #     pyautogui.click(x=xreload3, y=yreload3, clicks=1, button="left")
        # sleep(1)
        # try:
        #     (xreload4, yreload4) = pyautogui.locateCenterOnScreen(
        #         "reload4.png", confidence=0.9
        #     )
        # except:
        #     pass
        # else:
        #     pyautogui.click(x=xreload4, y=yreload4, clicks=1, button="left")
        # sleep(1)
        # try:
        #     (xreload5, yreload5) = pyautogui.locateCenterOnScreen(
        #         "reload5.png", confidence=0.9
        #     )
        # except:
        #     pass
        # else:
        #     pyautogui.click(x=xreload5, y=yreload5, clicks=1, button="left")
        # self.realdo()


if __name__ == "__main__":
    doit()
