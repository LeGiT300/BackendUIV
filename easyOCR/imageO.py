import easyocr

reader = easyocr.Reader(['en'], gpu=False)
text = reader.readtext('D:/Smoke_IT/BackEndUIV/easyOCR/1Hwp3YIK.jpg', detail=0, paragraph=True)

print(text)

