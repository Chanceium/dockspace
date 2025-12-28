"""
Gunicorn configuration file for Dockspace.

This configuration optimizes Gunicorn for multi-core systems with proper
worker/thread configuration, timeouts, and logging.

Performance Tuning:
- Workers: Uses (2 × CPU cores) + 1 formula, capped at 17 for 16-core systems
- Threads: 2-4 threads per worker for handling concurrent requests
- Worker class: sync (compatible with Django, use gthread for more threading)
- Timeout: 60 seconds to handle slow operations
- Graceful timeout: 30 seconds for clean shutdowns
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
# Formula: (2 × CPU cores) + 1
# Use environment variable to override, with a sensible default
cpu_count = multiprocessing.cpu_count()
workers = int(os.getenv("GUNICORN_WORKERS", min((2 * cpu_count) + 1, 17)))

# Worker class and threading
# Use 'gthread' for threaded workers (better for I/O-bound operations)
# Use 'sync' for CPU-bound operations (default)
worker_class = "gthread"
threads = int(os.getenv("GUNICORN_THREADS", 4))  # 4 threads per worker

# Worker configuration
worker_connections = 1000
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", 10000))  # Restart workers after N requests
max_requests_jitter = 1000  # Add randomness to avoid all workers restarting at once

# Timeouts
timeout = int(os.getenv("GUNICORN_TIMEOUT", 60))  # 60 seconds
graceful_timeout = 30  # Time to finish requests during shutdown
keepalive = 5  # Keep-alive timeout

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "dockspace"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed in the future)
# keyfile = None
# certfile = None

# Debugging
reload = os.getenv("GUNICORN_RELOAD", "false").lower() == "true"
reload_engine = "auto"

# Preload app for better memory usage (workers share code)
preload_app = True


def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info(f"Starting Gunicorn with {workers} workers, {threads} threads per worker ({cpu_count} CPU cores detected)")


def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading Gunicorn workers")


def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Gunicorn is ready to handle requests")


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")


def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    pass


def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    worker.log.info(f"Worker {worker.pid} received SIGINT/SIGQUIT")


def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info(f"Worker {worker.pid} aborted")


def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forking new master process")


def pre_request(worker, req):
    """Called just before a worker processes the request."""
    # worker.log.debug(f"{req.method} {req.path}")
    pass


def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    pass


def child_exit(server, worker):
    """Called when a worker is exiting."""
    server.log.info(f"Worker {worker.pid} exited")


def worker_exit(server, worker):
    """Called when a worker is exited."""
    pass


def nworkers_changed(server, new_value, old_value):
    """Called when the number of workers changes."""
    server.log.info(f"Workers changed from {old_value} to {new_value}")


def on_exit(server):
    """Called just before the master process exits."""
    server.log.info("Shutting down Gunicorn")
