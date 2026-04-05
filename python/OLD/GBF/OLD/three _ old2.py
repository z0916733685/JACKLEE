import cv2
import numpy as np
import mss
import pyautogui
import keyboard
import threading
import os
import ctypes
from time import sleep

# --- 進階校準區 ---
# 1 通常是主螢幕，2 通常是副螢幕
# 注意：mss 的 sct.monitors[0] 是全螢幕合併，[1] 是第一螢幕，[2] 是第二螢幕
TARGET_MONITOR_INDEX = 2 

# 垂直與水平微調（如果點擊位置仍有偏差，調整這裡）
VERTICAL_ADJUST = 675 
HORIZONTAL_ADJUST = -130
# ----------------

# 解決 Windows 縮放導致的座標偏移問題 (DPI Awareness)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()

is_running = True

def keyboard_monitor():
    global is_running
    while is_running:
        if keyboard.is_pressed("5"):
            print("\n[停止] 程序結束")
            is_running = False
            os._exit(0)
        sleep(0.05)

class CalibrationBot:
    def __init__(self):
        self.steps = ["1.png", "2.png", "3.png",
                      "4.png", "5.png", "6.png",
                      "7.png", "8.png"]
        self.main_loop()

    def locate_and_click(self, template_path, threshold=0.8):
        if not os.path.exists(template_path): 
            print(f"找不到圖片檔案: {template_path}")
            return False

        with mss.mss() as sct:
            # 獲取指定螢幕的範圍
            try:
                monitor = sct.monitors[TARGET_MONITOR_INDEX]
            except IndexError:
                print(f"錯誤: 找不到索引為 {TARGET_MONITOR_INDEX} 的螢幕")
                return False

            # 僅擷取副螢幕畫面
            sct_img = sct.grab(monitor)
            
            # 轉換為 OpenCV 格式
            screen_bgr = cv2.cvtColor(np.array(sct_img), cv2.COLOR_BGRA2BGR)
            template = cv2.imread(template_path)
            if template is None: return False
            h, w = template.shape[:2]

            # 模板匹配
            res = cv2.matchTemplate(screen_bgr, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

            if max_val >= threshold:
                # --- 核心座標轉換邏輯 ---
                # max_loc 是在「截圖內」的相對位置
                # 我們必須加上該螢幕在系統中的起始座標 (monitor["left"] 和 monitor["top"])
                
                target_x = monitor["left"] + max_loc[0] + (w // 2) + HORIZONTAL_ADJUST
                target_y = monitor["top"] + max_loc[1] + (h // 2) + VERTICAL_ADJUST
                
                print(f"找到 {template_path} (信心值: {max_val:.2f})")
                print(f"副螢幕起始點: ({monitor['left']}, {monitor['top']}) | 最終點擊點: ({target_x}, {target_y})")
                
                # 執行移動與點擊
                pyautogui.moveTo(target_x, target_y, duration=0.1)
                pyautogui.click()
                sleep(0.5)
                return True
        return False

    def reload_sequence(self):
        print("執行 Reload 序列...")
        # Reload 邏輯同樣會調用 locate_and_click，所以會自動切換到副螢幕
        if self.locate_and_click("mypage.png", 0.9):
            sleep(0.5)
            for _ in range(9):
                pyautogui.press("down")
                sleep(0.1)
            self.locate_and_click("reload1.png", 0.9)
            sleep(1.5)

    def main_loop(self):
        print(f"啟動腳本，目標螢幕索引: {TARGET_MONITOR_INDEX}")
        while is_running:
            idx = 0
            while idx < len(self.steps):
                if not is_running: break
                target = self.steps[idx]
                found = False
                
                # 嘗試尋找圖片，最多嘗試 10 次
                for _ in range(10):
                    if not is_running: break
                    if self.locate_and_click(target):
                        found = True
                        break
                    sleep(0.3)
                
                if found:
                    idx += 1
                else:
                    print(f"找不到 {target}，執行 Reload...")
                    self.reload_sequence()
                    break

if __name__ == "__main__":
    # 啟動鍵盤監控線程
    threading.Thread(target=keyboard_monitor, daemon=True).start()
    try:
        CalibrationBot()
    except Exception as e:
        print(f"發生非預期錯誤: {e}")