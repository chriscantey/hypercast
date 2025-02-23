FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure proper permissions for mounted directories
RUN chown -R nobody:nogroup /app/app/static/audio \
    /app/app/static/images \
    /app/assets \
    /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_DEBUG=false

# Run the application in production mode
CMD ["python", "app.py"]
