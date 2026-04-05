import cv2
import numpy as np
import mss
import pyautogui
import keyboard
import threading
import os
import ctypes
from time import sleep

# --- 強制開啟 DPI 感知，防止 Windows 縮放導致座標偏移 ---
try:
    # 適用於 Windows 8.1 以上
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    # 適用於較舊版本 Windows
    ctypes.windll.user32.SetProcessDPIAware()

# --- 進階校準區 ---
TARGET_MONITOR_INDEX = 2 

# 自動對準後，x 和 y 補償通常設為 0 即可。
# 只有當圖片的「視覺中心」不是「點擊中心」時才需要微調。
STEP_CONFIG = {
    "1.png": {"x": 0, "y": 0, "th": 0.8},
    "2.png": {"x": 0, "y": 0, "th": 0.8},
    "3.png": {"x": 0, "y": 0, "th": 0.8},
    "4.png": {"x": 0, "y": 0, "th": 0.8},
    "5.png": {"x": 0, "y": 0, "th": 0.8},
    "6.png": {"x": 0, "y": 0, "th": 0.8},
    "7.png": {"x": 0, "y": 0, "th": 0.8},
    "in.png": {"x": 0, "y": 0, "th": 0.8},
    "mypage.png": {"x": 0, "y": 0, "th": 0.8},
    "desk.png": {"x": 0, "y": 0, "th": 0.8},
    "reload1.png": {"x": 0, "y": 0, "th": 0.8},
    "reload2.png": {"x": 0, "y": 0, "th": 0.8},
    "reload3.png": {"x": 0, "y": 0, "th": 0.8},
    "classup.png": {"x": 0, "y": 0, "th": 0.8},
}

DEFAULT_CONFIG = {"x": 0, "y": 0, "th": 0.85}

is_running = True

def keyboard_monitor():
    global is_running
    while is_running:
        if keyboard.is_pressed("5"):
            print("\n[緊急停止] 使用者按下 5，程式結束。")
            is_running = False
            os._exit(0)
        sleep(0.05)

class CalibrationBot:
    def __init__(self):
        self.steps = [
            "1.png", "2.png", "3.png", "4.png", "5.png", "6.png", "7.png",
            "1.png", "2.png", "3.png", "4.png", "5.png", "6.png", "7.png"
            
        ]
        # 預加載圖片以提升性能
        self.templates = {}
        for img_name in self.steps + ["mypage.png", "desk.png", "reload1.png", "reload2.png", "reload3.png"]:
            if os.path.exists(img_name):
                self.templates[img_name] = cv2.imread(img_name)
        
        print(f">>> 自動校準模式啟動 | 副螢幕索引: {TARGET_MONITOR_INDEX}")
        self.main_loop()

    def get_screen_data(self):
        with mss.mss() as sct:
            try:
                # 取得目標螢幕的資訊 (包含 left, top, width, height)
                monitor = sct.monitors[TARGET_MONITOR_INDEX]
                sct_img = sct.grab(monitor)
                # 轉為 OpenCV BGR 格式
                img = cv2.cvtColor(np.array(sct_img), cv2.COLOR_BGRA2BGR)
                return img, monitor
            except IndexError:
                print(f"錯誤: 找不到螢幕索引 {TARGET_MONITOR_INDEX}")
                return None, None

    def locate_and_click(self, template_path, threshold_override=None):
        template = self.templates.get(template_path)
        if template is None:
            if os.path.exists(template_path):
                template = cv2.imread(template_path)
                self.templates[template_path] = template
            else:
                return False

        cfg = STEP_CONFIG.get(template_path, DEFAULT_CONFIG)
        final_th = threshold_override if threshold_override else cfg["th"]

        screen_img, monitor_info = self.get_screen_data()
        if screen_img is None: return False

        # 執行模板匹配
        res = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if max_val >= final_th:
            h, w = template.shape[:2]
            
            # 1. 計算在截圖中的中心點像素位置
            center_x_in_img = max_loc[0] + (w // 2) + cfg["x"]
            center_y_in_img = max_loc[1] + (h // 2) + cfg["y"]

            # 2. DPI 縮放校正：
            # 截圖的像素寬度(img.shape[1])與螢幕邏輯寬度(monitor_info["width"])可能不一致
            img_h, img_w = screen_img.shape[:2]
            scale_x = monitor_info["width"] / img_w
            scale_y = monitor_info["height"] / img_h

            # 3. 轉換為全域座標
            abs_x = monitor_info["left"] + (center_x_in_img * scale_x)
            abs_y = monitor_info["top"] + (center_y_in_img * scale_y)
            
            # 執行移動與點擊
            pyautogui.moveTo(abs_x, abs_y, duration=0.1)
            pyautogui.click()
            
            print(f"[成功] {template_path} (信心:{max_val:.2f}) | 座標:({int(abs_x)},{int(abs_y)})")
            sleep(0.1)
            return True
        return False

    def extra_actions(self, current_idx, found_status):
        import time
        """保留的額外步驟空間，你可以在這裡撰寫偵測到特定圖片後的自定義邏輯"""
        
        if current_idx == 4 and not found_status:
            print("\n[偵測] 步驟失敗，準備跳過下一個動作")
            return "skip"  # 回傳 skip 表示要跳過
        
        if current_idx >= 5 and not found_status:
            target_img = self.steps[current_idx] # 獲取原本當前步驟要找的圖
            print(f"\n[救援] 進入 60 秒監控：嘗試點擊 classup.png 或等待 {target_img}...")
            
            start_time = time.time()
            while is_running:
                elapsed = time.time() - start_time
                if elapsed > 60:
                    print(f"\n[超時] 60 秒已到，classup 與 {target_img} 均未成功，執行重整。")
                    return "reload"

                # 嘗試 A：點擊 classup.png
                if self.locate_and_click("classup.png"):
                    print(f" -> [成功] 點擊 classup.png，繼續監控目標...")
                    # 點完 classup 後通常還是在找同一張目標圖，所以不直接 return，讓迴圈繼續

                # 嘗試 B：檢查原本的目標圖 (下一步動作) 是否出現了
                if self.locate_and_click(target_img):
                    print(f" -> [成功] 偵測到目標 {target_img}，回到主流程。")
                    return "continue" # 告訴主程式可以進到下一標籤了

                print(f" -> [救援中] 剩餘 {int(60 - elapsed)}s | 搜尋 classup 或 {target_img}...", end="\r")
                sleep(0.5)

        return False

    def reload_sequence(self):
        print("\n[資訊] 執行重整序列...")
        reload_steps = ["mypage.png", "desk.png", "reload1.png", "reload2.png", "reload3.png"]
        
        for step_img in reload_steps:
            if not is_running: break
            found = False
            for _ in range(5):
                if self.locate_and_click(step_img):
                    print(f" -> 已點擊 {step_img}")
                    sleep(1.2)
                    found = True
                    break
                sleep(0.5) 
            
            if not found:
                print(f" [警告] 重整中斷：找不到 {step_img}")
                break

    def main_loop(self):
        while is_running:
            idx = 0
            while idx < len(self.steps):
                if not is_running: break
                target = self.steps[idx]
                print(f"進度: {idx+1}/{len(self.steps)} | 正在尋找: {target}      ", end="\r")

                found = False
                for _ in range(25):
                    if not is_running: break
                    if self.locate_and_click(target):
                        found = True
                        break
                    sleep(0.3)

                if found:
                    # 執行保留的額外動作
                    self.extra_actions(idx, True)
                    idx += 1
                else:
                    # 沒找到原本的圖，啟動救援機制
                    status = self.extra_actions(idx, False)
                    
                    if status == "skip":
                        idx += 1 # 跳過目前的和下一個
                    elif status == "continue":
                        idx += 1 # 救援模式中已經點到目標了，直接去下一個
                    elif status == "reload" or status is False:
                        self.reload_sequence()
                        break # 跳出內層迴圈，從頭開始

if __name__ == "__main__":
    # 啟動鍵盤監控線程
    threading.Thread(target=keyboard_monitor, daemon=True).start()
    try:
        CalibrationBot()
    except Exception as e:
        print(f"\n[崩潰] 錯誤訊息: {e}")