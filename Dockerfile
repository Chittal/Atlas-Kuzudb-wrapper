# Dockerfile for KuzuDB Wrapper API
# Optimized for both local development and cloud deployment

# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    CONTAINERIZED=true

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application and database
# Copy application code
COPY app.py config.py requirements.txt run_server.py ./
COPY helper/ ./helper/
COPY routes/ ./routes/

# Copy database file into image
COPY skills_graph.db /app/skills_graph.db

# Create directories for databases and ensure proper permissions
RUN mkdir -p /app/data /app/static /app/templates && \
    chmod -R 755 /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose the port (default 8008, can be overridden with PORT env var)
EXPOSE 8008

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8008}/health || exit 1

# Start the application
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8008}"]
