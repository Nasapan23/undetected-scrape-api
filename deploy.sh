#!/bin/bash

# Exit on error
set -e

# Print commands
set -x

# Create necessary directories
mkdir -p data/cookies
mkdir -p logs

# Check if env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp env.example .env
    echo "Please edit .env file with your configuration"
    exit 1
fi

# Build and start the Docker containers
docker-compose up -d --build

# Display container status
docker-compose ps

echo "Undetected Scrape API is running!"
echo "Access the API at: http://localhost:5000"
echo "Health check endpoint: http://localhost:5000/health"
echo "Logs can be viewed with: docker-compose logs -f" 