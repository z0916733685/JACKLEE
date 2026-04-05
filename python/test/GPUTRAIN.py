import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torch.backends.cudnn as cudnn
from torch.utils.data import Dataset, DataLoader
import cv2
import numpy as np
import random
import os
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm
from typing import List, Tuple, Dict

# =================================================================
# [正規化階段 1] 核心硬體配置與環境封裝
# =================================================================

class ModelConfig:
    """
    集中的配置管理類別，針對 4070 Ti Super (16GB VRAM) 
    與 Ryzen 9800X3D (8C/16T) 進行參數標準化。
    """
    # 設備檢測與優化
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # 40 系列專屬優化：TF32 矩陣運算加速
    ALLOW_TF32 = True
    CUDNN_BENCHMARK = True
    
    # 影像規格
    IMAGE_WIDTH = 200
    IMAGE_HEIGHT = 60
    CHAR_LENGTH = 6
    
    # 字符集定義 (第一位必須為 CTC Blank '-')
    CHARS = "-" + "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    NUM_CLASSES = len(CHARS)
    CHAR_TO_IDX = {char: i for i, char in enumerate(CHARS)}
    IDX_TO_CHAR = {i: char for i, char in enumerate(CHARS)}
    
    # 訓練超參數 (針對 16GB 大顯存優化)
    BATCH_SIZE = 128 
    MAX_EPOCHS = 1000
    INITIAL_LR = 1e-3
    STN_LR_SCALER = 0.1  # STN 的學習率通常需要稍低於主網絡
    # 熱身設定
    WARMUP_EPOCHS = 50
    
    font_path = r"F:\AI\MyProject\python\test\Fonts"
    
    # 權重管理
    WEIGHT_PATHS = {
        "best": r"F:\AI\MyProject\python\test\model_best.pth",
        "medium": "model_medium_distort.pth",
        "base": "model_base_structure.pth"
    }

    @classmethod
    def apply_hardware_optimization(cls):
        """執行硬體層級的性能調優"""
        if torch.cuda.is_available():
            torch.backends.cuda.matmul.allow_tf32 = cls.ALLOW_TF32
            torch.backends.cudnn.allow_tf32 = cls.ALLOW_TF32
            cudnn.benchmark = cls.CUDNN_BENCHMARK
            print(f">>> [硬體優化] 4070 Ti Super TF32 模式: {cls.ALLOW_TF32}")
            print(f">>> [硬體優化] CUDNN Benchmark: {cls.CUDNN_BENCHMARK}")
            
    # 新增輸出資料夾路徑
    OUTPUT_DIR = r"F:\AI\MyProject\python\test\training_outputs"
            
    @classmethod
    def prepare_folders(cls):
        """確保輸出資料夾存在"""
        if not os.path.exists(cls.OUTPUT_DIR):
            os.makedirs(cls.OUTPUT_DIR)
            print(f">>> [系統] 已建立輸出資料夾: {cls.OUTPUT_DIR}")

# =================================================================
# [新增] 實時趨勢繪圖引擎
# =================================================================

class RealTimePlotter:
    """
    使用 OpenCV 繪製訓練趨勢圖，完全替代 Matplotlib 以避免 GIL 崩潰。
    針對 2K/4K 螢幕優化，支援自動定位。
    """
    def __init__(self):
        self.win_title = "Training Metrics (OpenCV)"
        self.width, self.height = 2000, 1200
        self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.window_moved = False
        
        # 初始建立視窗
        cv2.namedWindow(self.win_title, cv2.WINDOW_NORMAL)
        # [選配] 強制設定初始位置 (例如在你的 4K 主螢幕中央或 2K 副螢幕)
        cv2.moveWindow(self.win_title, -1850, 900)
        cv2.resizeWindow(self.win_title, 1200, 800)         # 設定初始寬 1200, 高 800 (可自行調整)
        # 建立一個空白黑色畫面作為初始顯示
        self.blank_canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        cv2.imshow(self.win_title, self.blank_canvas)
        cv2.waitKey(1) # 刷新視窗狀態

    def _normalize(self, data, min_val, max_val, height):
        """將數據映射到畫布高度"""
        # 增加邊距感，讓線條不要貼齊邊框
        if not data: return []
        range_val = max_val - min_val
        if range_val == 0: range_val = 1e-6
        # 映射至畫布 15% ~ 85% 的高度區間，避免貼邊
        return [int(height - (v - min_val) / range_val * (height * 0.7) - (height * 0.15)) for v in data]

    def update(self, history: dict):
        import threading
        # 核心防護：只在主執行緒繪圖
        if threading.current_thread() is not threading.main_thread():
            return
        
        # 重置畫布
        self.canvas.fill(20) # 背景改為深藍黑漸層感
        h, w = self.height, self.width
        pad = 80 # 邊距
            
        # 2. 視窗初始化（確保一進入函數就先建立視窗，不論有沒有數據）
        if not hasattr(self, 'window_moved') or not self.window_moved:
            cv2.resizeWindow(self.win_title, 1200, 800)         # 設定初始寬 1200, 高 800 (可自行調整)
            cv2.moveWindow(self.win_title, -1850, 900) 
            self.window_moved = True
        
        epochs = history.get('epochs', [])
        num_points = len(epochs)
        
        # --- 分歧點：如果數據點不足，顯示等待畫面並直接顯示視窗 ---
        if num_points < 2:
            font = cv2.FONT_HERSHEY_DUPLEX
            loading_text = "Initializing Monitor: Waiting for Epoch 1..."
            font_scale = 1.5
            thickness = 3
            # 1. 計算文字的寬度與高度 (w_text, h_text)
            # baseline 是文字基線，通常略低於文字主體
            (w_text, h_text), baseline = cv2.getTextSize(loading_text, font, font_scale, thickness)
            # 2. 計算置中的起始座標 (x, y)
            # OpenCV 的文字座標是左下角，所以 y 座標要加上高度
            text_x = (w - w_text) // 2
            text_y = (h + h_text) // 2
            cv2.putText(self.canvas, loading_text, (text_x, text_y), font, font_scale, (180, 180, 180), thickness, cv2.LINE_AA)
            cv2.imshow(self.win_title, self.canvas)
            cv2.waitKey(1) # 這行最重要，讓視窗能接收作業系統的移動指令
            return 
        # -----------------------------------------------------
        
        # 畫出主要座標軸 (白色)
        # 起點 (pad, pad) 到 終點 (pad, height-pad) 為 Y 軸
        cv2.line(self.canvas, (pad, pad), (pad, self.height-pad), (255, 255, 255), 2) 
        # X 軸
        cv2.line(self.canvas, (pad, self.height-pad), (self.width-pad, self.height-pad), (255, 255, 255), 2)

        # 3. 數據平滑處理 (選配：如果線條太抖動可以開)
        loss_data = history['loss']
        lr_data = history.get('lr', [])
        lr_events = history.get('lr_events', [])
        char_acc = history['char_acc']
        full_acc = history['full_acc']
        
        x_coords = [int(pad + (i / (num_points - 1)) * (w - 2 * pad)) for i in range(num_points)]
        
        y_lr = None
        if lr_data:
            lr_log = [np.log10(max(lr, 1e-12)) for lr in lr_data]
            y_lr = self._normalize(lr_log, min(lr_log), max(lr_log), h)

        y_loss = self._normalize(loss_data, min(loss_data), max(loss_data), h)
        y_char = self._normalize(char_acc, 0, 100, h)
        y_full = self._normalize(full_acc, 0, 100, h)
        
        # 4. 繪製背景網格與標註 (0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100%)
        for val in [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
            # 映射 ACC 數值到畫布高度
            y_grid = int(h - (val / 100 * (h * 0.7) + (h * 0.15)))
            cv2.line(self.canvas, (pad, y_grid), (w-pad, y_grid), (45, 45, 45), 1)
            cv2.putText(self.canvas, f"{val}%", (10, y_grid+5), cv2.FONT_HERSHEY_PLAIN, 1.5, (200, 200, 200), 3)
            
        # UI 面板美化
        # 在頂部加一個半透明的橫條放數據
        overlay = self.canvas.copy()
        cv2.rectangle(overlay, (0, 0), (w, 80), (40, 40, 40), -1)
        cv2.addWeighted(overlay, 0.6, self.canvas, 0.4, 0, self.canvas)

        # 繪製抗鋸齒線條 (LINE_AA)
        for i in range(num_points - 1):
            p1_x, p2_x = x_coords[i], x_coords[i+1]

            # (A) Loss - 紅色 (雙層線條營造發光感)
            cv2.line(self.canvas, (p1_x, y_loss[i]), (p2_x, y_loss[i+1]), (50, 50, 180), 2, cv2.LINE_AA)
            cv2.line(self.canvas, (p1_x, y_loss[i]), (p2_x, y_loss[i+1]), (80, 80, 255), 4, cv2.LINE_AA)

            # (B) Char ACC - 亮綠色 (細線，代表字元級細節)
            cv2.line(self.canvas, (p1_x, y_char[i]), (p2_x, y_char[i+1]), (100, 255, 100), 2, cv2.LINE_AA)

            # (C) Full ACC - 亮橘色 (粗線，代表最終目標)
            cv2.line(self.canvas, (p1_x, y_full[i]), (p2_x, y_full[i+1]), (0, 140, 255), 5, cv2.LINE_AA)
            
            # LR 曲線 - 藍色
            if lr_data:
                cv2.line(self.canvas,(p1_x, y_lr[i]),(p2_x, y_lr[i+1]),(255, 180, 0), 2, cv2.LINE_AA)

        # 顯示即時數值
        font = cv2.FONT_HERSHEY_DUPLEX
        font_scale = 1.2
        white = (255, 255, 255)
        
        # 1. 左邊：LOSS 座標軸標籤
        cv2.putText(self.canvas, "LOSS", (5, pad - 10), font, font_scale, white, 3)
        
        # 2. 下面：EPOCH 數量標籤
        cv2.putText(self.canvas, "EPOCH", (self.width // 2, self.height - 10), font, font_scale, white, 3)
        
        # 3. 右邊：正確率 % 標籤 (對應 Full/Char Acc)
        cv2.putText(self.canvas, "ACC (%)", (self.width - pad + 5, pad - 10), font, font_scale, white, 3)
        
        # 右邊：LR 軸標籤
        cv2.putText(self.canvas, "LR (log10)", (self.width - pad + 5, self.height - pad + 40),cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 200, 0), 2)
        
        # 4. 數值標記 (範例：0, 50, 100)
        labels = ["100%", "87.5%", "75%", "62.5%", "50%", "37.5%", "25%", "12.5%", "0%"]
        # 調整起始高度避開頂部文字，並計算剩餘可用高度
        top_margin = pad + 40  # 往下移 40 像素避開 ACC 標頭
        bottom_margin = pad
        available_height = self.height - top_margin - bottom_margin
        
        # 4. 數值標記 (範例：0, 50, 100)
        for i, val in enumerate(labels):
            # 使用 len(labels)-1 (即 8) 來均分間距，確保 9 個值都落在畫布內
            y_pos = top_margin + (i * available_height // (len(labels) - 1))
            
            # x 座標往左修正 (減去約 80-100 像素)，確保文字不會被右側邊緣卡掉
            # 調整 fontScale 為 0.7 讓畫面更精緻
            cv2.putText(self.canvas, val, (self.width - 95, y_pos), font, 0.7, white, 1, cv2.LINE_AA)
        
        if lr_data:
            for event_epoch, event_lr in lr_events:
                if event_epoch in epochs:
                    idx = epochs.index(event_epoch)
                    x = x_coords[idx]
                    y = y_lr[idx]

                    # 畫垂直線
                    cv2.line(self.canvas,
                            (x, pad),
                            (x, self.height - pad),
                            (100, 100, 255), 1)

                    # 畫箭頭
                    cv2.putText(self.canvas,
                                "LR↓",
                                (x - 20, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.5,
                                (0, 0, 255),
                                2)
        
        # Loss (紅)
        cv2.putText(self.canvas, f"LOSS: {loss_data[-1]:.4f}", (pad, 50), font, 1.0, (100, 100, 255), 2, cv2.LINE_AA)
        # Char ACC (綠)
        cv2.putText(self.canvas, f"CHAR ACC: {char_acc[-1]:.2f}%", (w//3 + 50, 50), font, 1.0, (120, 255, 120), 2, cv2.LINE_AA)
        # Full ACC (橘)
        cv2.putText(self.canvas, f"FULL ACC: {full_acc[-1]:.2f}%", (w*2//3 - 50, 50), font, 1.0, (0, 180, 255), 2, cv2.LINE_AA)
        # Epoch
        cv2.putText(self.canvas, f"EPOCH: {epochs[-1]}", (w - 250, 50), font, 1.0, (220, 220, 220), 2, cv2.LINE_AA)
        
        if lr_data:
            cv2.putText(self.canvas,f"LR: {lr_data[-1]:.2e}",(w - 250, 80),cv2.FONT_HERSHEY_DUPLEX,1.0,(255, 200, 0),2,cv2.LINE_AA)
        
        cv2.imshow(self.win_title, self.canvas)
        cv2.waitKey(1)
        
        return self.canvas

    def save(self, filename="training_trend.png"):
        """使用 OpenCV 直接儲存畫布內容"""
        # 確保 ModelConfig.OUTPUT_DIR 存在
        if not os.path.exists(ModelConfig.OUTPUT_DIR):
            os.makedirs(ModelConfig.OUTPUT_DIR)
        full_path = os.path.join(ModelConfig.OUTPUT_DIR, filename)
        cv2.imwrite(full_path, self.canvas)
        print(f">>> [存檔] 趨勢圖已儲存至: {full_path}")

class LRPlotter:
    """
    專門顯示 Learning Rate 曲線（log scale）
    支援：
    - 即時更新
    - LR下降事件標記
    - 自動縮放
    """

    def __init__(self):
        self.win_title = "Learning Rate Monitor"
        self.width, self.height = 1400, 800
        self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        cv2.namedWindow(self.win_title, cv2.WINDOW_NORMAL)
        cv2.moveWindow(self.win_title, -2500, 900)
        cv2.resizeWindow(self.win_title, 600, 400)
        # 建立一個空白黑色畫面作為初始顯示
        self.blank_canvas_2 = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        cv2.imshow(self.win_title, self.blank_canvas_2)
        cv2.waitKey(1) # 刷新視窗狀態

    def _normalize(self, data, h):
        if not data:
            return []

        min_v, max_v = min(data), max(data)
        if max_v - min_v == 0:
            max_v += 1e-6

        return [
            int(h - (v - min_v) / (max_v - min_v) * (h * 0.7) - (h * 0.15))
            for v in data
        ]

    def update(self, history: dict):
        import threading
        if threading.current_thread() is not threading.main_thread():
            return

        self.canvas.fill(20)

        lr_data = history.get("lr", [])
        epochs = history.get("epochs", [])
        lr_events = history.get("lr_events", [])

        if len(lr_data) < 2:
            cv2.imshow(self.win_title, self.canvas)
            cv2.waitKey(1)
            return

        # --- 使用 log10 ---
        lr_log = [np.log10(max(lr, 1e-12)) for lr in lr_data]

        h, w = self.height, self.width
        pad = 80

        # X 軸
        x_coords = [
            int(pad + (i / (len(lr_log) - 1)) * (w - 2 * pad))
            for i in range(len(lr_log))
        ]

        # Y 軸
        y_coords = self._normalize(lr_log, h)

        # --- 畫座標軸 ---
        cv2.line(self.canvas, (pad, pad), (pad, h - pad), (255, 255, 255), 2)
        cv2.line(self.canvas, (pad, h - pad), (w - pad, h - pad), (255, 255, 255), 2)

        # --- 畫網格 ---
        for i in range(6):
            y = int(pad + i * (h - 2 * pad) / 5)
            cv2.line(self.canvas, (pad, y), (w - pad, y), (50, 50, 50), 1)

        # --- 畫 LR 曲線 ---
        for i in range(len(x_coords) - 1):
            cv2.line(
                self.canvas,
                (x_coords[i], y_coords[i]),
                (x_coords[i + 1], y_coords[i + 1]),
                (255, 200, 0),
                3,
                cv2.LINE_AA,
            )

        # --- LR 下降事件標記 ---
        for event_epoch, event_lr in lr_events:
            if event_epoch in epochs:
                idx = epochs.index(event_epoch)
                x = x_coords[idx]
                y = y_coords[idx]

                # 垂直線
                cv2.line(self.canvas, (x, pad), (x, h - pad), (100, 100, 255), 1)

                # 圓點
                cv2.circle(self.canvas, (x, y), 5, (0, 0, 255), -1)

                # 標記文字
                cv2.putText(
                    self.canvas,
                    "LR↓",
                    (x - 20, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 255),
                    2,
                )

        # --- 標題 ---
        cv2.putText(
            self.canvas,
            "Learning Rate (log10)",
            (pad, 40),
            cv2.FONT_HERSHEY_DUPLEX,
            1.0,
            (255, 200, 0),
            2,
        )

        # --- 當前 LR ---
        cv2.putText(
            self.canvas,
            f"Current LR: {lr_data[-1]:.2e}",
            (w - 350, 40),
            cv2.FONT_HERSHEY_DUPLEX,
            0.9,
            (255, 200, 0),
            2,
        )

        # --- Epoch ---
        cv2.putText(
            self.canvas,
            f"Epoch: {epochs[-1]}",
            (w - 350, 80),
            cv2.FONT_HERSHEY_DUPLEX,
            0.9,
            (220, 220, 220),
            2,
        )

        cv2.imshow(self.win_title, self.canvas)
        cv2.waitKey(1)

    def save(self, filename="lr_curve.png"):
        if not os.path.exists("training_outputs"):
            os.makedirs("training_outputs")

        path = os.path.join("training_outputs", filename)
        cv2.imwrite(path, self.canvas)
        print(f">>> [存檔] LR 曲線已儲存至: {path}")

# =================================================================
# [正規化階段 2] 高階驗證碼生成組件 (CaptchaGenerator)
# =================================================================

class StandardCaptchaGenerator:
    """
    正規化的數據生成器，封裝了 PIL 繪圖與 OpenCV 影像處理邏輯。
    所有的隨機參數與難度控制皆在此類別中閉環執行。
    """
    def __init__(self, font_dir: str = ModelConfig.font_path):
        self.width = ModelConfig.IMAGE_WIDTH
        self.height = ModelConfig.IMAGE_HEIGHT
        self.fonts_pool = self._load_fonts(font_dir)
        
    def _load_fonts(self, font_dir: str) -> List[ImageFont.FreeTypeFont]:
        """只載入字型路徑，不載入字型物件"""
        pool = []
        if not os.path.exists(font_dir):
            print(f">>> [警告] 未找到字型資料夾 {font_dir}，使用系統預設。")
            return [ImageFont.load_default()]
        
        font_files = [
            os.path.join(font_dir, f)
            for f in os.listdir(font_dir)
            if f.lower().endswith(('.ttf', '.otf'))
        ]
        
        return font_files
    
    def get_random_font(self) -> ImageFont.FreeTypeFont:
        """每次用的時候才隨機載入"""
        if not self.fonts_pool:
            return ImageFont.load_default()

        font_path = random.choice(self.fonts_pool)
        font_size = int(self.height * random.randint(5, 9) / 10)

        return ImageFont.truetype(font_path, font_size)

    def _apply_sine_warp(self, img_np: np.ndarray, difficulty: float) -> np.ndarray:
        """
        利用正弦波公式對影像進行空間幾何形變。
        這是模擬真實 CAPTCHA 扭曲的核心邏輯。
        """
        rows, cols = img_np.shape[:2]
        x_map, y_map = np.meshgrid(np.arange(cols), np.arange(rows))

        # --- 水平扭曲 (振幅加強) ---
        # 根據難度係數動態計算振幅 (Amplitude) 與週期 (Period)
        # 將最高振幅提升到 12-15 像素，這會讓字體產生明顯的斷層感
        amp_x = random.uniform(3.0, 5.0 + 10.0 * difficulty)
        period_x = random.uniform(25, 45)
        
        # --- 垂直扭曲 (新增) ---
        # 讓文字不只左右擺動，還會上下起伏
        amp_y = random.uniform(2.0, 4.0 * difficulty)
        period_y = random.uniform(30, 60)

        # 計算偏移量
        x_offsets = (amp_x * np.sin(2 * np.pi * y_map / period_x)).astype(np.float32)
        y_offsets = (amp_y * np.cos(2 * np.pi * x_map / period_y)).astype(np.float32)

        x_map_warped = (x_map + x_offsets).astype(np.float32)
        y_map_warped = (y_map + y_offsets).astype(np.float32)

        # 使用 OpenCV 的 Remap 進行高效插值運算
        return cv2.remap(img_np, x_map_warped, y_map_warped, 
                        interpolation=cv2.INTER_CUBIC, # 改用 CUBIC 插值減少鋸齒
                        borderMode=cv2.BORDER_REPLICATE)
    
    def _add_geometric_noise(self, img_np: np.ndarray, difficulty: float):
        """
        在影像中加入中空圓圈（像O）與中空方塊噪點
        強化版幾何噪點：增加深色中空圓圈與隨機線段，模擬字體筆畫
        """
        # 根據難度大幅增加數量 (從原本的 2~8 個增加到 5~15 個)
        num_shapes = random.randint(5, int(8 + 10 * difficulty))
        
        for _ in range(num_shapes):
            shape_type = random.choice(['circle', 'rect', 'ellipse'])
            
            # 隨機位置與大小 (適度縮放以符合字體比例)
            center = (random.randint(0, self.width), random.randint(0, self.height))
        
            # [核心強化] 讓圓圈大小與字體接近 (10~22 像素)
            size = random.randint(10, 22)
            
            # [核心強化] 顏色設為深色 (20-150)，與文字顏色 (0-100) 完全混淆
            color_val = random.randint(20, 150)
            color = (color_val, color_val, color_val)
            
            # 線條粗細：增加到 2-3 像素，讓「深色 O」更有存在感
            thickness = random.randint(1, 3)
            
            if shape_type == 'circle':
                cv2.circle(img_np, center, size, color, thickness)
            elif shape_type == 'ellipse':
                # 增加橢圓，更像受損的字元
                axes = (size, random.randint(5, 15))
                angle = random.randint(0, 180)
                cv2.ellipse(img_np, center, axes, angle, 0, 360, color, thickness)
            else:
                p2 = (center[0] + size, center[1] + random.randint(8, 20))
                cv2.rectangle(img_np, center, p2, color, thickness)
        
        return img_np
    
    def _generate_diverse_label(self, warmup: bool = False) -> str:
        """
        [新增] 標籤生成邏輯：warmup=True 時強制不出現重複字元
        """
        # 排除索引 0 的 CTC Blank (假設 ModelConfig.CHARS[0] 是 '-')
        chars_pool = list(ModelConfig.CHARS[1:]) 
        
        if warmup:
            # 熱身期：從字元池中「不放回」抽樣，確保 6 個字完全不同
            # 這能強制模型學習 6 個不同的特徵，防止它偷懶只認同一個字(如 QQQQQQ)
            selected = random.sample(chars_pool, k=ModelConfig.CHAR_LENGTH)
        else:
            # 正常期：恢復隨機抽樣（允許重複）
            selected = random.choices(chars_pool, k=ModelConfig.CHAR_LENGTH)
            
        return "".join(selected)
    
    def _generate_repeated_label(self):
        chars_pool = list(ModelConfig.CHARS[1:])
        mode = random.choice(["all_same", "pair_repeat", "partial_repeat"])

        if mode == "all_same":
            c = random.choice(chars_pool)
            return c * ModelConfig.CHAR_LENGTH

        elif mode == "pair_repeat":
            selected = random.sample(chars_pool, 3)
            return "".join([c*2 for c in selected])

        else:
            base = random.sample(chars_pool, 3)
            return "".join(random.choices(base, k=ModelConfig.CHAR_LENGTH))

    def generate(self, difficulty: float = 1.0, warmup: bool = False) -> Tuple[Image.Image, str]:
        """
        生成單張驗證碼影像及其對應標籤。
        包含：背景生成、文字排版、隨機旋轉、幾何扭曲與雜訊添加。
        """
        # 如果是熱身期，無視外部傳入的 difficulty
        current_diff = 0.0 if warmup else difficulty
        
        # 1. 隨機背景色彩 (難度越高，對比度可能越低)
        bg_val = 255 if warmup else random.randint(int(255 - 40 * current_diff), 255)
        image = Image.new('RGB', (self.width, self.height), color=(bg_val, bg_val, bg_val))
        draw = ImageDraw.Draw(image)
        
        # 2. 生成標籤
        if not warmup and random.random() < 0.25:
            label = self._generate_repeated_label()
        else:
            label = self._generate_diverse_label(warmup=warmup)
        
        # 3. 逐字繪製並旋轉
        curr_x = 15 if warmup else random.randint(10, 20)
        for char in label:
            font = self.get_random_font()
            # 建立獨立字元層以處理透明旋轉
            char_canvas_size = int(self.height * 1.5)  # 稍微大一點以容納旋轉
            char_layer = Image.new('RGBA', (char_canvas_size, char_canvas_size), (0, 0, 0, 0))
            char_draw = ImageDraw.Draw(char_layer)
            # 我們希望 curr_x 是文字的「中心」，所以粘貼左上角座標應該是 (curr_x - 畫布半寬)
            paste_x = int(curr_x - (char_canvas_size // 2))
            
            # 隨機文字顏色
            # 隨機文字顏色處理
            if warmup:
                # 熱身期使用純黑色 (0, 0, 0, 255)
                text_color = (0, 0, 0, 255)
            else:
                # 正常期：隨機深色 RGB + 不透明 A
                r, g, b = [random.randint(0, 100) for _ in range(3)]
                text_color = (r, g, b, 255)

            # 直接將 text_color 傳入 fill # 將文字繪製在畫布中心 (40, 40)
            char_draw.text((char_canvas_size // 2, char_canvas_size // 2), 
               char, font=font, fill=text_color, anchor="mm")
            
            # 隨機旋轉
            angle = 0 if warmup else random.randint(-35, 35) * current_diff
            if angle != 0:
                # center 指定旋轉中心為畫布中心
                char_layer = char_layer.rotate(angle, resample=Image.BICUBIC, expand=0)
            
            # 粘貼位置 (熱身期不上下抖動)
            # 3. 精確計算粘貼位置
            # 因為文字在 80x80 的中央，我們要讓這個中心對準主圖的垂直中心 (ModelConfig.IMAGE_HEIGHT // 2)
            # 主圖中心 Y = 30
            # 畫布中心 Y = 40
            # 基礎 offset = 30 - 40 = -10
            v_center_offset = (ModelConfig.IMAGE_HEIGHT // 2) - (char_canvas_size // 2)
            
            if warmup:
                final_y = v_center_offset
            else:
                # 這裡的隨機抖動控制在 +/- 8 像素內，避免字噴出去
                jitter = random.randint(-8, 8) 
                final_y = v_center_offset + jitter
            
            # 合併至主圖
            image.paste(char_layer, (paste_x, final_y), char_layer)
            if warmup:
                curr_x += int(self.height * 0.6)
            else:
                spacing = random.randint(18, 35)
                curr_x += spacing + random.randint(-5, 5)

                if random.random() < 0.3:
                    curr_x += random.randint(-10, 10)

        # 4. OpenCV 後處理 (雜訊與扭曲)
        img_np = np.array(image)
        
        # [新增] 在扭曲之前或之後加入幾何噪點
        # 建議在扭曲前加入，這樣方塊和圓圈也會跟著變形，看起來更自然
        if not warmup:
            if current_diff > 0.4:
                img_np = self._add_geometric_noise(img_np, current_diff)
            if current_diff > 0.2:
                img_np = self._apply_sine_warp(img_np, current_diff)
        
            # 加入雜訊干擾線
            line_count = int(12 * current_diff)
            for _ in range(line_count):
                p1 = (random.randint(0, self.width), random.randint(0, self.height))
                p2 = (random.randint(0, self.width), random.randint(0, self.height))
                color = (200, 200, 200) if warmup else tuple([random.randint(120, 200) for _ in range(3)])
                cv2.line(img_np, p1, p2, color, 1)

        return Image.fromarray(img_np), label
    
# =================================================================
# [正規化階段 3] 標準化 Dataset 與 多進程數據流
# =================================================================

class CaptchaDataset(Dataset):
    """
    正規化的驗證碼數據集類別。
    透過 map-style dataset 架構，配合 DataLoader 的 num_workers，
    能自動在 Ryzen 9800X3D 的多個核心上並行執行生成邏輯。
    """
    def __init__(self, size: int = 60000, font_dir: str = ModelConfig.font_path):
        super(CaptchaDataset, self).__init__()
        self.size = size
        # 初始化生成器
        self.generator = StandardCaptchaGenerator(font_dir=font_dir)
        # 訓練難度：由外部 Trainer 動態控制
        self.difficulty = 0.0
        self.warmup = True
        
    def set_difficulty(self, diff: float):
        """動態調整生成樣本的扭曲難度"""
        self.difficulty = max(0.0, min(1.0, diff))

    def __len__(self):
        return self.size

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        單個樣本的生成與基本預處理。
        注意：這裡返回 uint8 格式，後續由 GPUPreprocessor 進行浮點數轉換。
        """
        try:
            # 1. 調用生成引擎產生影像與標籤
            img_pil, label = self.generator.generate(self.difficulty, warmup=self.warmup)
            
            # 2. 轉換為灰階並轉成 Numpy 陣列
            img_gray = np.array(img_pil.convert('L'))
            
            # 3. 封裝為 Tensor (C, H, W)
            # 使用 uint8 是為了減少進程間通訊 (IPC) 的頻寬壓力
            img_tensor = torch.from_numpy(img_gray).unsqueeze(0).to(torch.uint8)
            
            # 4. 標籤序列化
            label_tensor = torch.tensor(
                [ModelConfig.CHAR_TO_IDX[c] for c in label], 
                dtype=torch.long
            )
            
            label_length = len(label)
            
            return img_tensor, label_tensor, label_length
            
        except Exception as e:
            # 健壯性處理：萬一生成失敗，返回一個全黑樣本避免崩潰
            print(f">>> [Dataset Error] 索引 {idx} 生成失敗: {e}")
            for _ in range(3):
                try:
                    new_idx = random.randint(0, self.size - 1)
                    return self.__getitem__(new_idx)
                except:
                    pass
            
            # 最後 fallback（真的不行才用）
            img = torch.zeros(3, ModelConfig.IMAGE_HEIGHT, ModelConfig.IMAGE_WIDTH)
            label = torch.zeros(ModelConfig.MAX_LABEL_LENGTH, dtype=torch.long)
            return img, label, ModelConfig.CHAR_LENGTH

class DataManager:
    """
    數據管理中心，負責構建高度優化的 DataLoader。
    """
    def __init__(self, dataset: CaptchaDataset):
        self.dataset = dataset

    def get_loader(self, batch_size: int, num_workers: int = 8) -> DataLoader:
        """
        針對 9800X3D 優化的加載器配置：
        - num_workers: 設為 8 以對應實體核心數。
        - pin_memory: 設為 True 加速數據轉移至 4070 Ti Super。
        - persistent_workers: 保持進程開啟，減少每個 Epoch 重啟的開銷。
        """
        return DataLoader(
            self.dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=True,
            collate_fn=self.collate_fn,
            persistent_workers=True if num_workers > 0 else False,
            drop_last=True
        )
        
    @staticmethod
    def collate_fn(batch):
        imgs, labels, lengths = zip(*batch)

        imgs = torch.stack(imgs)              # (B, C, H, W)
        lengths = torch.tensor(lengths, dtype=torch.long)

        return imgs, list(labels), lengths    # labels 保持 list！

# =================================================================
# [正規化階段 4] GPU 影像預處理與增強層 (On-GPU Preprocessing)
# =================================================================

class GPUPreprocessor(nn.Module):
    """
    利用 4070 Ti Super 的 CUDA 核心進行高速影像預處理。
    這將原本耗時的 Gaussian Blur 與 Normalization 從 CPU 移至 GPU。
    """
    def __init__(self, kernel_size: int = 3, sigma: float = 0.5):
        super(GPUPreprocessor, self).__init__()
        self.kernel_size = kernel_size
        self.learnable_blur = nn.Conv2d(1, 1, kernel_size=3, padding=1, bias=False)
        # 初始化為接近 Identity (單位矩陣) 或輕微高斯
        
        # 建立高斯模糊卷積核
        kernel = self._create_gaussian_kernel(kernel_size, sigma)
        # 使用 register_buffer 確保 kernel 會隨模型移動至正確的 GPU 設備
        self.register_buffer('blur_kernel', kernel)

    def _create_gaussian_kernel(self, k: int, s: float) -> torch.Tensor:
        """生成二維高斯卷積核 Tensor"""
        coords = torch.arange(k).float() - (k - 1) / 2.0
        g = torch.exp(-(coords**2) / (2.0 * s**2))
        g = g / g.sum()
        kernel_2d = g.view(-1, 1) * g.view(1, -1)
        return kernel_2d.view(1, 1, k, k)

    def forward(self, x: torch.Tensor, apply_blur: bool = True) -> torch.Tensor:
        """
        輸入: uint8 Tensor (B, 1, H, W)
        輸出: float32 Normalized & Blurred Tensor
        """
        # 1. 異步轉型與歸一化 (0.0 ~ 1.0)
        x = x.float() / 255.0
        
        # 2. 執行高斯模糊以減少雜訊對 CNN 的干擾
        # padding 使用 circular 或 replicate 以保持邊界穩定
        # 修正這裡：同時檢查 training 狀態與外部傳入的 apply_blur 開關
        if self.training and apply_blur and random.random() < 0.3:
            x = F.conv2d(x, self.blur_kernel, padding=self.kernel_size // 2)
        
        # 3. 對比度拉伸 (可選，助於文字特徵提取)
        x = torch.clamp(x, 0, 1)
        
        return x

# =================================================================
# [正規化階段 5] 空間變換網絡 (Spatial Transformer Network)
# =================================================================

class SpatialTransformer(nn.Module):
    """
    正規化的 STN 模組。
    其功能是在影像進入主 CNN 前，自動學習如何「對齊」或「拉直」受損的驗證碼。
    針對 4070 Ti Super 優化：增加了定位網絡的特徵深度。
    """
    def __init__(self):
        super(SpatialTransformer, self).__init__()
        
        # 定位網絡 (Localization Network)
        # 負責從輸入影像中回歸出 6 個仿射變換參數
        self.localization = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=5, padding=2),
            nn.BatchNorm2d(32),
            nn.MaxPool2d(2, stride=2), # 60x200 -> 30x100
            nn.ReLU(True),
            
            nn.Conv2d(32, 64, kernel_size=5, padding=2),
            nn.BatchNorm2d(64),
            nn.MaxPool2d(2, stride=2), # 30x100 -> 15x50
            nn.ReLU(True),
            
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.AdaptiveAvgPool2d((4, 8)), # 確保輸出尺寸固定，增加魯棒性
            nn.ReLU(True)
        )

        # 仿射矩陣回歸層
        self.fc_loc = nn.Sequential(
            nn.Linear(128 * 4 * 8, 512),
            nn.ReLU(True),
            nn.Dropout(0.2),
            nn.Linear(512, 6) # 輸出 theta 矩陣 [2x3]
        )

        # 初始化為單位矩陣 (Identity Transformation)
        # 讓模型在訓練初期「不做任何變換」，避免梯度崩潰
        self.fc_loc[-1].weight.data.zero_()  # 權重歸零，初始不隨機變換
        self.fc_loc[-1].bias.data.copy_(torch.tensor([1, 0, 0, 0, 1, 0], dtype=torch.float))

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        回傳: (矯正後的影像, 仿射參數 theta, 採樣網格 grid)
        """
        batch_size = x.size(0)
        
        # 1. 提取定位特徵並回歸參數
        xs = self.localization(x)
        xs = xs.view(xs.size(0), -1)
        theta = self.fc_loc(xs).view(-1, 2, 3)
        
        # 2. 強制物理限制：限制平移範圍，防止文字被移出視窗
        # 利用 tanh 將平移參數限制在 [-0.15, 0.15] 之間
        theta[:, :, 2] = torch.tanh(theta[:, :, 2]) * 0.2
        
        # 限制縮放 (對角線元素)，防止過度縮小導致邊緣露出
        # 讓縮放係數維持在 0.9 ~ 1.1 之間
        theta[:, 0, 0] = torch.sigmoid(theta[:, 0, 0]) * 0.6 + 0.7
        theta[:, 1, 1] = torch.sigmoid(theta[:, 1, 1]) * 0.6 + 0.7
        
        # --- 測試代碼：手動加入隨機旋轉/平移 ---
        # 如果你發現網格永遠是直的，取消下面這幾行的註解來驗證視覺化邏輯
        # theta[:, 0, 0] += 0.5  # 縮放變形
        # theta[:, 0, 2] += 0.3  # 水平平移
        # ---------------------------------------
        
        # 3. 生成採樣網格並執行雙線性插值 (Bilinear Interpolation)
        grid = F.affine_grid(theta, x.size(), align_corners=False)
        x_transformed = F.grid_sample(x, grid, align_corners=False, padding_mode="border")
        
        return x_transformed, theta, grid

# =================================================================
# [正規化階段 6] 深度卷積循環網絡 (Ultimate CRNN)
# =================================================================

class UltimateCaptchaModel(nn.Module):
    """
    正規化後的終極識別模型。
    結構順序：GPU 預處理 -> STN 矯正 -> CNN 特徵提取 -> RNN 序列建模 -> CTC 映射。
    """
    def __init__(self, num_classes: int):
        super(UltimateCaptchaModel, self).__init__()
        
        # 封裝組件
        self.preprocessor = GPUPreprocessor(kernel_size=3, sigma=0.5)
        self.stn = SpatialTransformer()
        
        # 高性能 CNN 特徵提取器 (針對 40 系列加速)
        # 通道數採用 64-128-256-512 遞增模式
        self.feature_extractor = nn.Sequential(
            # Block 1
            nn.Conv2d(1, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(True),
            nn.MaxPool2d(2, 2), # 30x100
            
            # Block 2
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(True),
            nn.MaxPool2d(2, 1), # 15x100
            
            # Block 3
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(True),
            nn.MaxPool2d((2, 1)), # 7x100 (高度大幅壓縮，保留寬度序列)
            
            # Block 4
            nn.Conv2d(256, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(True),
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(True),
            nn.AdaptiveAvgPool2d((4, None)) # 壓成 1x50，512 通道
        )
        
        self.height_compress = nn.Conv2d(
            in_channels=512,
            out_channels=512,
            kernel_size=(4, 1)  # 一次吃掉整個 height
        )
        
        # 雙向 LSTM 序列模型
        # 9800X3D 的多線程優勢能在此處處理複雜的隱藏層狀態切換
        self.rnn = nn.LSTM(
            input_size=512, 
            hidden_size=512, 
            num_layers=2, 
            bidirectional=True, 
            batch_first=True,
            dropout=0.3
        )
        
        # 全連接分類層 (CTC 解碼層)
        # 雙向 RNN 輸出為 512 * 2 = 1024
        self.fc_dropout = nn.Dropout(0.5) # 新增這行
        self.fc = nn.Linear(1024, num_classes)
        
        # 註冊 STN 的單位矩陣參考點
        # 形狀為 [1, 2, 3]，後續再根據 Batch Size 進行 expand
        identity = torch.tensor([[1, 0, 0], [0, 1, 0]], dtype=torch.float32)
        self.register_buffer('stn_identity', identity)

    def forward(self, x: torch.Tensor, apply_blur: bool = True, temperature=1) -> Dict[str, torch.Tensor]:
        """
        採用字典形式回傳，增加代碼的擴充性與正規化程度。
        """
        # 1. GPU 預處理
        x = self.preprocessor(x, apply_blur=apply_blur)
        
        # 2. STN 幾何校正
        stn_x, theta, grid = self.stn(x)
        
        # 3. 視覺增強：對矯正後的影像進行自適應對比度提升
        # 這有助於 CNN 在強雜訊環境下捕捉邊緣特徵
        # enhanced_x = torch.sigmoid((stn_x - 0.5) * 12.0)
        enhanced_x = stn_x
        
        # 4. CNN 特徵提取
        features = self.feature_extractor(enhanced_x)
        features = self.height_compress(features)
        
        # 5. 維度轉換 (Batch, Channel, Height, Width) -> (Batch, Width, Channel)
        # 此處 Width 即為序列的 Timesteps
        features = features.squeeze(2)       # (B, 512, W)
        features = features.permute(0, 2, 1) # (B, W, 512)
        
        # 6. RNN 序列標註
        rnn_out, _ = self.rnn(features)
        rnn_out = self.fc_dropout(rnn_out) # 套用 Dropout
        
        # 7. Log Softmax 輸出 (CTC Loss 標準輸入)
        logits = self.fc(rnn_out)
        log_probs = F.log_softmax(logits / (temperature + 0.3), dim=2)
        
        return {
            "log_probs": log_probs,
            "stn_x": stn_x,
            "enhanced_x": enhanced_x,
            "theta": theta,
            "grid": grid
        }
    
# =================================================================
# [正規化階段 7] 智能權重管理與早停系統
# =================================================================

class TrainingMonitor:
    """
    正規化的監控與早停系統。
    負責監控 Loss 變化、防止梯度爆炸，並在模型不再進步時提前結束訓練。
    """
    def __init__(self, patience: int = 100, explosion_threshold: float = 15.0):
        self.patience = patience
        self.explosion_threshold = explosion_threshold
        self.best_loss = float('inf')
        self.counter = 0
        self.early_stop = False
        self.initial_loss = None
        # 數據紀錄存儲
        self.history = {
            'loss': [],
            'char_acc': [],
            'full_acc': [],
            'epochs': [],
            'lr': [],
            'lr_events': []  # 新增：記錄 LR 變動點
        }
        
    def is_mastered(self, current_acc: float) -> bool:
        """檢查當前難度是否已經『精通』(用來判斷是否該升難度)"""
        return current_acc >= 95  # 稍微調低一點點，加速推動難度上升
        
    def record_and_step(self, epoch: int, loss: float, c_acc: float, f_acc: float, lr: float):
        """僅負責數據紀錄，不執行早停決策"""
        self.history['epochs'].append(epoch)
        self.history['loss'].append(loss)
        self.history['char_acc'].append(c_acc)
        self.history['full_acc'].append(f_acc)
        self.history['lr'].append(lr)  # 新增
        
        # 偵測 LR 是否下降
        if len(self.history['lr']) > 1:
            prev_lr = self.history['lr'][-2]
            if lr < prev_lr:
                self.history['lr_events'].append((epoch, lr))
                print(f">>> [LR事件] Epoch {epoch}: LR下降 {prev_lr:.2e} → {lr:.2e}")
        
    def reset_patience(self):
        """當難度提升時，由外部呼叫此函數，重置耐心計數器與最佳 Loss"""
        self.best_loss = float('inf')
        self.counter = 0
        print(">>> [系統] 偵測到難度變化，已重置監控計數器。")

    def step(self, current_loss: float, current_acc: float, is_max_difficulty: bool) -> bool:
        """檢查是否觸發早停條件"""
        """
        核心邏輯：
        1. 數值爆炸必須停止（保護硬體）。
        2. 只有在『最高難度』且『達到準確率』或『失去耐心』時，才觸發真正的早停。
        """
        if self.initial_loss is None:
            self.initial_loss = current_loss

        # 針對 40 系列顯示卡的高主頻特性，加入梯度爆炸自動保護機制
        if current_loss > self.initial_loss * self.explosion_threshold:
            print(f"\n>>> [警告] 偵測到數值爆炸 (Loss: {current_loss:.2f})，強制停止。")
            self.early_stop = True
            return True
        
        # 判斷 Loss 是否改善
        if current_loss < self.best_loss:
            self.best_loss = current_loss
            self.counter = 0
        else:
            # 只有在最高難度時，才增加耐心計數器
            if is_max_difficulty:
                self.counter += 1

        # 執行早停判定 (僅在最高難度下生效)
        if is_max_difficulty:
            # 1. 準確率達標
            if current_acc >= 99.8:
                print("\n>>> [成就] 最高難度已達完美準確率，訓練正式結束。")
                self.early_stop = True
                return True
            
            # 2. 失去耐心 (連續未進步)
            if self.counter >= self.patience:
                print(f"\n>>> [通知] 最高難度下連續 {self.patience} 輪未見進步，啟動早停。")
                self.early_stop = True
                return True
        
        return False

# =================================================================
# [正規化階段 8] 核心訓練引擎 (CaptchaTrainer)
# =================================================================

class CaptchaTrainer:
    """
    高度封裝的訓練管理器。
    針對 RTX 4070 Ti Super 16GB VRAM 進行了以下優化：
    1. AMP 混合精度訓練：減少顯存佔用並提速 2-3 倍。
    2. 分層學習率：STN 使用較小 LR 以維持幾何穩定性。
    3. 權重兼容性加載：支援不同版本的 model state dict。
    """
    def __init__(self, model: nn.Module, device: torch.device):
        self.model = model.to(device)
        self.device = device
        self._stn_added = False
        
        # 一開始先凍結 STN
        for p in self.model.stn.parameters():
            p.requires_grad = False
        
        # 使用 AdamW 優化器，並針對不同模組設定分層學習率
        self.optimizer = optim.AdamW([
            {'params': model.feature_extractor.parameters(), 'lr': ModelConfig.INITIAL_LR, 'weight_decay': 1e-4},
            {'params': model.rnn.parameters(), 'lr': ModelConfig.INITIAL_LR, 'weight_decay': 1e-4},
            {'params': model.fc.parameters(), 'lr': ModelConfig.INITIAL_LR, 'weight_decay': 1e-4}
        ])

        # 學習率調度器
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=8,
            cooldown=2,
            min_lr=1e-6,
        )

        # 混合精度縮放器 (GradScaler)
        self.scaler = torch.amp.GradScaler(enabled=(self.device.type == 'cuda'))
        
        # CTC 損失函數
        self.criterion = nn.CTCLoss(blank=0, zero_infinity=True)
        self.monitor = TrainingMonitor()
        # 從配置檔讀取初始學習率
        self.current_lr = ModelConfig.INITIAL_LR

    def load_checkpoint(self, path: str) -> float:
        """正規化的權重載入邏輯，回傳上次訓練的難度"""
        if not os.path.exists(path):
            return 0.0
        
        print(f">>> [載入] 正在恢復權重檔案: {path}")
        # 修改後 (增加 weights_only=False，因為你的 checkpoint 包含自定義字典)
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        
        # 相容性檢查：區分純權重與完整存檔
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            state_dict = checkpoint['model_state_dict']
            saved_diff = checkpoint.get('current_diff', 0.2)
        else:
            state_dict = checkpoint
            saved_diff = 0.2

        # 過濾名稱不匹配的鍵 (用於熱更新模型結構)
        curr_model_dict = self.model.state_dict()
        filtered_dict = {k: v for k, v in state_dict.items() 
                         if k in curr_model_dict and v.shape == curr_model_dict[k].shape}
        
        curr_model_dict.update(filtered_dict)
        self.model.load_state_dict(curr_model_dict)
        
        print(f">>> [載入完成] 成功恢復 {len(filtered_dict)} 個參數層，起始難度: {saved_diff}")
        return saved_diff

    def _calculate_stn_loss(self, theta: torch.Tensor) -> torch.Tensor:
        """
        正規化的 STN 懲罰項。
        防止空間變換網絡過度拉扯影像導致資訊丟失。
        確保所有 Tensor 皆為 float32 以避免 dtype 衝突。
        """
        # 理想狀態是單位矩陣 [1, 0, 0, 0, 1, 0]
        # [核心修正] 強制指定 dtype=torch.float32 並確保與 theta 設備一致
        # 從 model 中取出註冊好的 stn_identity
        # 並根據當前的 batch size 進行擴展 (expand)
        batch_size = theta.size(0)
        target = self.model.stn_identity.unsqueeze(0).expand(batch_size, -1, -1)
        
        # 1. 基礎參數約束
        loss_base = F.mse_loss(theta, target)
        
        # 2. 強力平移約束 (單獨懲罰最後一列的 t_x 和 t_y)
        # theta[:, :, 2] 取出的是 (batch, 2) 的平移向量
        # 使用 L2 範數 (平方和) 進行強力懲罰
        loss_trans = torch.mean(theta[:, :, 2]**2)
        
        # 3. 組合 Loss：給予平移項更高的權重 (例如 2 倍)
        # 這樣模型只要稍微動一下位置，Loss 就會飆高，逼迫它回歸中心
        total_stn_loss = loss_base + 2.0 * loss_trans
        
        return total_stn_loss

    def train_epoch(self, loader: DataLoader, difficulty: float, epoch: int, epoch_temp: float = 1.0, visualizer=None) -> Tuple[float, float, float]:
        """執行單個 Epoch 的標準訓練流程"""
        self.model.train()
        
        # 判斷是否已經過了 Warmup 階段
        is_warmup = epoch < ModelConfig.WARMUP_EPOCHS
        # 如果是 warmup 則關閉模糊 (False)，否則開啟 (True)
        blur_on = not is_warmup
        
        # 當達到特定 Epoch (例如 100) 時解凍
        if (epoch >= ModelConfig.WARMUP_EPOCHS) and (not self._stn_added):
            print(f"\n>>> [系統通知] Epoch {epoch}: 達到熱身終點，正在解凍 STN 模組...")
            print(f"\nSTN LR:", self.optimizer.param_groups[0]['lr'])
            for param in self.model.stn.parameters():
                param.requires_grad = True
            # 重新建立 optimizer（關鍵）
            if not self._stn_added and epoch >= ModelConfig.WARMUP_EPOCHS:
                self.optimizer.add_param_group({
                    'params': self.model.stn.parameters(),
                    'lr': ModelConfig.INITIAL_LR * 0.02,
                    'weight_decay': 1e-4
                })
                self._stn_added = True
            # 針對 4070 Ti Super 優化：重新構建優化器以納入 STN 參數
            # 否則 Adam 不會更新剛剛解凍的權重
            # 降低 STN learning rate（避免炸掉）
        total_loss = 0.0
        correct_chars, total_chars = 0, 0
        full_match, total_samples = 0, 0
        c_acc = 0.0
        f_acc = 0.0
        valid_batches = 0
        
        # 設定顯示頻率 (例如每 5 個 Batch 顯示一次)
        display_freq = 5
        
        pbar = tqdm(loader, desc=f"Diff: {difficulty:.2f}", leave=False, dynamic_ncols=True)
        for batch_idx, (imgs, labels, target_lens) in enumerate(pbar): # 加上 batch_idx
            imgs = imgs.to(self.device, non_blocking=True)
            labels = [l.to(self.device) for l in labels]
            target_lens = target_lens.to(self.device)
            penalty = 0.0
            
            # 40 系列優化：使用 set_to_none 減少顯存寫入開銷
            self.optimizer.zero_grad(set_to_none=True)
            if batch_idx % 200 == 0:
                torch.cuda.empty_cache()
            
            # AMP 自動混合精度區塊
            with torch.amp.autocast(device_type=self.device.type):
                output_dict = self.model(imgs, apply_blur=blur_on, temperature=epoch_temp)
                log_probs = output_dict["log_probs"]
                
                # CTC Loss 要求形狀: (Time, Batch, Class)
                lp_for_ctc = log_probs.permute(1, 0, 2)
                batch_size = imgs.size(0)
                input_lens = torch.full((batch_size,), lp_for_ctc.size(0), dtype=torch.long, device=self.device)
                
                # 確保 labels 是 Long (CTC 要求)，但輸出的 loss 必須是 Float
                targets = torch.cat(labels).to(self.device)
                
                if len(labels) == 0 or any(len(l) == 0 for l in labels):
                    continue
                
                target_lens_batch = target_lens.to(self.device)
                
                loss_ctc = self.criterion(lp_for_ctc, targets, input_lens, target_lens_batch)
                if not torch.isfinite(loss_ctc):
                    print(">>> [警告] CTC Loss 非法，跳過 batch")
                    continue
                # 強制將 STN loss 轉換為 float32 確保與 CTC loss 兼容
                valid_batches += 1
                loss_stn = self._calculate_stn_loss(output_dict["theta"]).float()
                
                # 總損失結合 (確保所有項都是 float)
                stn_weight = 0.01 if epoch > ModelConfig.WARMUP_EPOCHS else 0.05
                probs = log_probs.exp()
                entropy = -torch.mean(torch.sum(probs * log_probs, dim=2))
                entropy = torch.clamp(entropy, 0, 10)

                loss = loss_ctc.float() + (stn_weight * loss_stn) + 0.005 * entropy
                
                if not torch.isfinite(loss):
                    print(">>> [警告] loss 非法，跳過 backward")
                    continue

            # 反向傳播與優化
            self.scaler.scale(loss).backward()
            
            if not torch.isfinite(loss):
                continue
            
            # 梯度裁剪：維持訓練穩定性
            self.scaler.unscale_(self.optimizer)
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            
            self.scaler.step(self.optimizer)
            self.scaler.update()
            
            # --- 即時計算 ACC 指標 (用於進度條) ---
            with torch.no_grad():
                preds = CaptchaDecoder.decode(log_probs)
                
                collapse_score = 0.0
                for p in preds:
                    if len(p) > 0:
                        unique_ratio = len(set(p)) / len(p)
                        if unique_ratio < 0.3:  # 🚨 collapse threshold
                            collapse_score += (0.3 - unique_ratio)

                collapse_score = collapse_score / max(1, len(preds))
                collapse_penalty = 0.1 * collapse_score
                loss = loss + collapse_penalty
                # 1. 這裡加入視覺化判斷 (例如每 200 個 Batch 抽樣一張圖看)
                if visualizer is not None and batch_idx % 200 == 0:
                    # 直接呼叫，傳入當前的 output_dict, imgs, labels 與剛剛解碼好的 preds
                    visualizer.show_debug_frame(output_dict, imgs, labels, preds)
                
                # 2. 原本的指標統計邏輯
                gt_list = ["".join([ModelConfig.IDX_TO_CHAR[i.item()] for i in l]) for l in labels]
                for p, g in zip(preds, gt_list):
                    total_samples += 1
                    if p == g:
                        dist = 0
                        full_match += 1
                    else:
                        if len(p) > 2 * ModelConfig.CHAR_LENGTH:
                            dist = len(g)
                        else:
                            dist = self.levenshtein(p, g)
                    if len(p) != ModelConfig.CHAR_LENGTH:
                        # 視情況處理
                        # 方法1：直接當錯
                        dist = len(g)
                    correct_chars += max(0, len(g) - dist)
                    total_chars += len(g)
            
            # 統計數據
            # 簡易準確率計算 (解碼邏輯放在下一部分)
            cur_loss = loss.item() + penalty
            c_acc = (correct_chars / total_chars) * 100 if total_chars > 0 else 0.0
            f_acc = (full_match / total_samples) * 100 if total_samples > 0 else 0.0
            pbar.set_postfix({
                "Diff": f"{difficulty:.2f}",   # 顯示當前難度
                "Loss": f"{cur_loss:.3f}", 
                "Char": f"{c_acc:.1f}%", 
                "Full": f"{f_acc:.1f}%"
                })
            
            total_loss += loss.item()
        
        # 動態調整 difficulty
        difficulty = self.update_difficulty(c_acc, f_acc, difficulty)

        # 動態調整 temperature
        epoch_temp = self.update_temperature(entropy.item(), epoch_temp)
            
        if valid_batches == 0:
                return 0.0, 0.0, 0.0

        return total_loss / valid_batches, c_acc, f_acc, difficulty, epoch_temp # 回傳準確率
    
    def update_temperature(self, entropy: float, current_temp: float) -> float:
        """
        自適應 temperature（避免過度自信 or collapse）
        """
        if entropy < 1.5:
            # 太確定 → 增加溫度（讓分布變平）
            current_temp += 0.05
        elif entropy > 3.5:
            # 太亂 → 降低溫度
            current_temp -= 0.05

        return float(np.clip(current_temp, 0.5, 2.0))
    
    def update_difficulty(self, c_acc: float, f_acc: float, current_diff: float) -> float:
        """
        根據模型表現自動調整難度
        """
        # 🎯 核心策略：
        # - Char acc 高 → 可以加難
        # - Full acc 高 → 快速加難
        # - 表現差 → 降難避免崩潰

        if f_acc > 85:
            current_diff += 0.05
        elif c_acc > 80:
            current_diff += 0.02
        elif c_acc < 50:
            current_diff -= 0.03

        return float(np.clip(current_diff, 0.1, 1.0))
    
    @staticmethod
    def levenshtein(a, b):
        m, n = len(a), len(b)
        
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
            
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                cost = 0 if a[i-1] == b[j-1] else 1
                dp[i][j] = min(
                    dp[i-1][j] + 1,      # delete
                    dp[i][j-1] + 1,      # insert
                    dp[i-1][j-1] + cost  # replace
                )
        
        return dp[m][n]

# =================================================================
# [正規化階段 9] 序列解碼與結果分析 (Sequence Decoder)
# =================================================================

class CaptchaDecoder:
    """
    負責將模型輸出的 Log-Probs 轉換為人類可讀的字串。
    實現了 Best-Path Decoding (Greedy Search) 邏輯。
    """
    @staticmethod
    def decode(log_probs: torch.Tensor) -> List[str]:
        """
        輸入: (Batch, Time, Class) 的 Tensor
        輸出: 解碼後的字串列表
        """
        # 取出機率最大的索引 (Greedy Search)
        # shape: (Batch, Time)
        _, max_indices = torch.max(log_probs, dim=2)
        max_indices = max_indices.cpu().numpy()
        
        results = []
        for batch_idx in range(max_indices.shape[0]):
            raw_sequence = max_indices[batch_idx]
            decoded_chars = []
            last_char_idx = -1
            
            for idx in raw_sequence:
                # CTC 解碼規則：
                # 1. 忽略 Blank (索引 0)
                # 2. 忽略連續重複的字符 (除非中間隔著 Blank)
                if idx != 0 and idx != last_char_idx:
                    decoded_chars.append(ModelConfig.IDX_TO_CHAR[idx])
                last_char_idx = idx
            
            results.append("".join(decoded_chars))
        return results

# =================================================================
# [正規化階段 10] 視覺化診斷工具 (Visualization Engine)
# =================================================================

class DiagnosticVisualizer:
    """
    取代原本的 cv2.imshow，提供結構化的模型狀態監控。
    包含：原始圖、預處理圖、STN 矯正圖、以及 STN 採樣網格。
    """
    def __init__(self):
        # 建立參考網格，用於視覺化 STN 的幾何拉扯程度
        h, w = ModelConfig.IMAGE_HEIGHT, ModelConfig.IMAGE_WIDTH
        # --- 核心修改：建立一個「有線條」的參考圖 ---
        # 建立一個黑色背景
        grid_canvas = np.zeros((h, w), dtype=np.float32)
        # 在畫布上繪製明顯的白色網格線 (1.0)
        # 每隔 20 像素畫一條線，這能讓你清楚看到 STN 的拉伸與扭曲
        step = 20
        # 畫上白色網格線 (每隔 20 像素畫一條)
        for x in range(0, w, step):
            cv2.line(grid_canvas, (x, 0), (x, h), 1.0, 1)
        for y in range(0, h, 20):
            cv2.line(grid_canvas, (0, y), (w, y), 1.0, 1)
        # 轉換為 Tensor (1, 1, H, W) 供 grid_sample 使用
        self.grid_ref = torch.from_numpy(grid_canvas).unsqueeze(0).unsqueeze(0).to(ModelConfig.DEVICE)
        self.window_moved = False

    def show_debug_frame(self, output_dict: dict, original_img: torch.Tensor, 
                         labels: torch.Tensor, preds: List[str]):
        """
        將多個中間層結果拼接成一張大圖進行實時監控。
        針對 4K 螢幕優化，確保顯示尺寸適中。
        """
        import threading
        # 1. 安全檢查：如果這不是主執行緒（例如來自 DataLoader 的 worker），直接回傳 None
        # 這是解決 PyEval_RestoreThread 報錯的最核心改動
        if threading.current_thread() is not threading.main_thread():
            return None
        # 1. 準備影像組件
        # 原始圖 (正規化回 0-255)
        orig_np = (original_img[0, 0].detach().cpu().numpy() * 255).astype(np.uint8)
        orig_np = cv2.resize(orig_np, (ModelConfig.IMAGE_WIDTH, ModelConfig.IMAGE_HEIGHT))
        
        # STN 矯正後的圖
        stn_np = (output_dict["stn_x"][0, 0].detach().cpu().numpy() * 255).astype(np.uint8)
        stn_np = cv2.resize(stn_np, (ModelConfig.IMAGE_WIDTH, ModelConfig.IMAGE_HEIGHT))
        
        # STN 網格視覺化 (顯示 STN 是如何變換空間的)
        grid_viz_tensor = F.grid_sample(
            self.grid_ref.to(output_dict["grid"].dtype), # 強制將參考網格轉為與輸出相同的類型 (Float 或 Half) 
            output_dict["grid"][:1], 
            mode='bilinear',       # 使用雙線性插值讓線條平滑
            padding_mode='zeros',  # 超出邊界的補黑
            align_corners=False
        )
        # 強制正規化到 0-255，避免因為數值太小導致全黑
        # 轉換為 OpenCV 影像
        # 因為 grid_ref 的線條是 1.0，直接乘以 255 即可得到純白線條
        grid_raw = grid_viz_tensor[0, 0].detach().cpu().numpy()
        grid_np = np.clip(grid_raw * 255, 0, 255).astype(np.uint8) # 加入 clip 確保安全
        grid_np = cv2.resize(grid_np, (ModelConfig.IMAGE_WIDTH, ModelConfig.IMAGE_HEIGHT))
        
        # 2. 影像拼接 (橫向)
        combined = np.hstack((orig_np, stn_np, grid_np))
        combined_bgr = cv2.cvtColor(combined, cv2.COLOR_GRAY2BGR)
        
        # --- 【核心修改：加入座標軸標籤】 ---
        h_raw, w_raw = combined_bgr.shape[:2]
        # 擴展邊框 (上20, 下25, 左40, 右10) 用於放置座標數值
        labeled_canvas = cv2.copyMakeBorder(combined_bgr, 20, 25, 40, 10, cv2.BORDER_CONSTANT, value=(20, 20, 20))
        
        ax_color = (180, 180, 180) # 淺灰色標籤
        # 繪製 X 軸座標 (每 100 像素標註一次)
        for x in range(0, w_raw + 1, 100):
            target_x = x + 40 # 加上左邊框寬度
            cv2.line(labeled_canvas, (target_x, 20 + h_raw), (target_x, 20 + h_raw + 5), ax_color, 1)
            cv2.putText(labeled_canvas, str(x), (target_x - 12, 20 + h_raw + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.35, ax_color, 1)
            
        # 繪製 Y 軸座標 (每 20 像素標註一次)
        for y in range(0, h_raw + 1, 20):
            target_y = y + 20 # 加上頂部邊框高度
            cv2.line(labeled_canvas, (35, target_y), (40, target_y), ax_color, 1)
            cv2.putText(labeled_canvas, str(y), (5, target_y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.35, ax_color, 1)
        # ------------------------------------
        
        # 3. 繪製標籤與預測 (座標需考慮邊框偏移：x+40, y+20)
        gt_text = "".join([ModelConfig.IDX_TO_CHAR[i.item()] for i in labels[0]])
        pred_text = preds[0]
        color = (0, 255, 0) if gt_text == pred_text else (0, 0, 255)
        
        cv2.putText(labeled_canvas, f"GT: {gt_text} | Pred: {pred_text}", (10 + 40, 25 + 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # 確保視窗名稱一致
        win_name = "Normalization Diagnostic (Orig | STN | Grid)"
        
        try:
            # 使用 try 保護，防止視窗被手動關閉時導致的崩潰
            if not hasattr(self, '_cv_inited'):
                cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
                # 強制推向您的左側 2K 副螢幕
                cv2.resizeWindow(win_name, 1000, 250)         # 設定初始寬 1000, 高 250 (可自行調整)
                cv2.moveWindow(win_name, -2500, 600)
                self._cv_inited = True
                self.window_moved = True # 保持您的變數相容性
                
                # 這裡視窗名稱必須精確匹配
                cv2.imshow(win_name, labeled_canvas)
                
                # 3. 關鍵：waitKey(1) 是釋放 GIL 並處理 Windows 訊息隊列的唯一方式
                cv2.waitKey(1)
        except Exception as e:
            print(f"GUI Thread Warning: {e}")
        
        # [新增] 回傳這張拼接好的圖片，讓 main 可以在訓練結束時儲存它
        return labeled_canvas

# =================================================================
# [最終階段] 主程序執行入口與邏輯串接
# =================================================================

def main():
    # 執行硬體優化配置
    ModelConfig.apply_hardware_optimization()
    ModelConfig.prepare_folders() # <--- 確保資料夾已建立
    device = ModelConfig.DEVICE
    print(f">>> [系統] 運行設備: {device} | 使用者: z0916")
    
    last_debug_img = None  # 用來存放最後一幀診斷圖

    # 1. 初始化數據組件
    # 建立 6 萬張樣本的動態數據集，利用 9800X3D 的多核心生成
    dataset = CaptchaDataset(size=100000)
    data_mgr = DataManager(dataset)
    train_loader = data_mgr.get_loader(batch_size=ModelConfig.BATCH_SIZE, num_workers=8)

    # 2. 初始化模型與訓練器
    model = UltimateCaptchaModel(num_classes=ModelConfig.NUM_CLASSES)
    trainer = CaptchaTrainer(model, device)
    plotter = RealTimePlotter() # 初始化繪圖引擎
    lr_plotter = LRPlotter()
    visualizer = DiagnosticVisualizer()
    
    # 這裡如果是從頭訓練，強制 difficulty 為 0
    current_difficulty = 0.0
    
    # 3. 嘗試載入現有權重 (斷點續傳)
    current_difficulty = trainer.load_checkpoint(ModelConfig.WEIGHT_PATHS["best"])
    max_difficulty = 1.0
    
    acc_history = []
    
    sample_iter = iter(train_loader)

    # 4. 主訓練循環 (正規化 Epoch 邏輯)
    print("\n" + "="*50)
    print("開始正規化訓練流程 - 深度 STN + CRNN 模式")
    print("="*50)

    try:
        for epoch in range(1, ModelConfig.MAX_EPOCHS + 1):
            # --- 熱身邏輯判斷 ---
            is_warmup = (epoch < ModelConfig.WARMUP_EPOCHS)
            dataset.warmup = is_warmup
            
            # 如果在熱身期，強制難度為 0；否則才使用累積難度
            actual_diff = 0.0 if is_warmup else current_difficulty
            
            # --- [新增] 動態溫度策略 ---
            # 熱身期隨機溫度讓模型多嘗試不同路徑；過後 1.1~1.4 確保精準度
            if is_warmup:
                current_temp = random.uniform(1.3, 1.7)
            else:
                current_temp = random.uniform(1.1, 1.4)
            
            # 動態調整數據集難度 (每 10 個 Epoch 增加 0.02)
            # 這是一種正規化的課程學習 (Curriculum Learning) 策略
            dataset.set_difficulty(actual_diff)
            
            # 1. 訓練並取得三項指標
            avg_loss, char_acc, full_acc, difficulty, temp = trainer.train_epoch(
            loader=train_loader,
            difficulty=current_difficulty,
            epoch=epoch,  # <--- 務必傳入這個變數
            epoch_temp=current_temp, # 傳遞溫度
            visualizer=visualizer
            )
            
            # --- Moving Average ---
            acc_history.append(full_acc)
            if len(acc_history) > 5:
                acc_history.pop(0)
            
            smoothed_acc = sum(acc_history) / len(acc_history)
                
            # --- 核心邏輯：動態難度推動 ---
            is_max = (current_difficulty >= max_difficulty)
            
            # 3. 執行監控決策 (傳入 is_max)
            # 只有在 is_max=True 且滿足早停條件時，才會回傳 True
            stop_flag = trainer.monitor.step(avg_loss, smoothed_acc, is_max)
            
            if epoch == int(ModelConfig.WARMUP_EPOCHS * 0.6):
                print("\n>>> [系統通知] 熱身期結束，STN 參數已解凍，開始學習幾何校正。")
            # 建議：當模型在當前難度表現優異時，主動提升難度基礎值
            if not is_warmup:
                if trainer.monitor.is_mastered(smoothed_acc) and not is_max:
                    old_diff = current_difficulty
                    # 每次精通後增加 0.01 難度
                    increment = 0.02 if current_difficulty < 0.5 else 0.01
                    current_difficulty = min(max_difficulty, current_difficulty + increment)
                    print(f"\n>>> [升級] 難度 {old_diff:.2f} 已精通，提升至 {current_difficulty:.2f}")
                    
                    # 重要：重置 Monitor 的計數器，因為新難度 Loss 會跳動
                    trainer.monitor.reset_patience()
            else:
                print(f">>> [熱身中] 剩餘 {ModelConfig.WARMUP_EPOCHS - epoch} 輪簡化樣本訓練...")
            
            # 5. 更新學習率與監控
            trainer.scheduler.step(avg_loss)
            current_lr = trainer.scheduler.get_last_lr()[0]
            # 2. 更新趨勢圖
            trainer.monitor.record_and_step(epoch, avg_loss, char_acc, full_acc, current_lr)
            plotter.update(trainer.monitor.history)
            lr_plotter.update(trainer.monitor.history)
            
            # [新增] 每個 Epoch 強制將折線圖存入硬碟，確保訓練中途也能查看
            plotter.save("live_training_trend.png")
            lr_plotter.save("live_learning_trend.png")
            
            # 執行驗證與解碼測試 (拿 Batch 的第一個樣本做視覺化)
            model.eval()
            with torch.no_grad():
                # 從 Loader 抽樣一組進行視覺化
                try:
                    sample_imgs, sample_labels, _ = next(sample_iter)
                except StopIteration:
                    sample_iter = iter(train_loader)
                    sample_imgs, sample_labels, _ = next(sample_iter)
                sample_imgs = sample_imgs.to(device)
                
                output_dict = model(sample_imgs)
                preds = CaptchaDecoder.decode(output_dict["log_probs"])
                
                # 統合成一次呼叫：更新視窗 + 取得圖片物件 + 存檔
                last_debug_img = visualizer.show_debug_frame(output_dict, sample_imgs, sample_labels, preds)
                if last_debug_img is not None:
                    diag_path = os.path.join(ModelConfig.OUTPUT_DIR, "live_diagnostic_view.png")
                    cv2.imwrite(diag_path, last_debug_img) # 儲存為固定檔名，即時覆蓋
                
                # 計算簡易 Batch 準確率
                gt_list = ["".join([ModelConfig.IDX_TO_CHAR[i.item()] for i in labels]) for labels in sample_labels]
                correct = sum(1 for p, g in zip(preds, gt_list) if p == g)
                batch_acc = (correct / len(sample_labels)) * 100
                
            print(f"Epoch {epoch} | LR: {current_lr:.6e} | Diff: {current_difficulty:.2f} | Loss: {avg_loss:.4f} | FullACC: {full_acc:.2f}%")
            
            # --- 修改後的存檔邏輯：加入品質門檻 ---
            # 定義存檔門檻：例如 FullACC 必須大於 50% 或處於低難度期才存檔
            # 這樣可以防止在極高難度下模型崩潰時，覆蓋掉原本「堪用」的權重
            SAVE_THRESHOLD = 60.0
            
            # 定期存檔
            if True:
                if full_acc > SAVE_THRESHOLD or current_difficulty < 0.3:
                    # 1. 永遠保存一份最新的「最佳」權重
                    save_data = {
                        'model_state_dict': model.state_dict(),
                        'optimizer_state_dict': trainer.optimizer.state_dict(),
                        'current_diff': current_difficulty, # 保存當前進度難度
                        'epoch': epoch,
                        'full_acc': full_acc
                    }
                    torch.save(save_data, ModelConfig.WEIGHT_PATHS["best"])
                    # 2. 階梯式備份：每逢難度跨越 0.2, 0.4, 0.6, 0.8 時額外存一份檔
                    # 這樣萬一難度 1.0 練壞了，你可以隨時退回 0.8 的版本
                    milestones = [0.2, 0.4, 0.6, 0.8]
                    for m in milestones:
                        # 如果當前難度剛好超過里程碑（且在誤差範圍內），存一個獨立檔案
                        if abs(current_difficulty - m) < 0.005:
                            m_path = os.path.join(ModelConfig.OUTPUT_DIR, f"model_diff_{m:.1f}.pth")
                            if not os.path.exists(m_path): # 每個里程碑只存一次
                                torch.save(save_data, m_path)
                                print(f"\n>>> [里程碑] 已備份難度 {m:.1f} 的權重至: {m_path}")

                    print(f">>> [存檔] 表現達標 ({full_acc:.2f}%)，權重已更新。")
                else:
                    print(f">>> [警告] 當前準確率 ({full_acc:.2f}%) 低於門檻，放棄本次存檔以保護舊權重。")
            if stop_flag:
                break

    except KeyboardInterrupt:
        print("\n>>> [手動停止] 正在保存當前進度...")
        torch.save(model.state_dict(), r"F:\AI\MyProject\python\test\model_best.pth")
    
    finally:
        # --- 最終動作 ---
        
        # 2. 儲存虛擬生成圖片 (包含原始、STN、網格)
        if last_debug_img is not None:
            final_diag_path = os.path.join(ModelConfig.OUTPUT_DIR, "live_diagnostic_view.png")
            cv2.imwrite(final_diag_path, last_debug_img)
            print(f">>> [系統] 診斷圖片已儲存至: {final_diag_path}")
            
        cv2.destroyAllWindows()
        print(">>> 訓練任務結束。")

def visualize_preprocessing(num_samples=50, difficulty=1.0, warmup=False, font_dir=ModelConfig.font_path):
    """
    [互動診斷工具]：
    - 按下「ESC」：直接退出程式。
    - 按下「任何其他鍵」：跳轉至下一張樣本。
    - 功能：顯示原始圖、STN 矯正圖、視覺增強圖，以及 CNN 第一層的 16 個特徵通道。
    """
    # 根據是否為 warmup 強制調整顯示難度字串
    display_diff = 0.0 if warmup else difficulty
    print(f"\n>>> [啟動互動診斷] 模式: {'熱身期 (Warmup)' if warmup else '正常訓練'}")
    print(f"\n>>> [啟動互動診斷] 難度: {difficulty} | 樣本上限: {num_samples}")
    print(">>> 指令: [ESC] 退出 | [其餘任意鍵] 下一張")
    
    gen = StandardCaptchaGenerator(font_dir=font_dir)
    # 初始化模型並設為評估模式
    model = UltimateCaptchaModel(num_classes=ModelConfig.NUM_CLASSES).to(ModelConfig.DEVICE)
    
    # 載入現有權重，否則 STN 永遠是初始狀態 ---
    checkpoint_path = ModelConfig.WEIGHT_PATHS["best"]
    if os.path.exists(checkpoint_path):
        # 這裡同步修正 FutureWarning
        checkpoint = torch.load(checkpoint_path, map_location=ModelConfig.DEVICE, weights_only=False)
        # 判斷是完整 checkpoint 還是純 state_dict
        # 判斷是完整存檔還是純權重
        s_dict = checkpoint['model_state_dict'] if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint else checkpoint
        
        # 載入權重
        model.load_state_dict(s_dict)
        print(">>> [成功] 已載入權重，STN 現在具備變形能力。")
    else:
        print(">>> 警告：未找到權重檔案，STN 將維持初始狀態。")
    
    model.eval()

    for i in range(num_samples):
        # 1. 數據準備
        img_pil, label = gen.generate(difficulty=difficulty, warmup=warmup)
        img_gray = np.array(img_pil.convert('L'))
        # 轉為 Tensor 並送入 GPU
        img_tensor = torch.from_numpy(img_gray).unsqueeze(0).unsqueeze(0).to(ModelConfig.DEVICE).float() / 255.0
        
        with torch.no_grad():
            # 2. 模擬模型內部前向傳播
            processed = model.preprocessor(img_tensor)
            # 這裡模擬 forward 的溫度控制 (Warmup 時通常溫度較高，但評估模式建議 1.0)
            output_dict = model(img_tensor, temperature=1.0)
            stn_out, theta, grid_coords = model.stn(processed)
            enhanced = torch.sigmoid((stn_out - 0.5) * 12.0)
            # 建立參考網格 (如果類別內沒定義，就在函數內臨時建立)
            h, w = ModelConfig.IMAGE_HEIGHT, ModelConfig.IMAGE_WIDTH
            grid_canvas = np.zeros((h, w), dtype=np.float32)
            # 畫上白色網格線
            for x in range(0, w, 20): cv2.line(grid_canvas, (x, 0), (x, h), 1.0, 1)
            for y in range(0, h, 20): cv2.line(grid_canvas, (0, y), (w, y), 1.0, 1)
            grid_ref = torch.from_numpy(grid_canvas).view(1, 1, h, w).to(ModelConfig.DEVICE)

            # 宣告 grid_viz_tensor：使用 STN 產生的 grid_coords 來變換參考網格
            grid_viz_tensor = F.grid_sample(grid_ref, grid_coords, align_corners=False)
            
            # 3. 提取 CNN 特徵 (取 Block 1 的第一個 Conv 層)
            # feature_extractor[0] 是 Conv2d(1, 64, ...)
            features_raw = model.feature_extractor[0](enhanced) 
            
            # 4. 建立 4x4 的特徵網格 (共 16 個通道)
            ch_to_show = 16
            f_maps = features_raw[0, :ch_to_show].cpu().numpy()
            
            # 拼接網格邏輯
            rows = []
            for r in range(4):
                row = np.hstack([f_maps[r*4 + c] for c in range(4)])
                rows.append(row)
            grid_all = np.vstack(rows)
            
            # 正規化特徵圖至 0-255 以利視覺化
            grid_norm = cv2.normalize(grid_all, None, 0, 255, cv2.NORM_MINMAX)
            # 使用高斯模糊稍微平滑隨機噪點，讓色塊感減少
            grid_norm = cv2.GaussianBlur(grid_norm, (3, 3), 0).astype(np.uint8)
            # 放大網格讓細節更清楚
            grid_rescaled = cv2.resize(grid_norm, (ModelConfig.IMAGE_WIDTH * 3, ModelConfig.IMAGE_HEIGHT * 3))

        # 5. 影像拼接與顯示
        def to_cv2_img(t):
            # 確保 Tensor 是在 CPU 上，並且去掉所有 Batch/Channel 維度
            # shape 從 (1, 1, H, W) -> (H, W)
            img = t.detach().cpu().squeeze().float().numpy()
            # 針對可能出現的單通道或多維度進行處理
            if len(img.shape) == 3: # 如果剩下 (C, H, W)
                img = img[0]
            # 正規化到 0-255
            img = (img - img.min()) / (img.max() - img.min() + 1e-8)
            return (img * 255).astype(np.uint8)

        # 上排：原始 | STN | 增強 (統一尺寸)
        view_size = (ModelConfig.IMAGE_WIDTH, ModelConfig.IMAGE_HEIGHT) # 200x60
        # 確保三張小圖尺寸絕對一致
        v1 = cv2.resize(img_gray, view_size)
        v2 = cv2.resize(to_cv2_img(stn_out), view_size)
        v3 = cv2.resize(to_cv2_img(grid_viz_tensor), view_size)
        
        # 確保三張圖橫向拼接
        top_row = np.hstack((v1, v2, v3))
        top_row_bgr = cv2.cvtColor(top_row, cv2.COLOR_GRAY2BGR)
        
        # 下排：CNN 特徵網格 (套用熱點圖)
        feat_bgr = cv2.applyColorMap(grid_rescaled, cv2.COLORMAP_JET)
        
        # 垂直拼接 (確保寬度一致)
        canvas_w = top_row_bgr.shape[1] 
        feat_bgr_resized = cv2.resize(feat_bgr, (canvas_w, 400))
        final_view = np.vstack((top_row_bgr, feat_bgr_resized))

        # 6. 繪製文字資訊
        mode_text = "MODE: WARMUP (No Repeat)" if warmup else f"MODE: TRAIN (Diff: {difficulty})"
        info_str = f"Sample: {i+1}/{num_samples} | Label: {label} | Diff: {mode_text}"
        text_color = (0, 255, 255) if warmup else (0, 255, 0)
        cv2.putText(final_view, info_str, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)
        cv2.putText(final_view, "Top: Orig/STN/Enhanced | Bottom: CNN Feature Maps (16ch)", 
                    (15, final_view.shape[0]-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # [修正] 加入視窗初始化與移動
        win_name = "z0916's GPU Ultimate Diagnostic"
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.moveWindow(win_name, -2500, 500) # 移動到左側副螢幕

        # 7. 互動監聽
        cv2.imshow(win_name, final_view)
        
        key = cv2.waitKey(0) & 0xFF
        if key == 27: # ESC 鍵的 ASCII
            print(">>> 診斷已提前結束。")
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    # 確保多進程在 Windows 下正常運作
    import multiprocessing
    multiprocessing.freeze_support()
    
    # 模式 A：單純查看預處理效果 (不啟動訓練)
    # visualize_preprocessing(num_samples=20, difficulty=0.0, warmup=False)
    
    # 模式 B：執行原本的訓練流程
    main()
