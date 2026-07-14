from contextlib import asynccontextmanager
import logging
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


from app.modules.users.user_router import router as user_router
from app.core.database import async_engine


from app.modules.users.user_model import User
from app.modules.companies.company_model import Companies
from app.modules.jobs.job_model import JobPost
from app.modules.applications.application_model import JobApplication


# -------------------------------------------------------------------------------------------------------------- #


# ---------- Logging Setup: Both console and file ---------- #
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)  # no filename

# File handler
file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)


# ---------- Main FASTAPI App with Lifespan ---------- #
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events: dispose database engine on exit."""
    yield
    await async_engine.dispose()
    logger.info("Database engine disposed.")


app = FastAPI(
    title="Job-Board-API",
    lifespan=lifespan,
    version="1.0.0",
    description="A job board API with role-based access for employees and managers."
)


# ---------- CORS Middleware ---------- #
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    # Add production frontend domains here when deployed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Custom Middleware: Process Time Header ---------- #
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to every response (in seconds)."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# ---------- Custom Middleware: Security Headers ---------- #
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add standard security headers to all responses."""
    response = await call_next(request)

    response.headers["X-Frame-Options"] = "DENY"                          # Prevent clickjacking
    response.headers["X-Content-Type-Options"] = "nosniff"               # Prevent MIME sniffing
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"  # Enforce HTTPS
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Allow Swagger UI to load scripts/styles from CDN
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://fastapi.tiangolo.com;"
    )

    return response


# ---------- Global Exception Handlers ---------- #

# Handler for HTTPException (e.g., 401, 404, 409)
@app.exception_handler(HTTPException)
async def global_http_exception_handler(request: Request, exc: HTTPException):
    """Log 401s specially and return standard JSON error response."""
    if exc.status_code == 401:
        logger.warning(
            f"Security Warning: Unauthorized {request.method} access to '{request.url.path}'. "
            f"Reason: {exc.detail}"
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Catch-all for any other unhandled exceptions (prevents 500 without traceback)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Log any uncaught exception with full traceback and return 500."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# ---------- Include Routers ---------- #
app.include_router(user_router)


# ---------- Root Endpoint ---------- #
@app.get("/")
async def root():
    return {"message": "Welcome to Job-Board-API"}