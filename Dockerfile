# Use the official lightweight Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies required for some Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    libgl1 \
    libglib2.0-0 \
    libpoppler-cpp-dev \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with special handling for reportlab
RUN pip install --upgrade pip && \
    pip install --no-cache-dir wheel setuptools && \
    pip install --no-cache-dir pillow==9.5.0 && \
    pip install --no-cache-dir --only-binary=:all: reportlab==3.6.12 && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make sure the directories exist
RUN mkdir -p data reports assets

# Expose port from Railway
ENV PORT=8000
EXPOSE $PORT

# Start Streamlit (using environment variables set in the script)
CMD streamlit run cannae_dashboard.py
