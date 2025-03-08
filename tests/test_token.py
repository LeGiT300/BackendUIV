import requests
import os
from pathlib import Path

def test_generate_token():
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    url = 'http://127.0.0.1:5000/generate-token'
    user_id = "1"
    
    # Use Path for cross-platform path handling
    selfie_path = project_root / "meeee.jpg"
    
    if not selfie_path.exists():
        print(f"Error: Image not found at {selfie_path}")
        return
        
    try:
        files = {
            'selfie': (selfie_path.name, open(selfie_path, 'rb'), 'image/jpeg')
        }
        data = {
            'userId': user_id
        }
        
        response = requests.post(url, files=files, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
    except requests.ConnectionError:
        print("Error: Server not running. Start Flask server first.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_generate_token()