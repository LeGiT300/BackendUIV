# import easyocr


# reader = easyocr.Reader(['en'])

# reader = easyocr.Reader(['en'],gpu=False)
# result = reader.readtext('D:/Smoke_IT/BackendUIV/WhatsApp Image 2025-02-19 at 13.47.47_099afc4b.jpg', detail=0)
# print(result)


import cv2
import pytesseract
import numpy as np
import keras

# Set Tesseract path if needed (Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'

def preprocess_image(image_path):
    """ Load and preprocess image for OCR """
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # Convert to grayscale
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)  # Binarization
    return binary

def extract_text(image_path):
    """ Extract text using Tesseract OCR """
    processed_image = preprocess_image(image_path)
    text = pytesseract.image_to_string(processed_image)  # OCR
    return text

# Test OCR on an image
image_path = "D:/Smoke_IT/BackendUIV/ID_card.jpg"
text_output = extract_text(image_path)
print("Extracted Text:\n", text_output)
