import multiprocessing
import os

# Bind to 0.0.0.0:8000
bind = "0.0.0.0:8000"

# Worker configuration
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"

# Process naming
proc_name = "llm-analysis-quiz"

# Reload for development (disable in production)
reload = os.getenv("FLASK_ENV") == "development"
