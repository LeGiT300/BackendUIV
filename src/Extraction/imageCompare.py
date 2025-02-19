import cv2 
import face_recognition

# Load images with validation
class Image_compare:
    def compare(self, Selfie, ID_Image):

        id_path = Selfie
        live_path = ID_Image  # Use a different image

        id_image = cv2.imread(id_path)
        if id_image is None:
            print(f"Error loading ID image from {id_path}")
            exit()

        live_image = cv2.imread(live_path)
        if live_image is None:
            print(f"Error loading live image from {live_path}")
            exit()

        # Convert to RGB
        id_rgb = cv2.cvtColor(id_image, cv2.COLOR_BGR2RGB)
        live_rgb = cv2.cvtColor(live_image, cv2.COLOR_BGR2RGB)

        # Detect faces
        id_face_locations = face_recognition.face_locations(id_rgb)
        live_face_locations = face_recognition.face_locations(live_rgb)

        if not id_face_locations:
            print("No face found in ID image.")
        elif not live_face_locations:
            print("No face found in live image.")
        else:
            # Encode first face in each image
            id_encoding = face_recognition.face_encodings(id_rgb, [id_face_locations[0]])[0]
            live_encoding = face_recognition.face_encodings(live_rgb, [live_face_locations[0]])[0]

            # Compare with adjusted tolerance
            match = face_recognition.compare_faces([id_encoding], live_encoding, tolerance=0.5)[0]
            distance = face_recognition.face_distance([id_encoding], live_encoding)[0]

            print(f"Match: {match}, Distance: {distance:.4f}")

        return match

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