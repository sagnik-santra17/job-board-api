from contextlib import asynccontextmanager
import logging
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


from app.modules.users.user_router import router as user_router
from app.modules.companies.company_router import router as company_router
from app.core.database import async_engine


from app.modules.users.user_model import User
from app.modules.companies.company_model import Companies
from app.modules.jobs.job_model import JobPost
from app.modules.applications.application_model import JobApplication


# -------------------------------------------------------------------------------------------------------------- #


# ---------- Logging Setup (file only, like your previous project) ---------- #
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logging.getLogger("watchfiles").setLevel(logging.WARNING)
logging.getLogger("passlib").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)
logger.info("Application starting up...")


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

    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://fastapi.tiangolo.com;"
    )

    return response


# ---------- Global Exception Handlers ---------- #

@app.exception_handler(HTTPException)
async def global_http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        logger.warning(
            f"Security Warning: Unauthorized {request.method} access to '{request.url.path}'. "
            f"Reason: {exc.detail}"
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# ---------- Include Routers ---------- #
app.include_router(user_router)
app.include_router(company_router)


# ---------- Root Endpoint ---------- #
@app.get("/")
async def root():
    return {"message": "Welcome to Job-Board-API"}