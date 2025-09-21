FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /shared/data

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV REDIS_HOST=redis-service
ENV REDIS_PORT=6379
ENV SHARED_DATA_PATH=/shared/data

# Expose Streamlit port
EXPOSE 8501

# Health check script
COPY healthcheck.py /healthcheck.py
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python /healthcheck.py || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]