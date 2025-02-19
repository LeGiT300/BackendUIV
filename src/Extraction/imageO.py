import cv2 as cv
from pytesseract import pytesseract
import re
from PIL import Image

pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'

img = cv.imread('D:/Smoke_IT/BackendUIV/Extraction/employee.jpg')

if img is None:
    print('Path error!')
    exit()


grey = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
thresh = cv.threshold(grey, 0, 255, cv.THRESH_BINARY)[1]

text = pytesseract.image_to_string(thresh)
print('Raw Text from image:\n', text)

name = re.findall(r"Name:\s*(.+?)\n", text, re.IGNORECASE)
id_number = re.findall(r"ID:\s*(\d+[A-Z-]*)", text, re.IGNORECASE)
dob = re.findall(r"\d{2}/\d{2}/\d{4}", text) 

print("\nExtracted Data:")
print(f"Name: {name[0] if name else 'Not found'}")
print(f"ID Number: {id_number[0] if id_number else 'Not found'}")
print(f"DOB: {dob[0] if dob else 'Not found'}")