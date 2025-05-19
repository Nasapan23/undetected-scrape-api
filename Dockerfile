FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    curl \
    git \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libxkbcommon0 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Update pip and install dependencies with better error handling
RUN pip install --upgrade pip && \
    pip install -U setuptools wheel && \
    # Handle dependency conflicts more gracefully
    pip install --no-cache-dir -r requirements.txt || \
    # If that fails, try installing one by one
    (echo "Attempting to install packages individually" && \
     (grep -v "^#" requirements.txt | xargs -n 1 pip install --no-cache-dir || true))

# Install Playwright browsers with minimal footprint
RUN mkdir -p /ms-playwright && \
    pip install playwright==1.40.0 && \
    playwright install chromium && \
    playwright install-deps chromium && \
    # Clean up browser cache
    rm -rf /root/.cache/ms-playwright/firefox* && \
    rm -rf /root/.cache/ms-playwright/webkit*

# Copy the rest of the application
COPY . .

# Create data directories
RUN mkdir -p data/cookies

# Expose port
EXPOSE 5000

# Set health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application with Gunicorn in production
CMD ["gunicorn", "--config", "config/gunicorn.conf.py", "wsgi:app"] 