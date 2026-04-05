# ================================================================
# PART 1: CONFIG + LOGGER + DEBUG UI (ULTRA EXPANDED)
# ================================================================

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

import sys
import numpy as np
import cv2
import os
import time
import math
import random
from collections import deque
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QSlider, QPushButton,
    QVBoxLayout, QHBoxLayout, QCheckBox, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap

# ================================================================
# CONFIG CLASS
# ================================================================

class Config:

    def __init__(self):

        # --------------------------------------------------------
        # DEVICE CONFIG
        # --------------------------------------------------------
        self.DEVICE = self.detect_device()

        # --------------------------------------------------------
        # IMAGE SETTINGS
        # --------------------------------------------------------
        self.IMG_WIDTH = 200
        self.IMG_HEIGHT = 60

        # --------------------------------------------------------
        # TEXT SETTINGS
        # --------------------------------------------------------
        self.MAX_TEXT_LEN = 6

        self.CHARS = "-" + "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

        self.NUM_CLASSES = len(self.CHARS)

        self.CHAR_TO_INDEX = {}
        self.INDEX_TO_CHAR = {}

        self.build_char_maps()

        # --------------------------------------------------------
        # TRAINING SETTINGS
        # --------------------------------------------------------
        self.BATCH_SIZE = 64
        self.EPOCHS = 200

        self.LEARNING_RATE = 0.001

        # --------------------------------------------------------
        # OUTPUT
        # --------------------------------------------------------
        self.OUTPUT_DIR = "output_full_system"

        self.prepare_output_dir()

    # ------------------------------------------------------------
    # DEVICE DETECTION
    # ------------------------------------------------------------

    def detect_device(self):

        if torch.cuda.is_available():
            return torch.device("cuda")
        else:
            return torch.device("cpu")

    # ------------------------------------------------------------
    # CHAR MAP BUILDING
    # ------------------------------------------------------------

    def build_char_maps(self):

        for index in range(len(self.CHARS)):

            char = self.CHARS[index]

            self.CHAR_TO_INDEX[char] = index
            self.INDEX_TO_CHAR[index] = char

    # ------------------------------------------------------------
    # OUTPUT DIR
    # ------------------------------------------------------------

    def prepare_output_dir(self):

        if not os.path.exists(self.OUTPUT_DIR):

            os.makedirs(self.OUTPUT_DIR)

# ================================================================
# LOGGER CLASS
# ================================================================

class TrainingLogger:

    def __init__(self):

        self.loss_history = []
        self.accuracy_history = []
        self.gradient_history = []

    def log_loss(self, value):

        self.loss_history.append(value)

    def log_accuracy(self, value):

        self.accuracy_history.append(value)

    def log_gradient(self, value):

        self.gradient_history.append(value)

    def get_last_loss(self):

        if len(self.loss_history) == 0:
            return 0.0

        return self.loss_history[-1]

    def get_last_accuracy(self):

        if len(self.accuracy_history) == 0:
            return 0.0

        return self.accuracy_history[-1]

    def get_last_gradient(self):

        if len(self.gradient_history) == 0:
            return 0.0

        return self.gradient_history[-1]

# ================================================================
# DEBUG WINDOW
# ================================================================

class DebugWindow:

    def __init__(self):

        self.width = 1200
        self.height = 800

        self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        self.loss_data = deque(maxlen=300)
        self.acc_data = deque(maxlen=300)
        self.grad_data = deque(maxlen=300)

        self.init_window()

    def init_window(self):

        cv2.namedWindow("DEBUG", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("DEBUG", 1000, 700)

    def update(self, loss, acc, grad):

        self.clear()

        self.loss_data.append(loss)
        self.acc_data.append(acc)
        self.grad_data.append(grad)

        self.draw_graph(self.loss_data, (0,0,255), 0)
        self.draw_graph(self.acc_data, (0,255,0), 250)
        self.draw_graph(self.grad_data, (255,0,0), 500)

        self.draw_text(loss, acc, grad)

        cv2.imshow("DEBUG", self.canvas)
        cv2.waitKey(1)

    def clear(self):

        self.canvas.fill(20)

    def draw_graph(self, data, color, y_offset):

        if len(data) < 2:
            return

        for i in range(len(data)-1):

            x1 = int(i / len(data) * self.width)
            x2 = int((i+1) / len(data) * self.width)

            y1 = int(y_offset + 200 - data[i] * 100)
            y2 = int(y_offset + 200 - data[i+1] * 100)

            cv2.line(self.canvas, (x1,y1), (x2,y2), color, 2)

    def draw_text(self, loss, acc, grad):

        cv2.putText(self.canvas, f"LOSS: {loss:.4f}", (20,50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255),2)

        cv2.putText(self.canvas, f"ACC: {acc:.4f}", (20,300),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0),2)

        cv2.putText(self.canvas, f"GRAD: {grad:.4f}", (20,550),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0),2)

# ================================================================
# GRADIENT NORM FUNCTION
# ================================================================

def compute_gradient_norm(model):

    total_norm = 0.0

    for param in model.parameters():

        if param.grad is not None:

            norm = param.grad.data.norm(2)
            total_norm += norm.item() ** 2

    total_norm = total_norm ** 0.5

    return total_norm

# ================================================================
# PART 2: CAPTCHA GENERATOR (ULTRA EXPANDED VERSION)
# ================================================================

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

# ================================================================
# FONT MANAGER
# ================================================================

class FontManager:

    def __init__(self):

        self.font_paths = []
        self.font_objects = []

        self.initialize_font_list()
        self.load_fonts_into_memory()

    # ------------------------------------------------------------
    # INIT FONT PATH LIST
    # ------------------------------------------------------------

    def initialize_font_list(self):

        # 可以自行擴充字體
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_dir = os.path.join(current_dir, "Fonts")   # 你的資料夾名稱
        
        self.font_paths = []   # 很重要（避免殘留）

        if not os.path.exists(font_dir):
            print(f"[WARNING] Font folder not found: {font_dir}")
            return

        for file in os.listdir(font_dir):

            if file.lower().endswith((".ttf", ".otf")):
                
                full_path = os.path.join(font_dir, file)
                
                self.font_paths.append(full_path)

        print(f"[FontManager] Loaded {len(self.font_paths)} fonts")

    # ------------------------------------------------------------
    # LOAD FONTS
    # ------------------------------------------------------------

    def load_fonts_into_memory(self):

        for path in self.font_paths:

            try:
                
                size = random.randint(36, 60)

                font_object = ImageFont.truetype(path, size)

                self.font_objects.append(font_object)

            except:

                continue

        # fallback
        if len(self.font_objects) == 0:
            
            print("⚠️ No fonts loaded, using default")

            default_font = ImageFont.load_default()

            self.font_objects.append(default_font)

    # ------------------------------------------------------------
    # GET RANDOM FONT
    # ------------------------------------------------------------

    def get_random_font(self):

        index = random.randint(0, len(self.font_objects) - 1)

        return self.font_objects[index]


# ================================================================
# CAPTCHA GENERATOR
# ================================================================

class CaptchaGenerator:

    def __init__(self, config):

        self.config = config

        self.font_manager = FontManager()
        
        self.diff = {
            "font": 0,
            "noise": 0,
            "distortion": 0,
            "layout": 0
        }

    # ------------------------------------------------------------
    # RANDOM TEXT
    # ------------------------------------------------------------

    def generate_random_text(self):

        text = ""

        for i in range(self.config.MAX_TEXT_LEN):

            char = random.choice(self.config.CHARS[1:])

            text += char

        return text

    # ------------------------------------------------------------
    # MAIN GENERATION ENTRY
    # ------------------------------------------------------------

    def generate_captcha(self):

        text = self.generate_random_text()

        image = self.create_blank_image()

        image = self.draw_text(image, text)

        # 加這個條件
        if self.diff == {"font": 0,"noise": 0,"distortion": 0,"layout": 0}:
            return np.array(image), text

        image = self.apply_all_noises(image)
        image = self.apply_all_distortions(image)

        return image, text

    # ------------------------------------------------------------
    # CREATE BLANK IMAGE
    # ------------------------------------------------------------

    def create_blank_image(self):

        image = Image.new(
            mode="L",
            size=(self.config.IMG_WIDTH, self.config.IMG_HEIGHT),
            color=255
        )

        return image

    # ------------------------------------------------------------
    # DRAW TEXT
    # ------------------------------------------------------------

    def draw_text(self, image, text):

        draw = ImageDraw.Draw(image)

        current_x = 10

        for index in range(len(text)):

            char = text[index]

            # ✅ 隨機字型大小（跟難度掛勾）
            d = self.diff["font"]
            size = random.randint(24, 36 + d * 5)

            if len(self.font_manager.font_paths) > 0:
                font_path = random.choice(self.font_manager.font_paths)
                try:
                    font = ImageFont.truetype(font_path, size)
                except:
                    font = ImageFont.load_default()
            else:
                font = ImageFont.load_default()

            # ✅ 垂直偏移（更亂）
            max_char_height = 50  # 跟 char_img 一致
            y_offset = random.randint(0, self.config.IMG_HEIGHT - max_char_height)

            # 先畫單字圖（為了旋轉）
            char_img = Image.new("RGBA", (50, 50), (255,255,255,0))
            
            char_draw = ImageDraw.Draw(char_img)

            char_draw.text((10, 10), char, font=font, fill=(0,0,0,255))

            # ✅ 每個字不同旋轉角度
            d = self.diff["font"]
            angle = random.randint(-15 - d * 3, 15 + d * 3)

            char_img = char_img.rotate(angle, expand=True, fillcolor=255)
            
            w, h = char_img.size
            # 防止貼出去
            max_x = self.config.IMG_WIDTH - w
            max_y = self.config.IMG_HEIGHT - h

            safe_x = min(current_x, max_x)
            safe_y = min(y_offset, max_y)

            # 貼回主圖
            image = image.convert("RGBA")
            image.paste(char_img, (safe_x, safe_y), char_img)
            image = image.convert("L")

            # ✅ 字距亂掉（跟難度掛勾）
            d = self.diff["layout"]
            current_x += random.randint(10, 30 + d * 3)
            if current_x > self.config.IMG_WIDTH - 50:
                break

        return image

    # ------------------------------------------------------------
    # APPLY ALL NOISES
    # ------------------------------------------------------------

    def apply_all_noises(self, image):

        np_img = np.array(image)

        np_img = self.apply_line_noise(np_img)

        np_img = self.apply_gaussian_noise(np_img)

        np_img = self.apply_salt_noise(np_img)

        return np_img

    # ------------------------------------------------------------
    # LINE NOISE
    # ------------------------------------------------------------

    def apply_line_noise(self, img):

        d = self.diff["noise"]
        number_of_lines = random.randint(2, 6 + d * 2)

        for i in range(number_of_lines):

            x1 = random.randint(0, self.config.IMG_WIDTH)
            y1 = random.randint(0, self.config.IMG_HEIGHT)

            x2 = random.randint(0, self.config.IMG_WIDTH)
            y2 = random.randint(0, self.config.IMG_HEIGHT)

            color = random.randint(0, 150)

            thickness = random.randint(1, 2)

            cv2.line(img, (x1, y1), (x2, y2), color, thickness)

        return img

    # ------------------------------------------------------------
    # GAUSSIAN NOISE
    # ------------------------------------------------------------

    def apply_gaussian_noise(self, img):

        mean = 0

        d = self.diff["noise"]
        sigma = 10 + d * 3

        gaussian = np.random.normal(mean, sigma, img.shape)

        noisy = img + gaussian

        noisy = np.clip(noisy, 0, 255)

        return noisy.astype(np.uint8)

    # ------------------------------------------------------------
    # SALT NOISE
    # ------------------------------------------------------------

    def apply_salt_noise(self, img):

        d = self.diff["noise"]
        probability = 0.01 + d * 0.005

        noisy = np.copy(img)

        height = img.shape[0]
        width = img.shape[1]

        for i in range(height):

            for j in range(width):

                r = random.random()

                if r < probability:

                    noisy[i][j] = 0

                elif r > 1 - probability:

                    noisy[i][j] = 255

        return noisy

    # ------------------------------------------------------------
    # APPLY DISTORTIONS
    # ------------------------------------------------------------

    def apply_all_distortions(self, img):

        img = self.apply_wave_distortion(img)

        img = self.apply_perspective(img)

        return img

    # ------------------------------------------------------------
    # WAVE DISTORTION
    # ------------------------------------------------------------

    def apply_wave_distortion(self, img):

        height, width = img.shape

        new_img = np.zeros_like(img)

        for row in range(height):

            d = self.diff["distortion"]
            amplitude = 5 + d * 3
            frequency = max(3, 10 - d)

            if frequency < 3:
                frequency = 3

            shift = int(amplitude * math.sin(row / frequency))

            for col in range(width):

                new_col = col + shift

                if new_col >= 0 and new_col < width:

                    new_img[row, new_col] = img[row, col]

        return new_img

    # ------------------------------------------------------------
    # PERSPECTIVE
    # ------------------------------------------------------------

    def apply_perspective(self, img):

        height = img.shape[0]
        width = img.shape[1]

        pts1 = np.array([
            [0, 0],
            [width, 0],
            [0, height],
            [width, height]
        ], dtype=np.float32)

        d = self.diff["distortion"]
        max_shift = 10 + d * 5
        shift = random.randint(-max_shift, max_shift)

        pts2 = np.array([
            [0 + shift, 0],
            [width - shift, 0],
            [0, height],
            [width, height]
        ], dtype=np.float32)

        matrix = cv2.getPerspectiveTransform(pts1, pts2)

        warped = cv2.warpPerspective(img, matrix, (width, height))

        return warped

    # ------------------------------------------------------------
    # DIFFICULTY UPDATE
    # ------------------------------------------------------------

    def update_difficulty(self, epoch):
        if epoch < 40:
            self.diff = {"font": 0,"noise": 0,"distortion": 0,"layout": 0}
        else:
            level = int(epoch / 100)

            if level > 5:
                level = 5

            self.diff = {"font": level,"noise": level,"distortion": level,"layout": level}
            
    def set_difficulty(self, level):
        for k in self.diff:
            self.diff[k] = int(level)
        
# ================================================================
# PART 3: DATASET + CACHE + HARD SAMPLE MINING (ULTRA EXPANDED)
# ================================================================

import torch
from torch.utils.data import Dataset as TorchDataset

# ================================================================
# TEXT ENCODER / DECODER
# ================================================================

class TextEncoder:

    def __init__(self, config):

        self.config = config

    # ------------------------------------------------------------
    # ENCODE TEXT TO INDEX LIST
    # ------------------------------------------------------------

    def encode_text(self, text):

        result = []

        for i in range(len(text)):

            char = text[i]

            index = self.config.CHAR_TO_INDEX[char]

            result.append(index)

        return result

    # ------------------------------------------------------------
    # DECODE INDEX LIST TO STRING
    # ------------------------------------------------------------

    def decode_indices(self, indices):

        text = ""

        for i in range(len(indices)):

            idx = indices[i]

            if idx == 0:
                continue

            char = self.config.INDEX_TO_CHAR[idx]

            text += char

        return text


# ================================================================
# CACHE SYSTEM
# ================================================================

class DatasetCache:

    def __init__(self, max_size=2000):

        self.max_size = max_size

        self.image_list = []
        self.label_list = []
        self.text_list = []

    # ------------------------------------------------------------
    # ADD SAMPLE
    # ------------------------------------------------------------

    def add(self, image, label, text):

        self.image_list.append(image)
        self.label_list.append(label)
        self.text_list.append(text)

        if len(self.image_list) > self.max_size:

            self.image_list.pop(0)
            self.label_list.pop(0)
            self.text_list.pop(0)

    # ------------------------------------------------------------
    # GET RANDOM
    # ------------------------------------------------------------

    def get_random(self):

        if len(self.image_list) == 0:
            return None

        idx = random.randint(0, len(self.image_list) - 1)

        image = self.image_list[idx]
        label = self.label_list[idx]
        text = self.text_list[idx]

        return image, label, text


# ================================================================
# HARD SAMPLE BUFFER
# ================================================================

class HardSampleBuffer:

    def __init__(self, max_size=3000):

        self.max_size = max_size

        self.samples = []

    # ------------------------------------------------------------
    # ADD HARD SAMPLE
    # ------------------------------------------------------------

    def add_sample(self, loss_value, image, label, text):

        item = (loss_value, image, label, text)

        self.samples.append(item)

        # sort by loss (descending)
        self.samples.sort(key=lambda x: x[0], reverse=True)

        if len(self.samples) > self.max_size:

            self.samples = self.samples[:self.max_size]

    # ------------------------------------------------------------
    # SAMPLE FROM HARD SET
    # ------------------------------------------------------------

    def sample(self, num_samples):

        if len(self.samples) == 0:
            return []

        selected = []

        upper = int(len(self.samples) * 0.5)

        if upper <= 0:
            upper = len(self.samples)

        for i in range(num_samples):

            idx = random.randint(0, upper - 1)

            selected.append(self.samples[idx])

        return selected


# ================================================================
# MAIN DATASET
# ================================================================

class CaptchaDataset(TorchDataset):

    def __init__(self, config, size=5000):

        self.config = config

        self.size = size

        self.generator = CaptchaGenerator(config)

        self.encoder = TextEncoder(config)

        self.cache = DatasetCache(max_size=2000)

        self.hard_buffer = HardSampleBuffer(max_size=3000)

    # ------------------------------------------------------------
    # LENGTH
    # ------------------------------------------------------------

    def __len__(self):

        return self.size

    # ------------------------------------------------------------
    # GET ITEM
    # ------------------------------------------------------------

    def __getitem__(self, index):

        # decide path
        if self.should_use_hard_sample():

            sample = self.get_hard_sample()

            if sample is not None:

                image, label, text = sample

                return image, label, text

        if self.should_use_cache():

            sample = self.cache.get_random()

            if sample is not None:

                image, label, text = sample

                return image, label, text

        # fallback: generate
        image, text = self.generate_new()

        label = self.encode_text(text)

        image_tensor = self.prepare_image(image)

        label_tensor = torch.tensor(label, dtype=torch.long)

        self.cache.add(image_tensor, label_tensor, text)

        return image_tensor, label_tensor, text

    # ------------------------------------------------------------
    # DECISION FUNCTIONS
    # ------------------------------------------------------------

    def should_use_cache(self):

        probability = 0.3

        r = random.random()

        if r < probability:
            return True
        else:
            return False

    def should_use_hard_sample(self):

        probability = 0.2

        r = random.random()

        if r < probability:
            return True
        else:
            return False

    # ------------------------------------------------------------
    # HARD SAMPLE FETCH
    # ------------------------------------------------------------

    def get_hard_sample(self):

        samples = self.hard_buffer.sample(1)

        if len(samples) == 0:
            return None

        _, image, label, text = samples[0]

        return image, label, text

    # ------------------------------------------------------------
    # GENERATE NEW SAMPLE
    # ------------------------------------------------------------

    def generate_new(self):

        image, text = self.generator.generate_captcha()

        return image, text

    # ------------------------------------------------------------
    # ENCODE TEXT
    # ------------------------------------------------------------

    def encode_text(self, text):

        encoded = self.encoder.encode_text(text)

        return encoded

    # ------------------------------------------------------------
    # IMAGE PREPROCESS
    # ------------------------------------------------------------

    def prepare_image(self, image):

        image = image.astype(np.float32)

        image = image / 255.0

        image = np.expand_dims(image, axis=0)

        tensor = torch.from_numpy(image)

        return tensor


# ================================================================
# COLLATE FUNCTION (CTC)
# ================================================================

def captcha_collate_fn(batch):

    image_list = []
    label_list = []
    text_list = []

    for item in batch:

        image, label, text = item

        image_list.append(image)
        label_list.append(label)
        text_list.append(text)

    # stack images
    images = torch.stack(image_list)

    # label lengths
    # 用 text 算長度（最準）
    label_lengths = torch.tensor(
        [len(text) for text in text_list],
        dtype=torch.long
    )

    # concat labels
    concat_labels = []

    for label in label_list:
        concat_labels.extend(label.tolist())

    concat_labels = torch.tensor(concat_labels, dtype=torch.long)

    return images, concat_labels, label_lengths, text_list

# ================================================================
# PART 4: MODEL (ULTRA EXPANDED VERSION)
# ================================================================

# ================================================================
# SPATIAL TRANSFORMER NETWORK
# ================================================================

class SpatialTransformerNetwork(nn.Module):

    def __init__(self):

        super(SpatialTransformerNetwork, self).__init__()

        # Conv block 1
        self.conv1 = nn.Conv2d(1, 8, kernel_size=7)
        self.relu1 = nn.ReLU()
        self.pool1 = nn.MaxPool2d(2, 2)

        # Conv block 2
        self.conv2 = nn.Conv2d(8, 10, kernel_size=5)
        self.relu2 = nn.ReLU()
        self.pool2 = nn.MaxPool2d(2, 2)
        
        # 🔥 用 dummy 自動算
        self._init_fc()

        self.fc2 = nn.Linear(32, 6)

        self.initialize_weights()
        
    def _init_fc(self):
        with torch.no_grad():
            dummy = torch.zeros(1, 1, 60, 200)  # 你的輸入尺寸
            x = self.pool1(F.relu(self.conv1(dummy)))
            x = self.pool2(F.relu(self.conv2(x)))

            self.flatten_dim = x.view(1, -1).shape[1]

        self.fc1 = nn.Linear(self.flatten_dim, 32)

    def initialize_weights(self):

        self.fc2.weight.data.zero_()

        identity = torch.tensor(
            [1, 0, 0, 0, 1, 0],
            dtype=torch.float
        )

        self.fc2.bias.data.copy_(identity)

    def forward(self, x):

        xs = self.conv1(x)
        xs = self.relu1(xs)
        xs = self.pool1(xs)

        xs = self.conv2(xs)
        xs = self.relu2(xs)
        xs = self.pool2(xs)

        xs = xs.view(xs.size(0), -1)

        xs = self.fc1(xs)
        xs = F.relu(xs)

        theta = self.fc2(xs)
        theta = theta.view(-1, 2, 3)

        grid = F.affine_grid(theta, x.size(), align_corners=False)

        x_transformed = F.grid_sample(x, grid, align_corners=False)

        return x_transformed


# ================================================================
# CNN BACKBONE
# ================================================================

class CNNBackbone(nn.Module):

    def __init__(self):

        super(CNNBackbone, self).__init__()

        # Block 1
        self.conv1 = nn.Conv2d(1, 64, 3, padding=1)
        self.relu1 = nn.ReLU()
        self.pool1 = nn.MaxPool2d(2, 2)

        # Block 2
        self.conv2 = nn.Conv2d(64, 128, 3, padding=1)
        self.relu2 = nn.ReLU()
        self.pool2 = nn.MaxPool2d(2, 2)

        # Block 3
        self.conv3 = nn.Conv2d(128, 256, 3, padding=1)
        self.relu3 = nn.ReLU()

        self.conv4 = nn.Conv2d(256, 256, 3, padding=1)
        self.relu4 = nn.ReLU()

        self.pool3 = nn.MaxPool2d((2,1), (2,1))

        # Block 4
        self.conv5 = nn.Conv2d(256, 512, 3, padding=1)
        self.relu5 = nn.ReLU()

        self.conv6 = nn.Conv2d(512, 512, 3, padding=1)
        self.relu6 = nn.ReLU()

        self.pool4 = nn.MaxPool2d((2,1), (2,1))

        # Final
        self.conv7 = nn.Conv2d(512, 512, 2)
        self.relu7 = nn.ReLU()

    def forward(self, x):

        x = self.conv1(x)
        x = self.relu1(x)
        x = self.pool1(x)

        x = self.conv2(x)
        x = self.relu2(x)
        x = self.pool2(x)

        x = self.conv3(x)
        x = self.relu3(x)

        x = self.conv4(x)
        x = self.relu4(x)
        x = self.pool3(x)

        x = self.conv5(x)
        x = self.relu5(x)

        x = self.conv6(x)
        x = self.relu6(x)
        x = self.pool4(x)

        x = self.conv7(x)
        x = self.relu7(x)

        return x


# ================================================================
# FEATURE PROCESSOR
# ================================================================

class FeatureProcessor(nn.Module):

    def __init__(self):

        super(FeatureProcessor, self).__init__()

    def forward(self, x):

        batch_size = x.size(0)
        channels = x.size(1)
        height = x.size(2)
        width = x.size(3)

        x = x.permute(3, 0, 1, 2)

        x = x.contiguous()

        x = x.view(width, batch_size, channels * height)

        return x


# ================================================================
# TRANSFORMER ENCODER
# ================================================================

class TransformerEncoderModule(nn.Module):

    def __init__(self):

        super(TransformerEncoderModule, self).__init__()

        self.layer1 = nn.TransformerEncoderLayer(
            d_model=512,
            nhead=8,
            dim_feedforward=1024
        )

        self.layer2 = nn.TransformerEncoderLayer(
            d_model=512,
            nhead=8,
            dim_feedforward=1024
        )

        self.layer3 = nn.TransformerEncoderLayer(
            d_model=512,
            nhead=8,
            dim_feedforward=1024
        )

        self.layer4 = nn.TransformerEncoderLayer(
            d_model=512,
            nhead=8,
            dim_feedforward=1024
        )

    def forward(self, x):

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        return x


# ================================================================
# BiLSTM
# ================================================================

class BiLSTMModule(nn.Module):

    def __init__(self):

        super(BiLSTMModule, self).__init__()

        self.lstm1 = nn.LSTM(
            input_size=512,
            hidden_size=256,
            bidirectional=True
        )

        self.lstm2 = nn.LSTM(
            input_size=512,
            hidden_size=256,
            bidirectional=True
        )

    def forward(self, x):

        x, _ = self.lstm1(x)

        x, _ = self.lstm2(x)

        return x


# ================================================================
# FEATURE FUSION (EXPLICIT)
# ================================================================

class FeatureFusion(nn.Module):

    def __init__(self):

        super(FeatureFusion, self).__init__()

    def forward(self, transformer_feat, lstm_feat):

        fused = transformer_feat + lstm_feat

        return fused


# ================================================================
# FINAL MODEL
# ================================================================

class OCRModel(nn.Module):

    def __init__(self, config):

        super(OCRModel, self).__init__()

        self.config = config

        self.stn = SpatialTransformerNetwork()

        self.cnn = CNNBackbone()

        self.feature_processor = FeatureProcessor()

        self.transformer = TransformerEncoderModule()

        self.lstm = BiLSTMModule()

        self.fusion = FeatureFusion()

        self.fc = nn.Linear(512, config.NUM_CLASSES)
        
        self.proj = nn.Linear(1024, 512)

    def forward(self, x):

        # STN
        x = self.stn(x)

        # CNN
        x = self.cnn(x)

        # reshape
        x = self.feature_processor(x)

        # 
        x = self.proj(x)            # 1024 → 512

        # transformer 要的格式
        x = x.permute(1, 0, 2)      # [W, B, 512]

        # Transformer path
        t_feat = self.transformer(x)

        # LSTM path
        l_feat = self.lstm(x)

        # Fusion
        fused = self.fusion(t_feat, l_feat)

        # Output
        output = self.fc(fused)

        return output
    
# ================================================================
# PART 5: TRAINER (ULTRA EXPANDED)
# ================================================================

from torch.amp.autocast_mode import autocast
from torch.cuda.amp import GradScaler

# ================================================================
# EMA
# ================================================================

class EMA:

    def __init__(self, model, decay=0.999):

        self.decay = decay

        self.shadow_model = OCRModel(model.config)

        self.shadow_model.load_state_dict(model.state_dict())

        self.shadow_model.to(model.config.DEVICE)

    def update(self, model):

        for shadow_param, param in zip(self.shadow_model.parameters(), model.parameters()):

            new_data = self.decay * shadow_param.data + (1.0 - self.decay) * param.data

            shadow_param.data.copy_(new_data)


# ================================================================
# TRAINER
# ================================================================

class Trainer:

    def __init__(self, config, model, raw_model, dataloader):

        self.config = config

        self.model = model
        self.raw_model = raw_model      # EMA 用（原始）

        self.dataloader = dataloader

        self.criterion = nn.CTCLoss(blank=0, zero_infinity=True)

        self.optimizer = optim.Adam(self.model.parameters(), lr=self.config.LEARNING_RATE)

        try:
            # 新版 PyTorch
            from torch.amp.grad_scaler import GradScaler
            self.scaler = GradScaler(
                device="cuda",
                enabled=torch.cuda.is_available()
            )
        except TypeError:
            # 舊版 fallback
            from torch.cuda.amp import GradScaler
            self.scaler = GradScaler(
                enabled=torch.cuda.is_available()
            )

        self.logger = TrainingLogger()

        self.debug_window = DebugWindow()

        self.ema = EMA(self.raw_model)

        self.best_accuracy = 0.0
        
        self.stop_flag = False

    # ------------------------------------------------------------
    # GREEDY DECODE
    # ------------------------------------------------------------

    def greedy_decode(self, outputs):
        
        # (B, T, C) → (T, B, C)
        outputs = outputs.permute(1, 0, 2)

        outputs = outputs.argmax(2)

        time_steps = outputs.shape[0]
        batch_size = outputs.shape[1]

        results = []

        for b in range(batch_size):

            prev = -1
            text = ""

            for t in range(time_steps):

                idx = outputs[t, b].item()

                if idx != prev and idx != 0:

                    char = self.config.INDEX_TO_CHAR[idx]

                    text += char

                prev = idx

            results.append(text)

        return results

    # ------------------------------------------------------------
    # ACCURACY
    # ------------------------------------------------------------

    def compute_accuracy(self, preds, gts):

        correct = 0

        total = len(gts)

        for i in range(total):

            if preds[i] == gts[i]:
                correct += 1

        if total == 0:
            return 0.0

        return correct / total

    # ------------------------------------------------------------
    # TRAIN SINGLE BATCH
    # ------------------------------------------------------------

    def train_batch(self, images, labels, label_lengths, texts):

        images = images.to(self.config.DEVICE)
        labels = labels.to(self.config.DEVICE)

        with autocast(device_type="cuda"):

            outputs = self.model(images)
            
            # log_probs
            log_probs = outputs.log_softmax(2)
            
            log_probs = log_probs.permute(1, 0, 2)

            T, B, C = log_probs.size()

            # input_lengths
            input_lengths = torch.full(
                (B,),
                T,
                dtype=torch.long,
                device=images.device   # 重點
            )
            
            # label_lengths
            label_lengths = label_lengths.to(images.device)

            # labels
            labels = labels.to(images.device)

            loss = self.criterion(
                log_probs,
                labels,
                input_lengths,
                label_lengths
            )

        self.scaler.scale(loss).backward()

        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 5.0)

        self.scaler.step(self.optimizer)
        self.scaler.update()

        self.optimizer.zero_grad()

        return loss, outputs

    # ------------------------------------------------------------
    # HARD SAMPLE UPDATE
    # ------------------------------------------------------------

    def update_hard_samples(self, images, labels, texts, loss_value):

        batch_size = images.size(0)

        pointer = 0

        for i in range(batch_size):

            text = texts[i]

            length = len(text)

            label_slice = labels[pointer:pointer + length]

            pointer += length

            image_cpu = images[i].detach().cpu()
            label_cpu = label_slice.detach().cpu()

            self.dataloader.dataset.hard_buffer.add_sample(
                loss_value,
                image_cpu,
                label_cpu,
                text
            )

    # ------------------------------------------------------------
    # TRAIN LOOP
    # ------------------------------------------------------------

    def train(self, callback=None):

        for epoch in range(self.config.EPOCHS):
            
            if self.stop_flag:
                print("🛑 Training stopped")
                break

            epoch_loss = 0.0
            epoch_acc = 0.0

            for batch_index, (images, labels, label_lengths, texts) in enumerate(self.dataloader):
                
                if self.stop_flag:
                    print("🛑 Training stopped (batch loop)")
                    break

                loss, outputs = self.train_batch(images, labels, label_lengths, texts)

                loss_value = loss.item()

                preds = self.greedy_decode(outputs.detach())

                acc = self.compute_accuracy(preds, texts)
                
                yield {
                    "epoch": epoch,
                    "batch": batch_index,
                    "loss": loss.item(),
                    "acc": acc   # ✅ 加這行
                }

                grad_norm = compute_gradient_norm(self.model)

                self.logger.log_loss(loss_value)
                self.logger.log_accuracy(acc)
                self.logger.log_gradient(grad_norm)

                self.ema.update(self.model)

                self.update_hard_samples(images, labels, texts, loss_value)

                if batch_index % 10 == 0:

                    self.debug_window.update(loss_value, acc, grad_norm)

                    print(
                        f"[E{epoch}] [B{batch_index}] "
                        f"Loss={loss_value:.4f} "
                        f"Acc={acc:.4f} "
                        f"Grad={grad_norm:.4f}"
                    )

                epoch_loss += loss_value
                epoch_acc += acc
                
                if callback is not None and batch_index % 10 == 0:
                    yield({
                        "loss": loss_value,
                        "acc": acc,
                        "grad": grad_norm,
                        "epoch": epoch,
                        "batch": batch_index
                    })

            epoch_loss = epoch_loss / len(self.dataloader)
            epoch_acc = epoch_acc / len(self.dataloader)

            print(f"\n[EPOCH {epoch}] LOSS={epoch_loss:.4f} ACC={epoch_acc:.4f}")

            self.evaluate(epoch)

    # ------------------------------------------------------------
    # EVALUATE
    # ------------------------------------------------------------

    def evaluate(self, epoch):

        self.ema.shadow_model.eval()

        total_acc = 0.0
        count = 0

        with torch.no_grad():

            for images, labels, label_lengths, texts in self.dataloader:

                images = images.to(self.config.DEVICE)

                outputs = self.ema.shadow_model(images)

                preds = self.greedy_decode(outputs)

                acc = self.compute_accuracy(preds, texts)

                total_acc += acc
                count += 1

        final_acc = total_acc / count

        print(f"[EPOCH {epoch}] EMA ACC={final_acc:.4f}")

        if final_acc < self.best_accuracy:

            print("⚠️ Overfitting warning")

        if final_acc > self.best_accuracy:

            self.best_accuracy = final_acc

            path = os.path.join(self.config.OUTPUT_DIR, "best_model.pth")

            torch.save(self.ema.shadow_model.state_dict(), path)

            print("✅ Saved best model")
            
# ================================================================
# PART 6: BEAM SEARCH + INFERENCE (ULTRA EXPANDED)
# ================================================================

# ================================================================
# BEAM SEARCH DECODER
# ================================================================

class BeamSearchDecoder:

    def __init__(self, config, beam_width=10):

        self.config = config

        self.beam_width = beam_width

    # ------------------------------------------------------------
    # DECODE FUNCTION
    # ------------------------------------------------------------

    def decode(self, probs):

        time_steps = probs.shape[0]
        num_classes = probs.shape[1]

        beams = []

        # 初始 beam
        beams.append(("", 0.0))

        # --------------------------------------------------------
        # 時序展開
        # --------------------------------------------------------

        for t in range(time_steps):

            new_beams = []

            for beam_index in range(len(beams)):

                seq, score = beams[beam_index]

                for c in range(num_classes):

                    char = self.config.INDEX_TO_CHAR[c]

                    if c == 0:
                        new_seq = seq
                    else:
                        new_seq = seq + char

                    prob = probs[t, c]

                    if prob <= 0:
                        prob = 1e-9

                    new_score = score + math.log(prob)

                    new_beams.append((new_seq, new_score))

            # ----------------------------------------------------
            # 排序 + 截斷
            # ----------------------------------------------------

            new_beams = sorted(
                new_beams,
                key=lambda x: x[1],
                reverse=True
            )

            beams = new_beams[:self.beam_width]

        best_sequence = beams[0][0]

        return best_sequence


# ================================================================
# INFERENCE ENGINE
# ================================================================

class InferenceEngine:

    def __init__(self, config, model_path):

        self.config = config

        self.model = OCRModel(config)

        self.load_model(model_path)

        self.decoder = BeamSearchDecoder(config)

    # ------------------------------------------------------------
    # LOAD MODEL
    # ------------------------------------------------------------

    def load_model(self, model_path):

        state_dict = torch.load(model_path, map_location=self.config.DEVICE)

        self.model.load_state_dict(state_dict)

        self.model.to(self.config.DEVICE)

        self.model.eval()

    # ------------------------------------------------------------
    # PREPROCESS SINGLE IMAGE
    # ------------------------------------------------------------

    def preprocess_single(self, image):

        resized = cv2.resize(
            image,
            (self.config.IMG_WIDTH, self.config.IMG_HEIGHT)
        )

        normalized = resized.astype(np.float32) / 255.0

        expanded = np.expand_dims(normalized, axis=0)

        expanded = np.expand_dims(expanded, axis=0)

        tensor = torch.from_numpy(expanded)

        tensor = tensor.to(self.config.DEVICE)

        return tensor

    # ------------------------------------------------------------
    # POSTPROCESS OUTPUT
    # ------------------------------------------------------------

    def postprocess_output(self, output):

        probs = output.softmax(2)

        probs = probs.detach().cpu().numpy()

        sequence = probs[:, 0, :]

        decoded = self.decoder.decode(sequence)

        return decoded

    # ------------------------------------------------------------
    # PREDICT SINGLE
    # ------------------------------------------------------------

    def predict_single(self, image):

        tensor = self.preprocess_single(image)

        with torch.no_grad():

            output = self.model(tensor)

        text = self.postprocess_output(output)

        return text

    # ------------------------------------------------------------
    # PREDICT BATCH
    # ------------------------------------------------------------

    def predict_batch(self, image_list):

        processed_list = []

        for image in image_list:

            tensor = self.preprocess_single(image)

            processed_list.append(tensor)

        batch_tensor = torch.cat(processed_list, dim=0)

        with torch.no_grad():

            outputs = self.model(batch_tensor)

        results = []

        batch_size = outputs.size(1)

        probs = outputs.softmax(2).cpu().numpy()

        for i in range(batch_size):

            sequence = probs[:, i, :]

            decoded = self.decoder.decode(sequence)

            results.append(decoded)

        return results
    
# ================================================================
# PART 7: VISUALIZATION SYSTEM (ULTRA EXPANDED)
# ================================================================

# ================================================================
# VISUALIZER CLASS
# ================================================================

class Visualizer:

    def __init__(self):

        self.window_name = "OCR VISUALIZER"

        self.window_initialized = False

        self.init_window()

    # ------------------------------------------------------------
    # INIT WINDOW
    # ------------------------------------------------------------

    def init_window(self):

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

        cv2.resizeWindow(self.window_name, 1200, 800)

        self.window_initialized = True

    # ------------------------------------------------------------
    # DRAW TEXT ON IMAGE
    # ------------------------------------------------------------

    def draw_text(self, image, text, position, color):

        cv2.putText(
            image,
            text,
            position,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color,
            2
        )

    # ------------------------------------------------------------
    # SINGLE PREDICTION DISPLAY
    # ------------------------------------------------------------

    def show_single(self, image, prediction, ground_truth=None):

        display = self.prepare_display_image(image)

        self.draw_text(display, f"Pred: {prediction}", (10, 30), (0, 255, 0))

        if ground_truth is not None:

            color = (0, 255, 0)

            if prediction != ground_truth:
                color = (0, 0, 255)

            self.draw_text(display, f"GT: {ground_truth}", (10, 60), color)

        cv2.imshow(self.window_name, display)
        cv2.waitKey(0)

    # ------------------------------------------------------------
    # PREPARE IMAGE
    # ------------------------------------------------------------

    def prepare_display_image(self, image):

        if len(image.shape) == 2:

            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        resized = cv2.resize(image, (400, 120))

        return resized

    # ------------------------------------------------------------
    # BATCH DISPLAY
    # ------------------------------------------------------------

    def show_batch(self, images, predictions, ground_truths=None):

        rows = []

        current_row = []

        for i in range(len(images)):

            img = self.prepare_display_image(images[i])

            pred = predictions[i]

            if ground_truths is not None:

                gt = ground_truths[i]

                color = (0, 255, 0)

                if pred != gt:
                    color = (0, 0, 255)

                self.draw_text(img, f"P:{pred}", (5, 20), color)
                self.draw_text(img, f"G:{gt}", (5, 45), color)

            else:

                self.draw_text(img, f"P:{pred}", (5, 20), (0, 255, 0))

            current_row.append(img)

            if len(current_row) == 3:

                row_img = np.hstack(current_row)

                rows.append(row_img)

                current_row = []

        if len(current_row) > 0:

            row_img = np.hstack(current_row)

            rows.append(row_img)

        final = np.vstack(rows)

        cv2.imshow(self.window_name, final)
        cv2.waitKey(0)

    # ------------------------------------------------------------
    # SAVE IMAGE
    # ------------------------------------------------------------

    def save_image(self, image, prediction, path):

        display = self.prepare_display_image(image)

        self.draw_text(display, prediction, (10, 30), (0, 255, 0))

        cv2.imwrite(path, display)

    # ------------------------------------------------------------
    # SAVE BATCH
    # ------------------------------------------------------------

    def save_batch(self, images, predictions, folder):

        if not os.path.exists(folder):
            os.makedirs(folder)

        for i in range(len(images)):

            filename = os.path.join(folder, f"sample_{i}.png")

            self.save_image(images[i], predictions[i], filename)

    # ------------------------------------------------------------
    # ERROR ANALYSIS
    # ------------------------------------------------------------

    def show_errors(self, images, preds, gts):

        error_images = []
        error_preds = []
        error_gts = []

        for i in range(len(preds)):

            if preds[i] != gts[i]:

                error_images.append(images[i])
                error_preds.append(preds[i])
                error_gts.append(gts[i])

        if len(error_images) == 0:

            print("No errors found")

            return

        self.show_batch(error_images, error_preds, error_gts)

    # ------------------------------------------------------------
    # GRID VISUALIZATION
    # ------------------------------------------------------------

    def show_grid(self, images):

        resized_images = []

        for img in images:

            resized = self.prepare_display_image(img)

            resized_images.append(resized)

        rows = []

        for i in range(0, len(resized_images), 5):

            row = resized_images[i:i+5]

            if len(row) < 5:
                continue

            rows.append(np.hstack(row))

        if len(rows) == 0:
            return

        grid = np.vstack(rows)

        cv2.imshow(self.window_name, grid)
        cv2.waitKey(0)

    # ------------------------------------------------------------
    # LIVE DISPLAY (NON-BLOCKING)
    # ------------------------------------------------------------

    def show_live(self, image, prediction):

        display = self.prepare_display_image(image)

        self.draw_text(display, prediction, (10, 30), (0, 255, 0))

        cv2.imshow(self.window_name, display)
        cv2.waitKey(1)
        
# ================================================================
# PART 8: MAIN PIPELINE (ULTRA EXPANDED)
# ================================================================

# ================================================================
# debug
# ================================================================

class InteractiveCaptchaDebugger:

    def __init__(self, config):

        self.config = config
        self.generator = CaptchaGenerator(config)

        # UI state
        self.font_level = 1
        self.noise_level = 1
        self.distortion_level = 1
        self.layout_level = 1
        
        self.enable_wave = True
        self.enable_perspective = True

        self.window_name = "CAPTCHA DEBUGGER"

        self.init_ui()

    # ------------------------------------------------------------
    # UI 初始化
    # ------------------------------------------------------------

    def init_ui(self):

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 1000, 300)

        # slider (0~10)
        cv2.createTrackbar("Font", self.window_name, 1, 10, lambda v: setattr(self, "font_level", v))
        cv2.createTrackbar("Noise", self.window_name, 1, 10, lambda v: setattr(self, "noise_level", v))
        cv2.createTrackbar("Distortion", self.window_name, 1, 10, lambda v: setattr(self, "distortion_level", v))
        cv2.createTrackbar("Layout", self.window_name, 1, 10, lambda v: setattr(self, "layout_level", v))

    def on_trackbar(self, val):

        self.noise_level = max(0, val)

    # ------------------------------------------------------------
    # 生成 pipeline（可控版）
    # ------------------------------------------------------------

    def generate_pipeline(self):

        text = self.generator.generate_random_text()

        # STEP 1: blank
        step0 = self.generator.create_blank_image()

        # STEP 2: text
        step1 = self.generator.draw_text(step0.copy(), text)

        step1_np = np.array(step1)

        # STEP 3: noise
        self.generator.diff["font"] = self.font_level
        self.generator.diff["noise"] = self.noise_level
        self.generator.diff["distortion"] = self.distortion_level
        self.generator.diff["layout"] = self.layout_level
        step2 = self.generator.apply_all_noises(step1_np.copy())

        # STEP 4: distortion
        step3 = step2.copy()

        if self.enable_wave:
            step3 = self.generator.apply_wave_distortion(step3)

        if self.enable_perspective:
            step3 = self.generator.apply_perspective(step3)

        return step0, step1_np, step2, step3, text

    # ------------------------------------------------------------
    # 主 loop
    # ------------------------------------------------------------

    def run(self):

        print("=== Interactive Debugger ===")
        print("Keys:")
        print("  [q] quit")
        print("  [r] refresh")
        print("  [w] toggle wave")
        print("  [p] toggle perspective")

        while True:

            step0, step1, step2, step3, text = self.generate_pipeline()

            view = self.build_comparison_view(step0, step1, step2, step3, text)

            cv2.imshow(self.window_name, view)

            key = cv2.waitKey(0) & 0xFF

            if key == ord('q'):
                break

            elif key == ord('r'):
                continue

            elif key == ord('w'):
                self.enable_wave = not self.enable_wave
                print("Wave:", self.enable_wave)

            elif key == ord('p'):
                self.enable_perspective = not self.enable_perspective
                print("Perspective:", self.enable_perspective)

        cv2.destroyAllWindows()

    # ------------------------------------------------------------
    # 顯示用
    # ------------------------------------------------------------

    def prepare_display(self, img, text):

        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        img = cv2.resize(img, (600, 180))

        # UI文字
        cv2.putText(img, f"TEXT: {text}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

        cv2.putText(img, f"F:{self.font_level} N:{self.noise_level} D:{self.distortion_level} L:{self.layout_level}", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)

        cv2.putText(img, f"W:{self.enable_wave} P:{self.enable_perspective}",
                    (10, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,200), 2)

        return img
    
    # ------------------------------------------------------------
    # 多圖拼接
    # ------------------------------------------------------------
    
    def build_comparison_view(self, step0, step1, step2, step3, text):

        def to_bgr(img):
            if len(img.shape) == 2:
                return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            return img

        def resize(img):
            return cv2.resize(img, (250, 80))

        # 轉換
        imgs = [
            ("BLANK", step0),
            ("TEXT", step1),
            ("NOISE", step2),
            ("DISTORT", step3),
        ]

        panels = []

        for title, img in imgs:

            img = to_bgr(np.array(img))
            img = resize(img)

            cv2.putText(img, title, (5, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0,255,255), 1)

            panels.append(img)

        # 拼接
        row = np.hstack(panels)

        # 額外資訊區
        info = np.zeros((100, row.shape[1], 3), dtype=np.uint8)

        cv2.putText(info, f"TEXT: {text}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

        cv2.putText(info,
                    f"F:{self.font_level} | N:{self.noise_level} | D:{self.distortion_level} | L:{self.layout_level} | Wave={self.enable_wave} | Perspective={self.enable_perspective}",
                    (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 2)

        final = np.vstack([row, info])

        return final

# ================================================================
# INITIALIZATION FUNCTIONS
# ================================================================

def initialize_config():

    config = Config()

    print("Config initialized")

    print(f"Device: {config.DEVICE}")
    print(f"Image Size: {config.IMG_WIDTH}x{config.IMG_HEIGHT}")
    print(f"Batch Size: {config.BATCH_SIZE}")

    return config


# ------------------------------------------------------------
# DATASET INIT
# ------------------------------------------------------------

def initialize_dataset(config):

    print("Initializing dataset...")

    dataset = CaptchaDataset(config, size=5000)

    dataloader = torch.utils.data.DataLoader(
        dataset,
        batch_size=config.BATCH_SIZE,
        shuffle=True,
        num_workers=2,
        collate_fn=captcha_collate_fn
    )

    print("Dataset ready")

    return dataset, dataloader


# ------------------------------------------------------------
# MODEL INIT
# ------------------------------------------------------------

def initialize_model(config):

    print("Building model...")

    raw_model = OCRModel(config)
    raw_model = raw_model.to(config.DEVICE)
    
    model = raw_model

    # Optional compile
    try:

        # model = torch.compile(model)

        print("torch.compile enabled")

    except:

        print("torch.compile not available")

    return model, raw_model


# ------------------------------------------------------------
# TRAINER INIT
# ------------------------------------------------------------

def initialize_trainer(config, model, dataloader):

    print("Initializing trainer...")

    trainer = Trainer(config, model, dataloader)

    return trainer


# ------------------------------------------------------------
# VISUALIZER INIT
# ------------------------------------------------------------

def initialize_visualizer():

    visualizer = Visualizer()

    return visualizer


# ================================================================
# TRAINING PIPELINE
# ================================================================

def run_training(trainer):

    print("Starting training process...")

    start_time = time.time()

    trainer.train()

    end_time = time.time()

    total_time = end_time - start_time

    print(f"Training finished in {total_time:.2f} seconds")


# ================================================================
# SAVE MODEL
# ================================================================

def save_final_model(model, config):

    path = os.path.join(config.OUTPUT_DIR, "final_model.pth")

    torch.save(model.state_dict(), path)

    print(f"Final model saved to {path}")

    return path


# ================================================================
# TEST INFERENCE PIPELINE
# ================================================================

def run_test_inference(config, model_path, visualizer):

    print("Running test inference...")

    generator = CaptchaGenerator(config)

    engine = InferenceEngine(config, model_path)

    images = []
    ground_truths = []
    predictions = []

    for i in range(10):

        image, text = generator.generate_captcha()

        pred = engine.predict_single(image)

        images.append(image)
        ground_truths.append(text)
        predictions.append(pred)

        print(f"[{i}] GT: {text} | Pred: {pred}")

    visualizer.show_batch(images, predictions, ground_truths)

    visualizer.show_errors(images, predictions, ground_truths)


# ================================================================
# BATCH INFERENCE TEST
# ================================================================

def run_batch_inference_test(config, model_path):

    print("Running batch inference test...")

    generator = CaptchaGenerator(config)

    engine = InferenceEngine(config, model_path)

    images = []

    for i in range(16):

        img, _ = generator.generate_captcha()

        images.append(img)

    results = engine.predict_batch(images)

    for i in range(len(results)):

        print(f"Sample {i}: {results[i]}")


# ================================================================
# MAIN FUNCTION
# ================================================================

def main():

    # ------------------------------------------------------------
    # INIT
    # ------------------------------------------------------------

    config = initialize_config()

    dataset, dataloader = initialize_dataset(config)

    model = initialize_model(config)

    trainer = initialize_trainer(config, model, dataloader)

    visualizer = initialize_visualizer()

    # ------------------------------------------------------------
    # TRAIN
    # ------------------------------------------------------------

    run_training(trainer)

    # ------------------------------------------------------------
    # SAVE MODEL
    # ------------------------------------------------------------

    model_path = save_final_model(model, config)

    # ------------------------------------------------------------
    # TEST SINGLE INFERENCE
    # ------------------------------------------------------------

    run_test_inference(config, model_path, visualizer)

    # ------------------------------------------------------------
    # TEST BATCH INFERENCE
    # ------------------------------------------------------------

    run_batch_inference_test(config, model_path)

    print("Pipeline completed successfully")


# ================================================================
# ENTRY POINT
# ================================================================
    
# ================================================================
# PART 9: UTILITY FUNCTIONS (ULTRA EXPANDED)
# ================================================================

# ================================================================
# RANDOM SEED CONTROL
# ================================================================

def set_global_seed(seed):

    random.seed(seed)

    np.random.seed(seed)

    torch.manual_seed(seed)

    if torch.cuda.is_available():

        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    print(f"Global seed set to {seed}")


# ================================================================
# IMAGE AUGMENTATION UTILITIES
# ================================================================

def random_blur(image):

    ksize = random.choice([3, 5])

    blurred = cv2.GaussianBlur(image, (ksize, ksize), 0)

    return blurred


def random_threshold(image):

    _, thresh = cv2.threshold(
        image,
        random.randint(100, 150),
        255,
        cv2.THRESH_BINARY
    )

    return thresh


def random_erode(image):

    kernel = np.ones((2, 2), np.uint8)

    eroded = cv2.erode(image, kernel, iterations=1)

    return eroded


def random_dilate(image):

    kernel = np.ones((2, 2), np.uint8)

    dilated = cv2.dilate(image, kernel, iterations=1)

    return dilated


def apply_random_augmentation(image):

    operations = [
        random_blur,
        random_threshold,
        random_erode,
        random_dilate
    ]

    num_ops = random.randint(1, 3)

    selected = random.sample(operations, num_ops)

    result = image.copy()

    for op in selected:

        result = op(result)

    return result


# ================================================================
# MODEL INSPECTION
# ================================================================

def count_parameters(model):

    total = 0

    for param in model.parameters():

        total += param.numel()

    return total


def print_model_summary(model):

    total_params = count_parameters(model)

    print(f"Total parameters: {total_params}")

    for name, param in model.named_parameters():

        print(f"{name} -> {param.shape}")


# ================================================================
# FPS TEST
# ================================================================

def measure_fps(model, config, num_runs=100):

    model.eval()

    dummy = torch.randn(
        1,
        1,
        config.IMG_HEIGHT,
        config.IMG_WIDTH
    ).to(config.DEVICE)

    start = time.time()

    with torch.no_grad():

        for _ in range(num_runs):

            _ = model(dummy)

    end = time.time()

    total_time = end - start

    fps = num_runs / total_time

    print(f"FPS: {fps:.2f}")


# ================================================================
# DATA CHECK
# ================================================================

def inspect_dataset(dataset, num_samples=5):

    print("Inspecting dataset...")

    for i in range(num_samples):

        image, label, text = dataset[i]

        print(f"Sample {i}")

        print(f"Text: {text}")
        print(f"Label length: {len(label)}")
        print(f"Image shape: {image.shape}")


# ================================================================
# LABEL VALIDATION
# ================================================================

def validate_labels(dataset):

    print("Validating labels...")

    for i in range(100):

        _, label, text = dataset[i]

        if len(label) != len(text):

            print(f"Mismatch at {i}")


# ================================================================
# DEBUG IMAGE SAVE
# ================================================================

def save_debug_image(image, filename):

    if len(image.shape) == 2:

        cv2.imwrite(filename, image)

    else:

        cv2.imwrite(filename, image)


# ================================================================
# BATCH ANALYSIS
# ================================================================

def analyze_batch(images, labels, texts):

    print("Batch Analysis:")

    print(f"Batch size: {len(images)}")

    lengths = [len(t) for t in texts]

    print(f"Avg length: {sum(lengths)/len(lengths):.2f}")

    print(f"Max length: {max(lengths)}")
    print(f"Min length: {min(lengths)}")


# ================================================================
# TENSOR DEBUG
# ================================================================

def debug_tensor(tensor, name="tensor"):

    print(f"--- {name} ---")

    print(f"Shape: {tensor.shape}")

    print(f"Min: {tensor.min().item()}")
    print(f"Max: {tensor.max().item()}")

    print(f"Mean: {tensor.mean().item()}")


# ================================================================
# CHECK GRADIENT FLOW
# ================================================================

def check_gradient_flow(model):

    print("Gradient Flow:")

    for name, param in model.named_parameters():

        if param.grad is not None:

            grad_mean = param.grad.abs().mean().item()

            print(f"{name}: {grad_mean:.6f}")


# ================================================================
# MEMORY USAGE
# ================================================================

def print_memory_usage():

    if torch.cuda.is_available():

        allocated = torch.cuda.memory_allocated() / 1024**2
        reserved = torch.cuda.memory_reserved() / 1024**2

        print(f"GPU Memory - Allocated: {allocated:.2f} MB")
        print(f"GPU Memory - Reserved: {reserved:.2f} MB")
        
# ================================================================
# PART 10: EXPORT + BENCHMARK + STRESS TEST + CLI
# ================================================================

import argparse

# ================================================================
# ONNX EXPORT (ENHANCED)
# ================================================================

def export_to_onnx(model, config, filename="model.onnx"):

    print("Exporting to ONNX...")

    model.eval()

    dummy_input = torch.randn(
        1,
        1,
        config.IMG_HEIGHT,
        config.IMG_WIDTH
    ).to(config.DEVICE)

    output_path = os.path.join(config.OUTPUT_DIR, filename)

    torch.onnx.export(
        model,
        (dummy_input,),   # 注意這個逗號！
        output_path,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch"},
            "output": {0: "batch"}   # ← 這裡順便幫你修一個 bug
        },
        opset_version=11
    )

    print(f"ONNX model saved at {output_path}")


# ================================================================
# BENCHMARK
# ================================================================

def run_benchmark(model, config):

    print("Running benchmark...")

    model.eval()

    dummy = torch.randn(
        config.BATCH_SIZE,
        1,
        config.IMG_HEIGHT,
        config.IMG_WIDTH
    ).to(config.DEVICE)

    warmup = 10

    with torch.no_grad():

        for _ in range(warmup):
            _ = model(dummy)

    start = time.time()

    iterations = 50

    with torch.no_grad():

        for _ in range(iterations):
            _ = model(dummy)

    end = time.time()

    total_time = end - start

    avg_time = total_time / iterations

    print(f"Avg batch time: {avg_time:.4f} sec")
    print(f"Throughput: {config.BATCH_SIZE / avg_time:.2f} samples/sec")


# ================================================================
# STRESS TEST
# ================================================================

def stress_test_inference(engine, num_samples=200):

    print("Running stress test...")

    generator = CaptchaGenerator(engine.config)

    success = 0

    start = time.time()

    for i in range(num_samples):

        img, gt = generator.generate_captcha()

        pred = engine.predict_single(img)

        if pred == gt:
            success += 1

        if i % 20 == 0:

            print(f"[{i}] Acc so far: {success/(i+1):.4f}")

    end = time.time()

    final_acc = success / num_samples

    print(f"Final accuracy: {final_acc:.4f}")
    print(f"Total time: {end - start:.2f}s")


# ================================================================
# AUTO TEST PIPELINE
# ================================================================

def run_auto_test(config, model_path):

    print("Running auto test pipeline...")

    engine = InferenceEngine(config, model_path)

    visualizer = Visualizer()

    generator = CaptchaGenerator(config)

    images = []
    preds = []
    gts = []

    for i in range(20):

        img, gt = generator.generate_captcha()

        pred = engine.predict_single(img)

        images.append(img)
        preds.append(pred)
        gts.append(gt)

    visualizer.show_batch(images, preds, gts)
    visualizer.show_errors(images, preds, gts)


# ================================================================
# CLI INTERFACE
# ================================================================

def run_cli():

    parser = argparse.ArgumentParser(
        description="🔥 CAPTCHA OCR Full System CLI"
    )

    subparsers = parser.add_subparsers(dest="command")

    # =========================================================
    # DEBUG
    # =========================================================
    debug_parser = subparsers.add_parser("debug", help="Interactive debugger")

    debug_parser.add_argument("--noise", type=int, default=1)
    debug_parser.add_argument("--font", type=int, default=1)
    debug_parser.add_argument("--distortion", type=int, default=1)
    debug_parser.add_argument("--layout", type=int, default=1)
    
    debug_parser.add_argument("--wave", action="store_true")
    debug_parser.add_argument("--perspective", action="store_true")

    # =========================================================
    # TRAIN
    # =========================================================
    train_parser = subparsers.add_parser("train", help="Train model")

    # （未來可加 epochs / lr）
    train_parser.add_argument("--epochs", type=int, default=None)

    # =========================================================
    # TEST
    # =========================================================
    test_parser = subparsers.add_parser("test", help="Test model")

    test_parser.add_argument("--model", type=str, required=True)

    # =========================================================
    # BENCHMARK
    # =========================================================
    bench_parser = subparsers.add_parser("benchmark", help="Benchmark model")

    bench_parser.add_argument("--model", type=str, required=True)

    # =========================================================
    # STRESS
    # =========================================================
    stress_parser = subparsers.add_parser("stress", help="Stress test")

    stress_parser.add_argument("--model", type=str, required=True)

    # =========================================================
    # PARSE
    # =========================================================
    args = parser.parse_args()

    config = Config()

    # =========================================================
    # DISPATCH
    # =========================================================
    if args.command == "debug":

        debugger = InteractiveCaptchaDebugger(config)
        
        debugger.font_level = args.font
        debugger.noise_level = args.noise
        debugger.distortion_level = args.distortion
        debugger.layout_level = args.layout
        
        debugger.enable_wave = args.wave
        debugger.enable_perspective = args.perspective

        debugger.run()

    elif args.command == "train":

        if args.epochs is not None:
            config.EPOCHS = args.epochs

        dataset, dataloader = initialize_dataset(config)
        model = initialize_model(config)
        trainer = initialize_trainer(config, model, dataloader)

        trainer.train()

        path = save_final_model(model, config)
        export_to_onnx(model, config)

    elif args.command == "test":

        run_auto_test(config, args.model)

    elif args.command == "benchmark":

        model = OCRModel(config)
        model.load_state_dict(torch.load(args.model, map_location=config.DEVICE))
        model.to(config.DEVICE)

        run_benchmark(model, config)

    elif args.command == "stress":

        engine = InferenceEngine(config, args.model)
        stress_test_inference(engine)

    else:
        parser.print_help()

# ================================================================
# GUI
# ================================================================

class AdvancedCaptchaGUI(QWidget):

    def __init__(self):
        super().__init__()

        self.config = Config()
        self.generator = CaptchaGenerator(self.config)

        self.model, self.raw_model = initialize_model(self.config)
        _, self.dataloader = initialize_dataset(self.config)
        self.trainer = Trainer(
            self.config,
            self.model,
            self.raw_model,
            self.dataloader
        )

        self.engine = None

        self.loss_data = []
        self.acc_data = []

        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_preview)
        self.timer.start(500)

    # =========================================================
    # UI
    # =========================================================
    def init_ui(self):

        self.setWindowTitle("🔥 OCR Studio Pro")
        self.resize(1400, 800)

        layout = QGridLayout()

        # ========= IMAGE =========
        self.image_label = QLabel()
        self.image_label.setFixedSize(600, 200)
        layout.addWidget(self.image_label, 0, 0, 1, 2)

        # ========= GRAPH =========
        self.graph_label = QLabel()
        self.graph_label.setFixedSize(600, 200)
        layout.addWidget(self.graph_label, 1, 0, 1, 2)

        # ========= SLIDERS =========
        self.font_slider = self.create_slider("Font", layout, 0, 2)
        self.noise_slider = self.create_slider("Noise", layout, 1, 2)
        self.dist_slider = self.create_slider("Distortion", layout, 2, 2)
        self.layout_slider = self.create_slider("Layout", layout, 3, 2)

        # ========= BUTTONS =========
        btn_train = QPushButton("🚀 Start Training")
        btn_train.clicked.connect(self.start_training)

        btn_load = QPushButton("📂 Load Model")
        btn_load.clicked.connect(self.load_model)

        btn_predict = QPushButton("🔍 Predict")
        btn_predict.clicked.connect(self.predict)
        
        btn_stop = QPushButton("🛑 Stop Training")
        btn_stop.clicked.connect(self.stop_training)

        layout.addWidget(btn_train, 4, 2)
        layout.addWidget(btn_load, 5, 2)
        layout.addWidget(btn_predict, 6, 2)
        layout.addWidget(btn_stop, 7, 2)  # 位置自己調

        # ========= LOG =========
        self.log_label = QLabel("Logs...")
        self.log_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.log_label.setFixedHeight(200)

        layout.addWidget(self.log_label, 7, 0, 1, 3)

        self.setLayout(layout)

    def create_slider(self, name, layout, row, col):

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMaximum(10)
        slider.setValue(1)

        layout.addWidget(QLabel(name), row, col)
        layout.addWidget(slider, row, col+1)

        return slider
    
    def apply_slider_to_dataset(self):
        dataset = self.trainer.dataloader.dataset
        gen = dataset.generator

        gen.diff["font"] = self.font_slider.value()
        gen.diff["noise"] = self.noise_slider.value()
        gen.diff["distortion"] = self.dist_slider.value()
        gen.diff["layout"] = self.layout_slider.value()
        
    def apply_slider_to_preview(self):
        self.generator.diff["font"] = self.font_slider.value()
        self.generator.diff["noise"] = self.noise_slider.value()
        self.generator.diff["distortion"] = self.dist_slider.value()
        self.generator.diff["layout"] = self.layout_slider.value()

    # =========================================================
    # PREVIEW
    # =========================================================
    def update_preview(self):

        self.font_slider.valueChanged.connect(self.apply_slider_to_preview)
        self.noise_slider.valueChanged.connect(self.apply_slider_to_preview)
        self.dist_slider.valueChanged.connect(self.apply_slider_to_preview)
        self.layout_slider.valueChanged.connect(self.apply_slider_to_preview)

        img, text = self.generator.generate_captcha()

        self.current_img = img
        self.current_text = text

        self.show_image(img)

    def show_image(self, img):

        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

        h, w, ch = img.shape
        qt_img = QImage(img.data, w, h, ch*w, QImage.Format.Format_RGB888)

        self.image_label.setPixmap(QPixmap.fromImage(qt_img))

    # =========================================================
    # TRAINING
    # =========================================================
    def start_training(self):
        
        self.trainer.stop_flag = False
        
        self.apply_slider_to_dataset()   # ← 加這行

        self.worker = TrainWorker(self.trainer)
        self.worker.update_signal.connect(self.update_training_ui)
        print(self.trainer.dataloader.dataset.generator.diff)
        
        self.worker.start()

    def update_training_ui(self, data):
        
        # 先處理「狀態訊號」
        if "status" in data:
            self.log_label.setText("✅ Training Finished")
            return

        loss = data["loss"]
        acc = data["acc"]

        self.loss_data.append(loss)
        self.acc_data.append(acc)

        self.update_graph()

        self.log_label.setText(
            f"Epoch {data['epoch']} | Batch {data['batch']} "
            f"| Loss {loss:.4f} | Acc {acc:.4f}"
        )

    # =========================================================
    # GRAPH
    # =========================================================
    def update_graph(self):

        canvas = np.zeros((200, 600, 3), dtype=np.uint8)

        if len(self.loss_data) < 2:
            return

        for i in range(len(self.loss_data)-1):

            x1 = int(i / len(self.loss_data) * 600)
            x2 = int((i+1) / len(self.loss_data) * 600)

            y1 = int(200 - self.loss_data[i]*100)
            y2 = int(200 - self.loss_data[i+1]*100)

            cv2.line(canvas, (x1,y1), (x2,y2), (0,0,255), 2)

        qt_img = QImage(canvas.data, 600, 200, 3*600, QImage.Format.Format_RGB888)
        self.graph_label.setPixmap(QPixmap.fromImage(qt_img))

    # =========================================================
    # MODEL
    # =========================================================
    def load_model(self):

        path = "output_full_system/best_model.pth"

        if not os.path.exists(path):
            self.log_label.setText("❌ Model not found")
            return

        self.engine = InferenceEngine(self.config, path)

        self.log_label.setText("✅ Model Loaded")

    def predict(self):

        if self.engine is None:
            self.log_label.setText("⚠️ Load model first")
            return

        pred = self.engine.predict_single(self.current_img)

        self.log_label.setText(f"Pred: {pred} | GT: {self.current_text}")
        
    def stop_training(self):
        if hasattr(self, "trainer"):
            self.trainer.stop_flag = True
            self.log_label.setText("🛑 Stopping training...")

class TrainWorker(QThread):

    update_signal = pyqtSignal(dict)

    def __init__(self, trainer):
        super().__init__()
        self.trainer = trainer

    def run(self):

        for data in self.trainer.train():

            self.update_signal.emit(data)

            self.msleep(1)   # 🔥 關鍵：讓UI喘一口氣

        self.update_signal.emit({"status": "finished"})

# =========================================================
# RUN GUI
# =========================================================

def run_gui():
    app = QApplication(sys.argv)
    win = AdvancedCaptchaGUI()
    win.show()
    sys.exit(app.exec())

# ================================================================
# OPTIONAL ENTRY
# ================================================================

if __name__ == "__main__":
    # 路徑要更改 C:/Users/z0916/agent-brain/AItest/python/test/captcha_full.py
    # python C:/Users/z0916/agent-brain/AItest/python/test/captcha_full.py
    # python C:/Users/z0916/agent-brain/AItest/python/test/captcha_full.py debug
    """
    # 🎮 Debug UI
    python captcha_full.py debug --font 3 --noise 6 --distortion 4 --layout 2 --wave --perspective

    # 🧠 訓練
    python captcha_full.py train

    # 🔍 測試
    python captcha_full.py test --model xxx.pth

    # ⚡ Benchmark
    python captcha_full.py benchmark --model xxx.pth

    # 💣 壓力測試
    python captcha_full.py stress --model xxx.pth
    """
    # 可改成 run_cli() 或 main() 或 run_gui()
    # run_cli()
    run_gui()
