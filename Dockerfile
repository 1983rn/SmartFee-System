# Use official Python runtime
FROM python:3.11.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=wsgi.py \
    FLASK_ENV=production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create instance and static directories
RUN mkdir -p instance static && chmod -R 755 static

# Copy project
COPY . .

# Create non-root user
RUN useradd -m smartfee
RUN chown -R smartfee:smartfee /app
USER smartfee

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5000}/health || exit 1

# Run with gunicorn
CMD gunicorn --bind 0.0.0.0:${PORT:-5000} \
    --workers=${WORKERS:-2} \
    --timeout=${TIMEOUT:-120} \
    --access-logfile=- \
    --error-logfile=- \
    --config=gunicorn_config.py \
    wsgi:app
