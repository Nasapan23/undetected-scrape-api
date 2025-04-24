








































































































"""
Application settings and configuration
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask settings
FLASK_APP = os.getenv("FLASK_APP", "run.py")
FLASK_ENV = os.getenv("FLASK_ENV", "development")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"
SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-change-in-production")

# Server settings
PORT = int(os.getenv("PORT", 5000))
HOST = os.getenv("HOST", "0.0.0.0")

# Playwright settings
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
BROWSER_TYPE = os.getenv("BROWSER_TYPE", "chromium")
USER_AGENT_ROTATION = os.getenv("USER_AGENT_ROTATION", "true").lower() == "true"

# Anti-detection settings (for future use)
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))
NAVIGATION_TIMEOUT = int(os.getenv("NAVIGATION_TIMEOUT", 60000))
WAIT_BEFORE_SCROLLING = float(os.getenv("WAIT_BEFORE_SCROLLING", 2.0))
RANDOM_SCROLL_DELAY_MIN = float(os.getenv("RANDOM_SCROLL_DELAY_MIN", 0.5))
RANDOM_SCROLL_DELAY_MAX = float(os.getenv("RANDOM_SCROLL_DELAY_MAX", 2.0)) 