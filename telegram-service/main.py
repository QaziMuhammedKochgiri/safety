"""
SafeChild Telegram Service
Production-ready Telegram API integration for evidence extraction
"""
import os
import asyncio
import qrcode
import io
import base64
import logging
import json
from typing import Dict, Optional
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from telethon import TelegramClient
from telethon.sessions import StringSession
import httpx

# Configuration
SHARED_DIR = os.environ.get("SHARED_DIR", "/tmp/forensics_uploads")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8001")
TELEGRAM_API_ID = int(os.environ.get("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH", "")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

# Ensure shared directory exists
os.makedirs(SHARED_DIR, exist_ok=True)


# Logging setup
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


logger = logging.getLogger("telegram-service")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
if ENVIRONMENT == "production":
    handler.setFormatter(JSONFormatter())
else:
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
logger.addHandler(handler)

# FastAPI app
app = FastAPI(title="SafeChild Telegram Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Session status enum
class SessionStatus:
    INITIALIZING = "initializing"
    QR_READY = "qr_ready"
    CONNECTED = "connected"
    EXTRACTING = "extracting"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


# Session data class
class SessionData:
    def __init__(self, client: TelegramClient, client_number: str):
        self.client = client
        self.client_number = client_number
        self.qr_url: Optional[str] = None
        self.status = SessionStatus.INITIALIZING
        self.error: Optional[str] = None
        self.created_at = datetime.utcnow()


# Active sessions store
sessions: Dict[str, SessionData] = {}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    api_configured = bool(TELEGRAM_API_ID and TELEGRAM_API_HASH)
    return {
        "status": "healthy" if api_configured else "degraded",
        "service": "telegram-service",
        "activeSessions": len(sessions),
        "apiConfigured": api_configured,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.post("/session/start")
async def start_session(data: dict = Body(...), background_tasks: BackgroundTasks = None):
    """Start a new Telegram session for QR code authentication."""
    client_number = data.get("client_number") or data.get("clientNumber")

    if not client_number:
        raise HTTPException(status_code=400, detail="client_number is required")

    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        raise HTTPException(
            status_code=503,
            detail="Telegram API credentials not configured. Please set TELEGRAM_API_ID and TELEGRAM_API_HASH."
        )

    session_id = f"tg_{client_number}_{int(datetime.utcnow().timestamp())}"
    logger.info(f"Starting Telegram session: {session_id}")

    try:
        # Initialize Telethon Client with a temporary session
        client = TelegramClient(StringSession(), TELEGRAM_API_ID, TELEGRAM_API_HASH)
        await client.connect()

        sessions[session_id] = SessionData(client, client_number)

        # Start QR Login process in background
        background_tasks.add_task(handle_qr_login, session_id)

        return {
            "success": True,
            "sessionId": session_id,
            "message": "Session started. Poll /session/:sessionId/status for QR code."
        }

    except Exception as e:
        logger.error(f"Failed to start session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}/status")
async def get_status(session_id: str):
    """Get the status of a Telegram session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    return {
        "sessionId": session_id,
        "status": session.status,
        "qr": session.qr_url,
        "error": session.error,
        "createdAt": session.created_at.isoformat() + "Z"
    }


@app.delete("/session/{session_id}")
async def cancel_session(session_id: str):
    """Cancel and cleanup a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    logger.info(f"Cancelling session: {session_id}")
    await cleanup_session(session_id)

    return {"success": True, "message": "Session cancelled"}


@app.get("/sessions")
async def list_sessions():
    """List all active sessions (admin endpoint)."""
    session_list = []
    for sid, session in sessions.items():
        session_list.append({
            "sessionId": sid,
            "clientNumber": session.client_number,
            "status": session.status,
            "createdAt": session.created_at.isoformat() + "Z",
            "hasQr": session.qr_url is not None
        })

    return {"total": len(session_list), "sessions": session_list}


async def handle_qr_login(session_id: str):
    """Handle QR code login flow."""
    if session_id not in sessions:
        return

    session = sessions[session_id]
    client = session.client

    try:
        if not await client.is_user_authorized():
            # Start QR login
            qr_login = await client.qr_login()

            # Generate QR code image
            img = qrcode.make(qr_login.url)
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            session.qr_url = f"data:image/png;base64,{img_str}"
            session.status = SessionStatus.QR_READY
            logger.info(f"QR Code ready for {session_id}")

            # Wait for login with timeout
            try:
                await asyncio.wait_for(qr_login.wait(), timeout=180)  # 3 minutes
                session.status = SessionStatus.CONNECTED
                session.qr_url = None
                logger.info(f"User logged in: {session_id}")

                # Start extraction
                await extract_data(session_id)

            except asyncio.TimeoutError:
                session.status = SessionStatus.TIMEOUT
                session.error = "QR scan timeout - please try again"
                logger.warning(f"QR scan timeout for {session_id}")
                await client.disconnect()

        else:
            # Already authorized
            session.status = SessionStatus.CONNECTED
            logger.info(f"Already authorized: {session_id}")
            await extract_data(session_id)

    except Exception as e:
        logger.error(f"Login error for {session_id}: {e}")
        session.status = SessionStatus.FAILED
        session.error = str(e)
        try:
            await client.disconnect()
        except:
            pass


async def extract_data(session_id: str):
    """Extract Telegram data from the authenticated session."""
    if session_id not in sessions:
        return

    session = sessions[session_id]
    client = session.client
    session.status = SessionStatus.EXTRACTING

    logger.info(f"Starting data extraction for {session_id}")

    try:
        full_transcript = "=== TELEGRAM FORENSIC EXPORT ===\n"
        full_transcript += f"Date: {datetime.utcnow().isoformat()}Z\n"
        full_transcript += f"Client Number: {session.client_number}\n"
        full_transcript += "=" * 50 + "\n\n"

        # Get user info
        me = await client.get_me()
        full_transcript += f"Account: {me.first_name or ''} {me.last_name or ''}\n"
        full_transcript += f"Phone: {me.phone or 'N/A'}\n"
        full_transcript += f"Username: @{me.username or 'N/A'}\n\n"

        # Iterate over dialogs (chats)
        dialog_count = 0
        total_messages = 0

        async for dialog in client.iter_dialogs(limit=50):
            dialog_count += 1
            chat_name = dialog.name or "Unknown"

            full_transcript += f"\n{'─' * 40}\n"
            full_transcript += f"CHAT: {chat_name} (ID: {dialog.id})\n"
            full_transcript += f"Type: {'Group' if dialog.is_group else 'Channel' if dialog.is_channel else 'Private'}\n"
            full_transcript += f"{'─' * 40}\n"

            # Fetch messages (limit to 100 per chat)
            try:
                async for message in client.iter_messages(dialog, limit=100):
                    total_messages += 1

                    try:
                        if message.out:
                            sender = "ME"
                        elif message.sender:
                            sender = message.sender.first_name or "Other"
                        else:
                            sender = "Unknown"

                        date_str = message.date.strftime("%Y-%m-%d %H:%M:%S") if message.date else "N/A"
                        text = message.text or "[Media/Sticker]"

                        full_transcript += f"[{date_str}] {sender}: {text}\n"
                    except Exception as msg_err:
                        full_transcript += f"[Error reading message: {msg_err}]\n"

            except Exception as chat_err:
                full_transcript += f"[Error fetching messages: {chat_err}]\n"

        full_transcript += f"\n{'=' * 50}\n"
        full_transcript += "END OF EXPORT\n"
        full_transcript += f"Total Dialogs: {dialog_count}\n"
        full_transcript += f"Total Messages: {total_messages}\n"

        # Save to file
        filename = f"TELEGRAM_AUTO_{session.client_number}_{int(datetime.utcnow().timestamp())}.txt"
        file_path = os.path.join(SHARED_DIR, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_transcript)

        logger.info(f"Data saved to {file_path}, messages: {total_messages}")

        # Notify backend
        try:
            async with httpx.AsyncClient() as http_client:
                await http_client.post(
                    f"{BACKEND_URL}/api/forensics/analyze-internal",
                    json={
                        "file_path": file_path,
                        "client_number": session.client_number,
                        "source": "telegram_automation",
                        "statistics": {
                            "total_dialogs": dialog_count,
                            "total_messages": total_messages
                        }
                    },
                    timeout=30.0
                )
            logger.info(f"Backend notified successfully for {session_id}")
            session.status = SessionStatus.COMPLETED

        except Exception as notify_err:
            logger.error(f"Failed to notify backend for {session_id}: {notify_err}")
            session.status = SessionStatus.COMPLETED  # Still completed, file saved
            session.error = "Data extracted but backend notification failed"

    except Exception as e:
        logger.error(f"Extraction failed for {session_id}: {e}")
        session.status = SessionStatus.FAILED
        session.error = f"Extraction failed: {str(e)}"

    finally:
        try:
            await client.disconnect()
        except:
            pass

        # Schedule cleanup
        asyncio.create_task(delayed_cleanup(session_id, 300))  # 5 minutes


async def delayed_cleanup(session_id: str, delay: int):
    """Cleanup session after delay."""
    await asyncio.sleep(delay)
    if session_id in sessions:
        del sessions[session_id]
        logger.info(f"Session {session_id} removed from memory")


async def cleanup_session(session_id: str):
    """Immediately cleanup a session."""
    if session_id not in sessions:
        return

    session = sessions[session_id]
    logger.info(f"Cleaning up session: {session_id}")

    try:
        if session.client:
            await session.client.disconnect()
    except Exception as e:
        logger.warning(f"Error disconnecting client {session_id}: {e}")

    del sessions[session_id]


# Startup event
@app.on_event("startup")
async def startup():
    logger.info(f"Telegram Service starting (env: {ENVIRONMENT})")
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        logger.warning("Telegram API credentials not configured!")


# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    logger.info("Telegram Service shutting down...")
    for session_id in list(sessions.keys()):
        await cleanup_session(session_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
