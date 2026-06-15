"""
Zero-Trust API Gateway - Main Application
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import time
from datetime import datetime

from app.routes import auth, predict
from app.models.ml_model import fraud_detector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Zero-Trust API Gateway",
    description="""
    Secure API Gateway with:
    - JWT Authentication
    - API Key Rate Limiting
    - Input Validation
    - Audit Logging
    - ML-based Fraud Detection
    
    ## Authentication
    - Register: `POST /auth/register`
    - Login: `POST /auth/login` (returns JWT token)
    - Use token in `Authorization: Bearer <token>` header
    
    ## Rate Limiting
    - Readonly: 100 requests/day
    - Analyst: 1000 requests/day
    - Admin: 10000 requests/day
    
    ## Predictions
    - `POST /predict/` - Single transaction fraud score
    - `POST /predict/batch` - Batch transaction scoring
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    logger.info(f"Response: {response.status_code} - {request.method} {request.url.path} in {time.time() - start_time:.3f}s")
    
    return response

# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle input validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "body": exc.body
        }
    )

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "model_loaded": fraud_detector.model is not None
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Zero-Trust API Gateway",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "auth": {
                "register": "POST /auth/register",
                "login": "POST /auth/login",
                "me": "GET /auth/me"
            },
            "predict": {
                "single": "POST /predict/",
                "batch": "POST /predict/batch"
            }
        }
    }

# Include routers
app.include_router(auth.router)
app.include_router(predict.router)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize model on startup."""
    logger.info("Starting Zero-Trust API Gateway...")
    
    # Train or load model
    if not fraud_detector.model:
        logger.info("Training fraud detection model...")
        fraud_detector.train()
    
    logger.info("API Gateway ready")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down API Gateway...")
