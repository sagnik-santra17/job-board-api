from contextlib import asynccontextmanager
import logging
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware



from app.modules.users.user_router import router as user_router
from app.core.database import async_engine
from app.modules.users.user_model import User


# -------------------------------------------------------------------------------------------------------------- #


#-----------logging setup-----------#
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logging.getLogger("watchfiles").setLevel(logging.WARNING)
logging.getLogger("passlib").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)
logger.info("Application starting up...")


# ---------- Main FASTAPI APP ---------- #
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await async_engine.dispose()

app = FastAPI(title="Job-Board-API", lifespan=lifespan)


#---------middleware----------#
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # This rule allows the app to load Swagger files from external CDNs safely
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://fastapi.tiangolo.com;"
    )

    return response


#--------global exception handler---------#
#This catches all HTTP errors, logs 401s, and returns the response
@app.exception_handler(HTTPException)
async def global_http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        logger.warning(
            f"Security Warning: Unauthorized {request.method} access attempt to path '{request.url.path}'. "
            f"Reason: {exc.detail}"
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


#--------main app routes---------#
app.include_router(user_router)


@app.get("/")
async def root():
    return {"message": "Welcome to Job-Board-API"}
