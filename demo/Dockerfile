# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including FFmpeg and FLAC for audio processing
RUN apt-get update && apt-get install -y \
  curl \
  ffmpeg \
  flac \
  && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
  && chown -R app:app /app
USER app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --user --upgrade -r requirements.txt

# Add user's pip install location to PATH
ENV PATH="/home/app/.local/bin:${PATH}"

# Copy application files
COPY --chown=app:app . .

EXPOSE 8001

# Healthcheck using curl
HEALTHCHECK CMD curl --fail http://localhost:8001/_stcore/health

# Run as non-root user
ENTRYPOINT ["streamlit", "run", "Hello.py", "--server.port=8001", "--server.address=0.0.0.0"]