"""
Health check endpoints for the API
"""
from flask import Blueprint, jsonify, current_app
import os
import platform
import psutil
import time

bp = Blueprint("health", __name__, url_prefix="/health")

start_time = time.time()

@bp.route("/", methods=["GET"])
def health():
    """
    Basic health check
    
    Returns:
        JSON: Status and basic health information
    """
    return jsonify({
        "status": "ok",
        "service": "undetected-scrape-api",
        "uptime": time.time() - start_time
    })

@bp.route("/detailed", methods=["GET"])
def detailed_health():
    """
    Detailed health check with system metrics
    
    Returns:
        JSON: Detailed system health information
    """
    # Only collect detailed stats if explicitly requested
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    
    return jsonify({
        "status": "ok",
        "service": "undetected-scrape-api",
        "uptime": time.time() - start_time,
        "system": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_usage": {
                "rss": mem_info.rss / 1024 / 1024,  # MB
                "vms": mem_info.vms / 1024 / 1024,  # MB
            },
            "disk_usage": {
                "total": psutil.disk_usage('/').total / 1024 / 1024 / 1024,  # GB
                "used": psutil.disk_usage('/').used / 1024 / 1024 / 1024,  # GB
                "free": psutil.disk_usage('/').free / 1024 / 1024 / 1024,  # GB
                "percent": psutil.disk_usage('/').percent
            }
        }
    }) 