"""
Social Media Integration Router for SafeChild
Proxies requests to WhatsApp and Telegram microservices
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from motor.motor_asyncio import AsyncIOMotorDatabase
import httpx
import os

from .. import get_db
from ..auth import get_current_admin
from ..logging_config import get_logger

router = APIRouter(tags=["Social Media Integration"])
logger = get_logger("safechild.social")

WHATSAPP_SERVICE_URL = os.environ.get("WHATSAPP_SERVICE_URL", "http://whatsapp-service:8002")
TELEGRAM_SERVICE_URL = os.environ.get("TELEGRAM_SERVICE_URL", "http://telegram-service:8003")


# =============================================================================
# WhatsApp Endpoints
# =============================================================================

@router.post("/whatsapp/session/start")
async def start_whatsapp_session(
    data: dict = Body(...),
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Start a WhatsApp session for a client.
    Requires admin privileges.
    """
    client_number = data.get("clientNumber")
    if not client_number:
        raise HTTPException(status_code=400, detail="clientNumber is required")

    # Verify client exists
    client = await db.clients.find_one({"clientNumber": client_number})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    logger.info(f"Starting WhatsApp session for client {client_number}")

    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                f"{WHATSAPP_SERVICE_URL}/session/start",
                json={"clientNumber": client_number},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError:
        logger.error("WhatsApp service unreachable")
        raise HTTPException(status_code=503, detail="WhatsApp service is unavailable")
    except httpx.HTTPStatusError as e:
        logger.error(f"WhatsApp service error: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"WhatsApp session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/whatsapp/session/{session_id}/status")
async def get_whatsapp_status(session_id: str):
    """
    Get WhatsApp session status and QR code.
    Public endpoint (identified by session_id).
    """
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{WHATSAPP_SERVICE_URL}/session/{session_id}/status",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="WhatsApp service is unavailable")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/whatsapp/session/{session_id}")
async def cancel_whatsapp_session(
    session_id: str,
    current_user: dict = Depends(get_current_admin)
):
    """Cancel a WhatsApp session (admin only)."""
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.delete(
                f"{WHATSAPP_SERVICE_URL}/session/{session_id}",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="WhatsApp service is unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/whatsapp/sessions")
async def list_whatsapp_sessions(current_user: dict = Depends(get_current_admin)):
    """List all active WhatsApp sessions (admin only)."""
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{WHATSAPP_SERVICE_URL}/sessions",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="WhatsApp service is unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Telegram Endpoints
# =============================================================================

@router.post("/telegram/session/start")
async def start_telegram_session(
    data: dict = Body(...),
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Start a Telegram session for a client.
    Requires admin privileges.
    """
    client_number = data.get("clientNumber")
    if not client_number:
        raise HTTPException(status_code=400, detail="clientNumber is required")

    # Verify client exists
    client = await db.clients.find_one({"clientNumber": client_number})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    logger.info(f"Starting Telegram session for client {client_number}")

    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                f"{TELEGRAM_SERVICE_URL}/session/start",
                json={"clientNumber": client_number},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError:
        logger.error("Telegram service unreachable")
        raise HTTPException(status_code=503, detail="Telegram service is unavailable")
    except httpx.HTTPStatusError as e:
        logger.error(f"Telegram service error: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"Telegram session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/telegram/session/{session_id}/status")
async def get_telegram_status(session_id: str):
    """
    Get Telegram session status and QR code.
    Public endpoint (identified by session_id).
    """
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{TELEGRAM_SERVICE_URL}/session/{session_id}/status",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Telegram service is unavailable")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/telegram/session/{session_id}")
async def cancel_telegram_session(
    session_id: str,
    current_user: dict = Depends(get_current_admin)
):
    """Cancel a Telegram session (admin only)."""
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.delete(
                f"{TELEGRAM_SERVICE_URL}/session/{session_id}",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Telegram service is unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/telegram/sessions")
async def list_telegram_sessions(current_user: dict = Depends(get_current_admin)):
    """List all active Telegram sessions (admin only)."""
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{TELEGRAM_SERVICE_URL}/sessions",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Telegram service is unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Health Check for Services
# =============================================================================

@router.get("/social/health")
async def social_services_health():
    """Check health of WhatsApp and Telegram services."""
    health_status = {
        "whatsapp": {"status": "unknown"},
        "telegram": {"status": "unknown"}
    }

    async with httpx.AsyncClient() as http_client:
        # Check WhatsApp
        try:
            response = await http_client.get(
                f"{WHATSAPP_SERVICE_URL}/health",
                timeout=5.0
            )
            if response.status_code == 200:
                health_status["whatsapp"] = response.json()
            else:
                health_status["whatsapp"] = {"status": "unhealthy"}
        except Exception as e:
            health_status["whatsapp"] = {"status": "unreachable", "error": str(e)}

        # Check Telegram
        try:
            response = await http_client.get(
                f"{TELEGRAM_SERVICE_URL}/health",
                timeout=5.0
            )
            if response.status_code == 200:
                health_status["telegram"] = response.json()
            else:
                health_status["telegram"] = {"status": "unhealthy"}
        except Exception as e:
            health_status["telegram"] = {"status": "unreachable", "error": str(e)}

    return health_status
