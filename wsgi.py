#!/usr/bin/env python3
"""
WSGI entry point for production deployments
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app

app = create_app()

if __name__ == "__main__":
    # For development server only - production should use Gunicorn
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    
    # Use waitress (a production WSGI server) if available
    try:
        from waitress import serve
        print(f"Starting production server on {host}:{port}")
        serve(app, host=host, port=port)
    except ImportError:
        print(f"Waitress not available, using Flask's development server on {host}:{port}")
        app.run(host=host, port=port, debug=debug) 