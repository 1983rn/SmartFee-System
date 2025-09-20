import os
import multiprocessing

# Server socket
port = int(os.environ.get('PORT', 5000))
bind = f'0.0.0.0:{port}'

# Worker processes
workers = 2  # Lower number of workers for better stability
worker_class = 'sync'  # Use sync workers instead of eventlet
worker_connections = 1000

# Logging
loglevel = 'info'
accesslog = '-'  # Log to stdout
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
errorlog = '-'  # Log to stderr
capture_output = True

# Timeouts
timeout = 120
keepalive = 5

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
max_requests = 1000
max_requests_jitter = 50

# Debugging
reload = os.environ.get('FLASK_ENV') == 'development'
