#!/usr/bin/env python3
"""
Development entry point for the Undetectable Web Scraping API
"""
import os
from wsgi import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    
    app.run(host=host, port=port, debug=debug) 