import pytesseract
import PIL.Image
import PIL.ImageDraw
from PIL import *
from PIL import ImageEnhance
from PIL import Image
import cv2


# Important variables
user_tesseract_cmd = r"D:\Program Files\Tesseract-OCR\tesseract.exe"
show_image = False


# ------- DO NOT EDIT BELOW -------


# Code from https://stackoverflow.max-everyday.com/2019/06/python-opencv-denoising/
def getPixel(image, x, y, G, N):
    L = image.getpixel((x, y))
    if L > G:
        L = True
    else:
        L = False

    nearDots = 0
    if L == (image.getpixel((x - 1, y - 1)) > G):
        nearDots += 1
    if L == (image.getpixel((x - 1, y)) > G):
        nearDots += 1
    if L == (image.getpixel((x - 1, y + 1)) > G):
        nearDots += 1
    if L == (image.getpixel((x, y - 1)) > G):
        nearDots += 1
    if L == (image.getpixel((x, y + 1)) > G):
        nearDots += 1
    if L == (image.getpixel((x + 1, y - 1)) > G):
        nearDots += 1
    if L == (image.getpixel((x + 1, y)) > G):
        nearDots += 1
    if L == (image.getpixel((x + 1, y + 1)) > G):
        nearDots += 1

    if nearDots < N:
        return image.getpixel((x, y - 1))
    else:
        return None


# 降噪 Function
def clearNoise(image, G, N, Z):
    draw = PIL.ImageDraw.Draw(image)

    for i in range(0, Z):
        for x in range(1, image.size[0] - 1):
            for y in range(1, image.size[1] - 1):
                color = getPixel(image, x, y, G, N)
                if color != None:
                    draw.point((x, y), color)

    return image


class CaptchaBroker:

    def decode(self, image_path):
        # open image
        image = Image.open(image_path)

        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(3.0)
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(10.0)

        im2 = image.convert("1")
        im2 = clearNoise(im2, 50, 4, 20)

        w, h = image.size

        if True:
            im2.show()

        # Very important, tesseract-ocr path here
        pytesseract.pytesseract.tesseract_cmd = user_tesseract_cmd
        code = pytesseract.image_to_string(im2)
        print(code)
        return code


if __name__ == "__main__":
    CaptchaBroker.decode(self=1, image_path="try1.png")
