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
│   │   └── flaskSQL.py         # Database models and configuration
│   ├── Extraction/
│   │   ├── imageCompare.py     # Facial recognition comparison
│   │   └── imageO.py           # OCR and image processing
│   └── dataCollection/
│       └── collect.py          # Main Flask application routes
├── uploads/
│   ├── front/                  # Front document images
│   ├── back/                   # Back document images
│   └── selfies/               # User selfie images
├── tests/                     # Test files
├── logs/                     # Application logs
├── requirements.txt          # Project dependencies
├── LICENSE                  # MIT License
└── README.md               # This file
```

## Prerequisites

### System Requirements

- Python 3.8 or higher
- Tesseract OCR engine
- Visual Studio Build Tools (for Windows)
- SQLite database

### Required Software

1. **Visual Studio Build Tools**
   - Download from [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - Select "Desktop development with C++"

2. **Tesseract OCR**
   ```batch
   winget install UB-Mannheim.TesseractOCR
   ```

## Installation

1. **Clone the repository**
   ```batch
   git clone [repository-url]
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

4. **Environment Setup**
   Create a `.env` file in the root directory:
   ```env
   JWT_SECRET_KEY=your_secret_key
   JWT_TOKEN=your_jwt_token
   ```

## Usage

### Starting the Server

```batch
python src/dataCollection/collect.py
```

### API Endpoints

#### POST /get-documents
Process and store user documents
- **Content-Type:** `multipart/form-data`
- **Body:**
  - `documentFront`: Front of ID document
  - `documentBack`: Back of ID document

#### POST /generate-token
Generate authentication token using facial verification
- **Content-Type:** `multipart/form-data`
- **Body:**
  - `userId`: User ID
  - `selfie`: User selfie image

#### GET /verify-user
Verify user token and retrieve user details
- **Headers:**
  - `Authorization`: Bearer token

## Development

### Running Tests

```batch
python -m pytest tests/ -v
```

### Logging

Logs are stored in `logs/app.log` with the following information:
- Request details
- Error tracking
- File operations
- Database transactions

## Security Features

- JWT-based authentication
- Secure file upload handling
- Path traversal prevention
- SQL injection protection
- Comprehensive error handling
- Request logging and monitoring

## Contributing

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