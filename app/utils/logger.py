import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from fastapi import Request
import time

# Ensure logs directory exists
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)

# Configure logger
logger = logging.getLogger("request_logger")
logger.setLevel(logging.INFO)

# Rotate daily, keep logs for ~3 years (approx 1095 days)
handler = TimedRotatingFileHandler(
    filename=log_dir / "app.log",
    when="midnight",
    interval=1,
    backupCount=1095,  # keep 3 years
    encoding="utf-8",
    utc=True
)
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Middleware
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Process request
    response = await call_next(request)
    duration = time.time() - start_time

    client_host = request.client.host if request.client else "unknown"

    logger.info(
        f"{client_host} {request.method} {request.url.path} "
        f"status={response.status_code} time={duration:.3f}s"
    )

    return response
