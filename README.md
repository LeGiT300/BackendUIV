# BackendUIV (Backend User Identity Verification)

A robust Flask-based backend service for user identity verification using facial recognition and document processing. This system provides secure document handling, OCR processing, and facial verification capabilities.

## Features

- 🔐 Secure document processing and storage
- 👤 Facial recognition for identity verification
- 📄 OCR-based document text extraction
- 🔑 JWT-based authentication
- 📝 Comprehensive logging system
- 🗄️ SQLite database integration

## Project Structure

```
BackendUIV/
├── src/
│   ├── Database/
│   │   ├── flaskSQL.py         # Database models and configuration
│   │   └── create_db.py        # Database initialization script
│   ├── Extraction/
│   │   ├── imageCompare.py     # Facial recognition comparison
│   │   └── imageO.py           # OCR and image processing
│   └── dataCollection/
│       └── collect.py          # Main Flask application routes
├── uploads/
│   ├── front/                  # Front document images
│   ├── back/                   # Back document images
│   └── selfies/               # User selfie images
├── logs/                     # Application logs
├── requirements.txt          # Project dependencies
├── LICENSE                  # MIT License
└── README.md               # This file
```

## Prerequisites

### System Requirements

- Docker (alternatively: Python 3.8 or higher)
- Tesseract OCR engine (for non-Docker setup)
- Visual Studio Build Tools (for non-Docker setup)
- SQLite database

### Docker Installation

1. **Install Docker Desktop**
   - Download from [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Follow installation instructions for Windows

2. **Build and Run with Docker**
   ```batch
   # Build the image
   docker build -t backendui:latest .

   # Run the container
   docker run -p 5000:5000 -v %cd%/uploads:/app/uploads -v %cd%/logs:/app/logs backendui:latest
   ```

### Manual Installation

1. **Clone the repository**
   ```batch
   git clone https://github.com/LeGiT300/BackendUIV
   cd BackendUIV
   ```

2. **Create and activate virtual environment**
   ```batch
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install dependencies**
   ```batch
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```batch
   python src/Database/create_db.py
   ```

5. **Environment Setup**
   Create a `.env` file in the root directory:
   ```env
   JWT_SECRET_KEY=your_secret_key
   JWT_TOKEN=your_jwt_token
   ```

## API Documentation

### POST /get-documents
Process and store user documents
- **Content-Type:** `multipart/form-data`
- **Body:**
  - `documentFront`: Front of ID document
  - `documentBack`: Back of ID document
  - `document_type`: Document type (ID, Passport or others)
- **Response:**
  ```json
  {
    "name": "extracted_name",
    "date_of_birth": "YYYY-MM-DD",
    "ocr_text": "extracted_text",
    "userId": "user_id",
    "document_type": "document_type"
  }
  ```

### POST /generate-token
Generate authentication token using facial verification. Uses the most recently created user automatically.
- **Content-Type:** `multipart/form-data`
- **Body:**
  - `selfie`: User selfie image for verification
- **Response:**
  ```json
  {
    "access_token": "jwt_token"
  }
  ```
- **Error Responses:**
  ```json
  {
    "error": "No users found. Please complete document registration first."
  }
  ```
  ```json
  {
    "error": "Face verification failed",
    "details": {
      "attempted_paths": ["path1", "path2"],
      "selfie_path": "path/to/selfie",
      "search_locations": [
        "uploads/front",
        "uploads/back",
        "uploads/selfies"
      ]
    }
  }
  ```

### GET /verify-user
Verify user token and retrieve user details
- **Headers:**
  - `Authorization`: Bearer token
- **Response:**
  ```json
  {
    "userId": "user_id",
    "name": "user_name",
    "date_of_birth": "YYYY-MM-DD",
    "verification_status": true,
    "images": ["image_urls"],
    "documents": [
      {
        "url": "document_url",
        "type": "document_type",
        "extracted_text": "text"
      }
    ]
  }
  ```

## Usage Flow

1. **Document Registration:**
   ```bash
   curl -X POST \
     -F "documentFront=@front.jpg" \
     -F "documentBack=@back.jpg" \
     http://localhost:5000/get-documents
   ```

2. **Token Generation:**
   ```bash
   # Use immediately after document registration
   curl -X POST \
     -F "selfie=@selfie.jpg" \
     http://localhost:5000/generate-token
   ```

3. **User Verification:**
   ```bash
   curl -X GET \
     -H "Authorization: Bearer your_token_here" \
     http://localhost:5000/verify-user
   ```

## Development

### Running Tests

```batch
python -m pytest tests/ -v
```

### Docker Development

1. **Build the development image:**
   ```batch
   docker build -t backendui:dev --target development .
   ```

2. **Run with volume mounts for development:**
   ```batch
   docker run -p 5000:5000 -v %cd%:/app backendui:dev
   ```

### Local Development

Logs are stored in `logs/app.log` with detailed information about:
- Request details
- Error tracking
- File operations
- Database transactions
- Face detection results
- OCR processing

## Security Features

- JWT-based authentication with 1-hour token expiry
- Token storage in user profile
- Secure file upload handling
- Path traversal prevention
- SQL injection protection
- Comprehensive error handling
- Face verification with confidence scoring
- Docker container security
  - Non-root user
  - Minimal base image
  - Secure volume mounts

## Additional Files

- `Dockerfile`: Container configuration
- `.dockerignore`: Docker build exclusions
- `docker-compose.yml`: Multi-container setup

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Acknowledgments

- Face Recognition library
- Tesseract OCR
- Flask framework
- SQLAlchemy ORM
