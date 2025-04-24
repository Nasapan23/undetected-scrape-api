"""
Flask application factory for the Undetectable Web Scraping API
"""
from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv
from app.utils.logging import configure_logging

# Configure logging
configure_logging()

# Load environment variables
load_dotenv()

def create_app(test_config=None):
    """
    Create and configure the Flask application
    
    Args:
        test_config: Configuration for testing
        
    Returns:
        Flask application instance
    """
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Set default configuration
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev"),
        
        # Browser settings
        HEADLESS=os.getenv("HEADLESS", "true").lower() == "true",
        BROWSER_TYPE=os.getenv("BROWSER_TYPE", "chromium"),
        USER_AGENT_ROTATION=os.getenv("USER_AGENT_ROTATION", "true").lower() == "true",
        
        # Anti-detection settings
        USE_PROXIES=os.getenv("USE_PROXIES", "false").lower() == "true",
        REQUEST_TIMEOUT=int(os.getenv("REQUEST_TIMEOUT", 30)),
        NAVIGATION_TIMEOUT=int(os.getenv("NAVIGATION_TIMEOUT", 60000)),
        WAIT_BEFORE_SCROLLING=float(os.getenv("WAIT_BEFORE_SCROLLING", 2.0)),
        RANDOM_SCROLL_DELAY_MIN=float(os.getenv("RANDOM_SCROLL_DELAY_MIN", 0.5)),
        RANDOM_SCROLL_DELAY_MAX=float(os.getenv("RANDOM_SCROLL_DELAY_MAX", 2.0)),
        
        # Retry configuration
        MAX_RETRIES=int(os.getenv("MAX_RETRIES", 3)),
        RETRY_DELAY=float(os.getenv("RETRY_DELAY", 2.0))
    )
    
    # Apply test config if provided
    if test_config:
        app.config.update(test_config)
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    from app.routes.scrape import bp as scrape_bp
    app.register_blueprint(scrape_bp)
    
    # Initialize browser service
    from app.services.browser import init_browser
    app.teardown_appcontext(init_browser)
    
    @app.route("/")
    def index():
        """API root endpoint"""
        return {
            "status": "success",
            "message": "Undetectable Web Scraping API is running",
            "version": "1.0.0"
        }
    
    return app 