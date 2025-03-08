import cv2
import face_recognition

class Image_compare:
    def compare(self, id_image_path, selfie_image_path, tolerance=0.5):
        """
        Compare faces between an ID image and a selfie.
        
        Args:
            id_image_path (str): Path to the ID card image
            selfie_image_path (str): Path to the selfie image
            tolerance (float): Threshold for face matching (lower is stricter)
            
        Returns:
            dict: Results containing match status, confidence score, and any error messages
        """
        result = {
            "match": False,
            "distance": None,
            "error": None
        }
        
        # Load images
        try:
            id_image = cv2.imread(id_image_path)
            if id_image is None:
                result["error"] = f"Error loading ID image from {id_image_path}"
                return result
                
            selfie_image = cv2.imread(selfie_image_path)
            if selfie_image is None:
                result["error"] = f"Error loading selfie image from {selfie_image_path}"
                return result
                
            # Convert to RGB (face_recognition uses RGB)
            id_rgb = cv2.cvtColor(id_image, cv2.COLOR_BGR2RGB)
            selfie_rgb = cv2.cvtColor(selfie_image, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            id_face_locations = face_recognition.face_locations(id_rgb)
            selfie_face_locations = face_recognition.face_locations(selfie_rgb)
            
            if not id_face_locations:
                result["error"] = "No face found in ID image"
                return result
                
            if not selfie_face_locations:
                result["error"] = "No face found in selfie image"
                return result
                
            # Encode faces
            try:
                id_encoding = face_recognition.face_encodings(id_rgb, [id_face_locations[0]])[0]
                selfie_encoding = face_recognition.face_encodings(selfie_rgb, [selfie_face_locations[0]])[0]
                
                # Compare faces
                match = face_recognition.compare_faces([id_encoding], selfie_encoding, tolerance=tolerance)[0]
                distance = face_recognition.face_distance([id_encoding], selfie_encoding)[0]
                
                result["match"] = bool(match)
                result["distance"] = float(distance)
                
                return result
                
            except IndexError:
                result["error"] = "Failed to encode faces"
                return result
                
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
            return result