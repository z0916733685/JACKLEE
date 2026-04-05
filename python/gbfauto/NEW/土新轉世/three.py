import cv2
import numpy as np
import mss
import pyautogui
import keyboard
import threading
import os
import ctypes
import ddddocr
from time import sleep

# --- 環境設定 ---
# 程式會自動在所有螢幕搜尋此圖來定位
CALIBRATION_ANCHOR = "lockon.png" 
DEFAULT_THRESHOLD = 0.7

TARGET_MONITOR_INDEX = 2

# 自動對準後，x 和 y 補償通常設為 0 即可。
# 只有當圖片的「視覺中心」不是「點擊中心」時才需要微調。
STEP_CONFIG = {
    "1.png": {"x": 0, "y": 0, "th": 0.8},               # --- 步驟 ---
    "2.png": {"x": 0, "y": 0, "th": 0.7},
    "3.png": {"x": 0, "y": 0, "th": 0.7},
    "4.png": {"x": 0, "y": 0, "th": 0.7},
    "playin.png": {"x": 0, "y": 0, "th": 0.7},
    "5.png": {"x": 0, "y": 0, "th": 0.7},
    "6.png": {"x": 0, "y": 0, "th": 0.7},
    "7.png": {"x": 0, "y": 0, "th": 0.85},              # --- 步驟 ---
    "mypage.png": {"x": 0, "y": 0, "th": 0.7},          # --- 重整 ---
    "desk.png": {"x": 0, "y": 0, "th": 0.7},
    "reload1.png": {"x": 0, "y": 0, "th": 0.7},
    "reload2.png": {"x": 0, "y": 0, "th": 0.7},
    "reload3.png": {"x": 0, "y": 0, "th": 0.6},         # --- 重整 ---
    "classup.png": {"x": 0, "y": 0, "th": 0.7},         # --- 升級 ---
    "lockon.png": {"x": 0, "y": 0, "th": 0.7},          # --- 鎖定主副螢幕 ---
    "check.png": {"x": 0, "y": 0, "th": 0.7},           # --- 驗證碼偵測 ---
    "takein.png": {"x": 0, "y": 0, "th": 0.65},          # --- 驗證碼輸入框 ---
    "takeenter.png": {"x": 0, "y": 0, "th": 0.65},       # --- 送信按鈕 ---
    "otherok.png": {"x": 0, "y": 0, "th": 0.95},
    "otherclose.png": {"x": 0, "y": 0, "th": 0.7},
}

DEFAULT_CONFIG = {"x": 0, "y": 0, "th": 0.85}

# --- 強制 Windows 使用原始像素座標 (解決 4K/2K 縮放問題) ---
try:
    # 嘗試使用最高等級的 DPI 感知 (Per Monitor v2)
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        # 適用於較舊版本 Windows
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

is_running = True

def keyboard_monitor():
    global is_running
    while is_running:
        if keyboard.is_pressed("5"):
            print("\n[緊急停止] 使用者按下 5，程式結束。")
            is_running = False
            os._exit(0)
        sleep(0.05)

class GBFBot:
    def __init__(self):        
        self.steps = [
            "1.png", "2.png", "3.png",
            "4.png", "playin.png", "5.png", "6.png",
            "7.png"
        ]
        self.ocr = ddddocr.DdddOcr(show_ad=False)
        # 預加載圖片以提升性能
        self.templates = {}
        for img_name in self.steps + ["mypage.png", "desk.png", "reload1.png", "reload2.png", "reload3.png", "lockon.png", "check.png", "takein.png", "takeenter.png", "otherok.png", "otherclose.png"]:
            if os.path.exists(img_name):
                self.templates[img_name] = cv2.imread(img_name)
                
        self.target_monitor = None
        print(f">>> 偵測到多螢幕環境")
        print(">>> 正在自動尋找遊戲所在的螢幕...")
        
        if self.auto_calibrate():
            m = self.target_monitor
            print(f">>> 校準成功！")
            print(f">>> 鎖定區域: 左={m['left']}, 上={m['top']}, 寬={m['width']}, 高={m['height']}")
            self.main_loop()
        else:
            print(">>> [錯誤] 在任何螢幕都找不到 'lockon.png'。")
            print(">>> 請確保遊戲視窗在副螢幕顯示，且 menu 沒被遮擋。")

    def auto_calibrate(self):
        """遍歷所有螢幕尋找遊戲；若找不到，則強制使用指定的副螢幕。"""
        with mss.mss() as sct:
            template = cv2.imread(CALIBRATION_ANCHOR)
            if template is None:
                print(f"錯誤：找不到檔案 {CALIBRATION_ANCHOR}")
                return False

            print(">>> 正在搜尋遊戲視窗 (lockon.png)...")
            # 1. 嘗試自動偵測
            for i in range(1, len(sct.monitors)):
                monitor = sct.monitors[i]
                sct_img = sct.grab(monitor)
                img = cv2.cvtColor(np.array(sct_img), cv2.COLOR_BGRA2BGR)
                
                res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
                
                if max_val >= 0.6:
                    self.target_monitor = monitor
                    print(f">>> [成功] 在螢幕 {i} 找到遊戲。")
                    return True

            # 2. 保底機制：若沒找到，使用設定的副螢幕
            print(f">>> [提醒] 找不到 {CALIBRATION_ANCHOR}，將強制使用副螢幕 (索引: {TARGET_MONITOR_INDEX})。")
            try:
                self.target_monitor = sct.monitors[TARGET_MONITOR_INDEX]
                return True
            except IndexError:
                print(f">>> [錯誤] 找不到預設的副螢幕索引 {TARGET_MONITOR_INDEX}。")
                return False
    
    def get_screen_data(self):
        """輔助方法：統一獲取當前鎖定螢幕的影像數據"""
        if self.target_monitor is None:
            return None, None
            
        with mss.mss() as sct:
            sct_img = sct.grab(self.target_monitor)
            img = cv2.cvtColor(np.array(sct_img), cv2.COLOR_BGRA2BGR)
            return img, self.target_monitor

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
            target_img_2 = self.steps[current_idx] # 獲取原本當前步驟要找的圖
            print(f"\n[救援] 進入 60 秒監控：嘗試點擊其餘步驟或等待 {target_img_2}...")
            
            start_time_2 = time.time()
            while is_running:
                elapsed_2 = time.time() - start_time_2
                if elapsed_2 > 60:
                    print(f"\n[超時] 60 秒已到，其餘步驟與 {target_img_2} 均未成功，執行重整。")
                    return "reload"

                # 嘗試 A：點擊 classup.png
                sleep(0.5)
                if self.locate_and_click("classup.png"):
                    print(f" -> [成功] 點擊 classup.png，繼續監控目標...")
                    # 點完 classup 後通常還是在找同一張目標圖，所以不直接 return，讓迴圈繼續
                    
                if self.locate_and_click("otherok.png"):
                    print(f" -> [成功] 點擊 otherok.png，繼續監控目標...")

                # 嘗試 B：檢查原本的目標圖 (下一步動作) 是否出現了
                if self.locate_and_click(target_img_2):
                    print(f" -> [成功] 偵測到目標 {target_img_2}，回到主流程。")
                    return "continue" # 告訴主程式可以進到下一標籤了

                print(f" -> [救援中] 剩餘 {int(60 - elapsed_2)}s | 搜尋 classup 或 {target_img_2}...", end="\r")
                sleep(0.5)

        return False
    
    def check_after_step(self):
        """第 7 步執行完後的特殊判斷：偵測到 otherclose.png 就點擊"""
        print("\n[判斷] 第 7 步完成，檢查是否有關閉視窗 (otherclose.png)...")
        # 嘗試偵測並點擊，這裡給予 3 次機會或短暫等待，增加穩定性
        found_target = False
        for _ in range(5):  # 給予約 1.5 秒的緩衝時間等待視窗彈出
            screen_img, _ = self.get_screen_data()
            if screen_img is not None:
                template = self.templates.get("otherclose.png")
                if template is not None:
                    res = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, _ = cv2.minMaxLoc(res)
                    if max_val >= 0.7:
                        found_target = True
                        break
            sleep(0.3)
        
        # 如果確認偵測到，才進入原本的點擊流程
        if found_target:
            print("[偵測] 發現關閉按鈕，準備執行點擊...")
            for _ in range(3):
                if self.locate_and_click("otherclose.png"):
                    print("[動作] 已成功點擊 otherclose.png。")
                    return # 點擊成功後直接結束此函式
                sleep(0.3)
        else:
            print("[跳過] 未偵測到 otherclose.png，繼續後續流程。")
        # 如果沒偵測到，函數結束，主程式會自然繼續下一步

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
            
    def handle_captcha(self, retry_count=0):
        """
        自動適應變形與縮放的驗證碼處理邏輯。
        使用多尺度匹配找出最吻合的視窗大小，並按比例裁切驗證碼。
        """
        global is_running
        
        # 限制最多執行兩次（第 0 次與 第 1 次），第三次則停止
        if retry_count >= 2:
            print(f"\n[嚴重錯誤] 已連續嘗試 {retry_count} 次辨識均未成功，為保安全停止程式。")
            is_running = False
            os._exit(0)
        
        print(f"\n[AI 啟動] 準備進行第 {retry_count + 1} 次驗證碼辨識...")
        
        screen_img, monitor_info = self.get_screen_data()
        if screen_img is None: return False
        
        # 重新定位 check.png 的精確像素座標
        template = self.templates.get("check.png")
        
        if template is None:
            if os.path.exists("check.png"):
                template = cv2.imread("check.png")
                self.templates["check.png"] = template
            else:
                print("[錯誤] 找不到 check.png 模板，跳過辨識。")
                return False
        
        # --- 多尺度偵測 (Multi-Scale Detection) ---
        best_val = 0
        best_loc = None
        best_scale = 1
        
        # 嘗試從 0.8 倍到 1.2 倍進行搜尋 (每 0.05 一跳)
        for scale in np.linspace(0.3, 2, 10):
            width = int(template.shape[1] * scale)
            height = int(template.shape[0] * scale)
            resized = cv2.resize(template, (width, height), interpolation=cv2.INTER_AREA)
            
            res = cv2.matchTemplate(screen_img, resized, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            
            if max_val > best_val:
                best_val = max_val
                best_loc = max_loc
                best_scale = scale
        
        # --- 判斷是否偵測成功 ---
        if best_val >= 0.7:
            print(f"[AI] 偵測成功 (信心度: {best_val:.2f}, 縮放比: {best_scale:.2f})")
            
            # 建立 debug 目錄
            debug_dir = "captcha_debug"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            # --- [優化] 精確的裁切坐標 (基於你的原圖) ---
            # 根據 best_loc (check.png 標題位置) 相對計算文字區域
            # 這些數值需要根據你的 `check.png` 的精確大小來微調，以下為預估值
            # 假設 check.png 是標題文字 "認証文字を入力してください。"
            
            crop_rel_x = int(90 * best_scale)   # 往右移一點
            crop_rel_y = int(165 * best_scale)   # 往下移到文字區
            crop_w = int(240 * best_scale)
            crop_h = int(110 * best_scale)

            c_x = best_loc[0] + crop_rel_x
            c_y = best_loc[1] + crop_rel_y
            
            # 裁切並預處理
            try:
                captcha_crop = screen_img[c_y:c_y+crop_h, c_x:c_x+crop_w]
                cv2.imwrite(f"{debug_dir}/1_raw_crop.png", captcha_crop)
                
                # --- [核心] 高級影像預處理 (反干擾線) ---
                # 1. 轉灰階
                gray = cv2.cvtColor(captcha_crop, cv2.COLOR_BGR2GRAY)
                
                # 2. 自適應二值化 (將背景變白，文字和線條變黑)
                # 使用較大的 block size (例如 21) 有助於處理大面積的背景
                binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                                cv2.THRESH_BINARY_INV, 21, 5)
                cv2.imwrite(f"{debug_dir}/2_binary.png", binary)
                
                # 3. 形態學操作：修復 (反干擾線的核心)
                # 建立一個水平和垂直的結構元素，嘗試保留文字的結構，去除斜線
                kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1)) # 水平
                kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5)) # 垂直
                
                # 先膨脹再腐蝕 (Closing)，嘗試填補文字內部的細微斷裂，使文字更連續
                # 這對去除細干擾線有效，但對粗斜線效果有限。
                processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_h, iterations=1)
                
                # 嘗試另一種策略：先開運算 (Opening) 去除細小雜點，再閉運算 (Closing) 連接文字
                processed = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_v, iterations=1)
                processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, np.ones((3,3)), iterations=1)
                
                cv2.imwrite(f"{debug_dir}/3_anti_line.png", processed)
                
                # 4. (選用) 形態學再加強：細化
                # 對處理後的圖片進行細化，有助於 OCR 辨識
                skeleton = cv2.ximgproc.thinning(processed, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
                cv2.imwrite(f"{debug_dir}/4_skeleton.png", skeleton)
                
                # 決定使用哪種處理結果送入 OCR (建議嘗試 processed 或 skeleton)
                final_for_ocr = processed 
                
                # --- 執行 OCR 辨識 ---
                _, img_encoded = cv2.imencode('.png', final_for_ocr)
                captcha_text = self.ocr.classification(img_encoded.tobytes())
                
                # 移除非字母數字字元並轉大寫 (通常驗證碼不分大小寫)
                captcha_text = "".join([c for c in captcha_text if c.isalnum()]).upper()
                print(f"[AI] 辨識結果 (修正後): {captcha_text}")

                # --- 計算輸入位置並執行操作 ---
                img_h, img_w = screen_img.shape[:2]
                scale_m_x = monitor_info["width"] / img_w
                scale_m_y = monitor_info["height"] / img_h
                
                # 輸入框中心相對座標
                input_rel_x = int(185 * best_scale)
                input_rel_y = int(400 * best_scale)
                input_abs_x = monitor_info["left"] + ((best_loc[0] + input_rel_x) * scale_m_x)
                input_abs_y = monitor_info["top"] + ((best_loc[1] + input_rel_y) * scale_m_y)

                # 點擊並輸入
                if self.locate_and_click("takein.png"):
                    sleep(0.5)
                    pyautogui.hotkey('ctrl', 'a')
                    pyautogui.press('backspace')
                    pyautogui.write(captcha_text)
                    print(f"[AI] 已輸入文字: {captcha_text}")
                else:
                    # 如果找不到 takein.png，才使用原本計算的備用座標
                    pyautogui.click(input_abs_x, input_abs_y)
                    sleep(0.5)
                    pyautogui.write(captcha_text)

                sleep(0.5)
                
                # --- 修改重點：取代 pyautogui.press('enter') ---
                print("[動作] 正在尋找並點擊送信按鈕 (takeenter.png)...")
                
                btn_found = False
                for _ in range(3):  # 嘗試找 3 次，增加容錯
                    if self.locate_and_click("takeenter.png"):
                        print("[成功] 已點擊送信按鈕。")
                        btn_found = True
                        break
                    sleep(0.5)
                
                if not btn_found:
                    print("[警告] 找不到送信按鈕 takeenter.png，驗證可能失敗。")
                
                print(f"[資訊] 驗證碼 [{captcha_text}] 已送出，等待 5 秒檢查結果...")
                sleep(5)
                
                # --- 二次安全檢查 ---
                if self.check_if_captcha_exists(template):
                    print(f"\n[警告] 驗證碼視窗未消失。嘗試重新辨識...")
                    # 遞迴呼叫自己，並將計數器 +1
                    return self.handle_captcha(retry_count = retry_count + 1) 
                else:
                    print("[成功] 驗證碼已輸入。")
                    return True
                
            except Exception as e:
                print(f"[錯誤] 辨識過程發生異常: {e}")
        return False
    
    def check_if_captcha_exists(self, template):
        """輔助方法：再次檢查畫面上是否還有驗證碼視窗"""
        check_img, _ = self.get_screen_data()
        if check_img is None: return False
        
        # 簡單檢查當前縮放下的匹配度
        res = cv2.matchTemplate(check_img, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        return max_val >= 0.7

    def main_loop(self):
        while is_running:
            # --- 新增：每一輪開始前檢查驗證碼 ---
            if self.locate_and_click("check.png"):
                self.handle_captcha()
                continue # 完成後重新開始檢查流程
            idx = 0
            while idx < len(self.steps):
                if not is_running: break
                # 在每個小步驟搜尋前也檢查一下
                if self.locate_and_click("check.png"):
                    self.handle_captcha()
                
                target = self.steps[idx]
                print(f"進度: {idx+1}/{len(self.steps)} | 正在尋找: {target}      ", end="\r")

                found = False
                for _ in range(10):
                    if not is_running: break
                    if self.locate_and_click("check.png"):
                        self.handle_captcha()
                    if self.locate_and_click(target):
                        found = True
                        break
                    sleep(0.3)

                if found:
                    # 執行保留的額外動作
                    self.extra_actions(idx, True)
                    if target == "7.png":
                        self.check_after_step()
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
        GBFBot()
    except Exception as e:
        print(f"\n[崩潰] 錯誤訊息: {e}")
        