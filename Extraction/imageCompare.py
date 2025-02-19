import cv2 
import face_recognition

# Load the ID/passport image and the actual image (e.g., a selfie)
id_images = cv2.imread("D:/Smoke_IT/BackendUIV/Extraction/1Hwp3YIK.jpg")
live_images = cv2.imread("D:/Smoke_IT/BackendUIV/Extraction/1Hwp3YIK.jpg")

id_image = cv2.cvtColor(id_images, cv2.COLOR_BGR2RGB)
live_image = cv2.cvtColor(live_images, cv2.COLOR_BGR2RGB)

# Detect faces in both images
id_face_locations = face_recognition.face_locations(id_image)
live_face_locations = face_recognition.face_locations(live_image)

if id_face_locations and live_face_locations:
    # For simplicity, take the first face found in each image
    id_encoding = face_recognition.face_encodings(id_image, known_face_locations=id_face_locations)[0]
    live_encoding = face_recognition.face_encodings(live_image, known_face_locations=live_face_locations)[0]

    # Compare the faces
    results = face_recognition.compare_faces([id_encoding], live_encoding)
    distance = face_recognition.face_distance([id_encoding], live_encoding)[0]

    print("Match:", results[0], "Distance:", distance)
else:
    print("Face not detected in one of the images.")


# cap = cv.VideoCapture(0)

# if not cap.isOpened:
#     print('Something is wrong with the camera')
#     exit()


# while True:
#     ret, frame = cap.read()

#     if not ret:
#         print('Could not get frames')
#         break

#     cv.imshow('ME', frame)

#     if cv.waitKey(1) & 0xFF == ord('q'):
#         break


# cap.release()
# cv.destroyAllWindows()