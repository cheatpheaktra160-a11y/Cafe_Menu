"""Gunicorn configuration for production deployment on Render."""
import os

# Bind to 0.0.0.0 on the port Render provides
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# Workers
workers = 2
threads = 2
worker_class = "gthread"

# Timeout
timeout = 120

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
