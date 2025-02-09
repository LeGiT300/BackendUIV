import cv2 as cv
import pytesseract
import re
from PIL import Image

img = cv.imread('1Hwp3YIK.jpg')
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