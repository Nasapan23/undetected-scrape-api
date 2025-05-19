"""
Gunicorn configuration for production deployments
"""
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1)
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2

# Process naming
proc_name = "undetected-scrape-api"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Logging
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
accesslog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Server hooks
def on_starting(server):
    """
    Log when server starts
    """
    print("Starting Undetected Scrape API server")

def on_exit(server):
    """
    Log when server exits
    """
    print("Stopping Undetected Scrape API server")

def post_fork(server, worker):
    """
    Prepare worker after fork
    """
    server.log.info("Worker spawned (pid: %s)", worker.pid)

# Max requests per worker before restart to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Increase this for performance but reduce for more even load balancing
preload_app = True 