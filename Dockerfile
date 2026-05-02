# Use a lightweight Python image
FROM python:3.11-slim

# Install system dependencies needed for Swiss Ephemeris (C-libraries)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your logic
COPY . .

# Expose the port for your "Local API"
EXPOSE 8000

# Start the engine
CMD ["uvicorn", "main.py:app", "--host", "0.0.0.0", "--port", "8000"]