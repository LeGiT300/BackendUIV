import cv2
import pytesseract


# Set Tesseract path if needed (Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'

class ImageExtractor:
    """ Extract text from images using OCR """
    
    def __init__(self):
        self.last_processed_image = None
        
    def process_and_extract(self, image_path):
        """ Process image and extract text in one step """
        try:
            # Load and preprocess
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Store processed image
            self.last_processed_image = binary
            
            # Perform OCR
            text = pytesseract.image_to_string(binary)
            return text
        except Exception as e:
            return f"Error processing image: {str(e)}"

# Test OCR on an image
# image_path = "D:/Smoke_IT/BackendUIV/ID_card.jpg"
# image_extractor = ImageExtractor()
# text_output = image_extractor.process_and_extract(image_path)
# print("Extracted Text:\n", text_output)
