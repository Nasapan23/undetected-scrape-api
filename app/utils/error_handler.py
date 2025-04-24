"""
Error handling utility functions
"""
from flask import jsonify
from playwright.sync_api import Error as PlaywrightError
from loguru import logger

def handle_error(error):
    """
    Handle exceptions and return appropriate JSON responses
    
    Args:
        error: The exception that was raised
        
    Returns:
        JSON response with error details
    """
    status_code = 500
    error_type = type(error).__name__
    
    # Handle different types of errors
    if isinstance(error, PlaywrightError):
        message = "Browser automation error"
        status_code = 500
    elif isinstance(error, ValueError):
        message = str(error)
        status_code = 400
    elif isinstance(error, ConnectionError):
        message = "Failed to connect to the target website"
        status_code = 502
    else:
        message = "An unexpected error occurred"
    
    # Log the error
    logger.error(f"{error_type}: {str(error)}")
    
    return jsonify({
        "status": "error",
        "error": {
            "type": error_type,
            "message": message
        }
    }), status_code 