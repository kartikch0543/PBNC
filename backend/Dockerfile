FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies for PDF parsing, image processing, and local OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy application source code
COPY backend /app/backend

# Create upload directory with appropriate permissions
RUN mkdir -p /app/uploads

ENV PYTHONPATH=/app/backend

EXPOSE 8000

# Default command runs the FastAPI server with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
