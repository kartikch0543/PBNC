FROM python:3.11-slim

WORKDIR /app

# Install system utilities and fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY backend/ /app/backend/
COPY frontend/dist/ /app/frontend/dist/

ENV PYTHONPATH=/app/backend
ENV ENVIRONMENT=production

EXPOSE 8000

WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
