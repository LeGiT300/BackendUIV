# Use Python 3.8 as base image
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies including git for dlib installation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    tesseract-ocr \
    python3-opencv \
    && rm -rf /var/lib/apt/lists/*

# Clone and install dlib from source
RUN git clone https://github.com/davisking/dlib.git && \
    cd dlib && \
    git checkout v19.24.2 && \
    mkdir build && cd build && \
    cmake .. && \
    cmake --build . --config Release && \
    cd .. && \
    python setup.py install && \
    cd .. && \
    rm -rf dlib

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/uploads/front \
    /app/uploads/back \
    /app/uploads/selfies \
    /app/logs

# Copy project files
COPY src/ /app/src/
COPY tests/ /app/tests/

# Set permissions
RUN chmod -R 755 /app/uploads \
    && chmod -R 755 /app/logs

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Set environment variables for Flask
ENV FLASK_APP=src/dataCollection/collect.py \
    FLASK_ENV=production \
    PYTHONPATH=/app

# Command to run the application
CMD ["flask", "run", "--host=0.0.0.0"]