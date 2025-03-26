FROM python:3.11-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the ambient.txt file
COPY ambient.txt .

# Copy the rest of the application
COPY . .

# Create directory for ChromaDB
RUN mkdir -p /app/chroma_db && chmod 777 /app/chroma_db

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 