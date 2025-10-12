# Base image
FROM python:3.11-slim

# Create venv
RUN python -m venv /opt/venv

# Activate it
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Install system dependencies for lxml and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . /app

# Expose port
EXPOSE 8000

# Start server with proper initialization sequence
# 1. Run migrations to ensure schema is up-to-date
# 2. Seed initial data (sources, topics, frameworks) if not exists
# 3. Start the FastAPI server (background jobs will handle article scraping)
# Note: Each step must succeed (&&) before proceeding to the next
CMD ["sh", "-c", "set -e && alembic upgrade head && python -m app.init_db && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

