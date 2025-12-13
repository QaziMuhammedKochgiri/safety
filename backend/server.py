"""
SafeChild Law Firm API - Main Application Server
Production-ready FastAPI application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
import os
import traceback
from motor.motor_asyncio import AsyncIOMotorClient

# Local imports
from .routers import (
    auth,
    clients,
    documents,
    consent,
    chat,
    cases,
    payment,
    forensics,
    ios_forensics,
    cloud_forensics,
    meetings,
    admin,
    emails,
    health,
    requests,
    public,
    social,
    collection,
    verification,
    data_pool,
    evidence_collection,
    case_timeline,
    analytics,
    templates,
    calendar,
    network_graph,
    location_map,
    transcription,
    image_analysis,
    reports,
    device_comparison
)
from . import db
from .logging_config import setup_logging, get_logger
from .middleware import RateLimitMiddleware, RequestLoggingMiddleware, SecurityHeadersMiddleware

# Initialize logging
logger = get_logger("safechild.server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown event management."""
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "safechild_db")

    logger.info(f"Starting SafeChild API server...")
    logger.info(f"Connecting to MongoDB: {db_name}")

    # Global DB Client
    db.client = AsyncIOMotorClient(mongo_url)
    db.db = db.client[db_name]

    # Verify connection
    try:
        await db.client.admin.command('ping')
        logger.info(f"MongoDB connected successfully: {db_name}")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise

    # Create indexes for better performance
    await create_indexes(db.db)

    yield

    logger.info("Shutting down SafeChild API server...")
    db.client.close()
    logger.info("MongoDB connection closed")


async def create_indexes(database):
    """Create database indexes for optimal performance."""
    try:
        # Clients collection
        await database.clients.create_index("clientNumber", unique=True)
        await database.clients.create_index("email", unique=True)
        await database.clients.create_index("status")

        # Documents collection
        await database.documents.create_index("clientNumber")
        await database.documents.create_index("documentNumber", unique=True)

        # Forensic analyses
        await database.forensic_analyses.create_index("case_id", unique=True)
        await database.forensic_analyses.create_index("client_number")
        await database.forensic_analyses.create_index("status")
        await database.forensic_analyses.create_index("created_at")

        # Evidence requests (magic links)
        await database.evidence_requests.create_index("token", unique=True)
        await database.evidence_requests.create_index("expiresAt")

        # Chat messages
        await database.chat_messages.create_index("clientNumber")
        await database.chat_messages.create_index("timestamp")

        # Meetings
        await database.meetings.create_index("meetingId", unique=True)
        await database.meetings.create_index("clientNumber")

        # Shared reports
        await database.shared_reports.create_index("token", unique=True)
        await database.shared_reports.create_index("expiresAt")

        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.warning(f"Index creation warning (may already exist): {e}")


# Create FastAPI application
app = FastAPI(
    title="SafeChild Law Firm API",
    description="API for SafeChild Law Firm - International Child Custody & Forensics Platform",
    version="1.0.0",
    docs_url="/api/docs" if os.environ.get("ENVIRONMENT") != "production" else None,
    redoc_url="/api/redoc" if os.environ.get("ENVIRONMENT") != "production" else None,
    lifespan=lifespan
)


# =============================================================================
# Global Exception Handlers
# =============================================================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with proper logging."""
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={"extra_fields": {
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "method": request.method
        }}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with details."""
    logger.warning(
        f"Validation Error: {request.url.path}",
        extra={"extra_fields": {
            "path": str(request.url.path),
            "method": request.method,
            "errors": exc.errors()
        }}
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler for unexpected errors."""
    logger.error(
        f"Unhandled Exception: {type(exc).__name__} - {str(exc)}",
        extra={"extra_fields": {
            "path": str(request.url.path),
            "method": request.method,
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc()
        }},
        exc_info=True
    )

    # Don't expose internal error details in production
    if os.environ.get("ENVIRONMENT") == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal error occurred. Please try again later."}
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": str(exc),
                "type": type(exc).__name__
            }
        )


# =============================================================================
# Middleware Stack (order matters - bottom to top execution)
# =============================================================================

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Request logging
app.add_middleware(RequestLoggingMiddleware)

# Rate limiting
app.add_middleware(RateLimitMiddleware)

# CORS - configure based on environment
cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["X-Process-Time"],
)


# =============================================================================
# Router Configuration
# =============================================================================

# Main API router
api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router)
api_router.include_router(clients.router)
api_router.include_router(documents.router)
api_router.include_router(consent.router)
api_router.include_router(chat.router)
api_router.include_router(cases.router)
api_router.include_router(payment.router)
api_router.include_router(forensics.router)
api_router.include_router(ios_forensics.router)
api_router.include_router(cloud_forensics.router)
api_router.include_router(meetings.router)
api_router.include_router(admin.router)
api_router.include_router(emails.router)
api_router.include_router(requests.router)
api_router.include_router(public.router)
api_router.include_router(social.router)
api_router.include_router(collection.router)
api_router.include_router(verification.router)
api_router.include_router(data_pool.router)
api_router.include_router(evidence_collection.router)
api_router.include_router(case_timeline.router)
api_router.include_router(analytics.router)
api_router.include_router(templates.router)
api_router.include_router(calendar.router)
api_router.include_router(network_graph.router)
api_router.include_router(location_map.router)
api_router.include_router(transcription.router)
api_router.include_router(image_analysis.router)
api_router.include_router(reports.router)
api_router.include_router(device_comparison.router)

# Health check outside /api prefix for easier monitoring
app.include_router(health.router)

# All API routes under /api prefix
app.include_router(api_router, prefix="/api")


# =============================================================================
# Root endpoint
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": "SafeChild Law Firm API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/api/docs" if os.environ.get("ENVIRONMENT") != "production" else "disabled"
    }


# =============================================================================
# Development server entry point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.server:app",
        host="0.0.0.0",
        port=8000,
        reload=os.environ.get("ENVIRONMENT") != "production",
        log_level="info"
    )
