"""
Health Check Endpoints for SafeChild API
Provides detailed health status for monitoring and orchestration
"""
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import os

from .. import get_db
from ..logging_config import get_logger

router = APIRouter(tags=["Health Check"])
logger = get_logger("safechild.health")


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    Returns minimal info for load balancer health checks.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Detailed health check with service status.
    Use this for monitoring dashboards.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "services": {}
    }

    # Check MongoDB
    try:
        await db.client.admin.command('ping')
        health_status["services"]["mongodb"] = {
            "status": "healthy",
            "latency_ms": None  # Could add latency measurement
        }
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        health_status["status"] = "degraded"
        health_status["services"]["mongodb"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Check if forensics upload directory exists and is writable
    forensics_dir = "/tmp/forensics_uploads"
    try:
        if os.path.exists(forensics_dir) and os.access(forensics_dir, os.W_OK):
            health_status["services"]["forensics_storage"] = {"status": "healthy"}
        else:
            health_status["services"]["forensics_storage"] = {
                "status": "warning",
                "message": "Directory not writable"
            }
    except Exception as e:
        health_status["services"]["forensics_storage"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Add database statistics
    try:
        stats = {
            "clients": await db.clients.count_documents({}),
            "documents": await db.documents.count_documents({}),
            "forensic_cases": await db.forensic_analyses.count_documents({}),
            "active_magic_links": await db.evidence_requests.count_documents({
                "expiresAt": {"$gt": datetime.utcnow()}
            })
        }
        health_status["database_stats"] = stats
    except Exception as e:
        logger.warning(f"Could not get database stats: {e}")

    return health_status


@router.get("/health/ready")
async def readiness_check(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Kubernetes readiness probe endpoint.
    Returns 200 only if the service is ready to accept traffic.
    """
    try:
        # Verify database connection
        await db.client.admin.command('ping')
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "reason": str(e)}


@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    Returns 200 if the service is running.
    """
    return {"status": "alive"}
