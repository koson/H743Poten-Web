# H743Poten Web Interface - Docker Image
# Optimized for Raspberry Pi deployment and development

FROM python:3.11-slim

LABEL maintainer="H743Poten Development Team"
LABEL description="H743Poten Web Interface - Potentiostat Control for Raspberry Pi"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    udev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Create user for running the application (security best practice)
RUN useradd -m -u 1000 h743user && chown -R h743user:h743user /app
USER h743user

# Expose Flask port
EXPOSE 8080

# Set environment variables for Docker
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Default command - run production server
CMD ["python", "src/run_app.py"]
