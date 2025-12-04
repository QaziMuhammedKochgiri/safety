# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, Body
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .. import get_db
from ..models import ChatMessage, ChatMessageCreate
from ..email_service import EmailService
import logging
import os
import uuid

router = APIRouter(prefix="/chat", tags=["Chat Management"])
logger = logging.getLogger(__name__)


class StartSessionRequest(BaseModel):
    sessionId: str
    language: Optional[str] = "en"
    userAgent: Optional[str] = None
    isMobile: Optional[bool] = False
    timestamp: Optional[str] = None


@router.post("/start-session")
async def start_chat_session(
    request: StartSessionRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Start a new live chat session and notify support team"""
    try:
        # Session bilgilerini kaydet
        session_record = {
            "sessionId": request.sessionId,
            "language": request.language,
            "userAgent": request.userAgent,
            "isMobile": request.isMobile,
            "status": "active",
            "startedAt": datetime.utcnow(),
            "lastActivity": datetime.utcnow()
        }

        await db.chat_sessions.insert_one(session_record)

        # Destek ekibine e-posta bildirimi gönder
        device_type = "Mobil" if request.isMobile else "Bilgisayar"
        lang_map = {"de": "Almanca", "tr": "Turkce", "en": "Ingilizce"}
        lang_name = lang_map.get(request.language, request.language)

        email_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="background: #2563eb; color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0;">YENI CANLI DESTEK TALEBI</h1>
            </div>
            <div style="background: #f3f4f6; padding: 20px; border-radius: 0 0 10px 10px;">
                <p><strong>Session ID:</strong> {request.sessionId}</p>
                <p><strong>Cihaz Tipi:</strong> {device_type}</p>
                <p><strong>Dil:</strong> {lang_name}</p>
                <p><strong>Zaman:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                <hr style="border: 1px solid #ddd;">
                <p style="color: #dc2626; font-weight: bold;">
                    ACIL: Bir musterı canlı destek bekliyor!
                </p>
                <p>Lutfen admin panelinden chat bolumune gidiniz.</p>
            </div>
        </body>
        </html>
        """

        try:
            EmailService.send_email(
                to=["info@safechild.mom"],
                subject=f"CANLI DESTEK - Yeni Talep ({device_type})",
                html=email_html
            )
            logger.info(f"Live chat session started: {request.sessionId}")
        except Exception as e:
            logger.error(f"Failed to send session notification: {str(e)}")

        return {
            "success": True,
            "sessionId": request.sessionId,
            "message": "Session started successfully"
        }

    except Exception as e:
        logger.error(f"Error starting chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message")
async def send_message(message_data: ChatMessageCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Send a chat message"""
    try:
        # Create message with all fields including agentName
        message_dict = {
            "id": str(uuid.uuid4()),
            "sessionId": message_data.sessionId,
            "sender": message_data.sender,
            "message": message_data.message,
            "agentName": message_data.agentName,
            "clientNumber": message_data.clientNumber,
            "timestamp": datetime.utcnow(),
            "isRead": False
        }
        await db.chat_messages.insert_one(message_dict)

        if message_data.sender == 'client':
            try:
                session_messages = await db.chat_messages.find(
                    {"sessionId": message_data.sessionId}
                ).sort("timestamp", 1).to_list(length=50)
                
                message_history = ""
                for msg in session_messages[-5:]:
                    sender_label = "Kunde" if msg.get("sender") == "client" else "Bot"
                    message_history += f"{sender_label}: {msg.get('message', '')}\n"
                
                # Simplified email content to avoid encoding issues
                email_html = f"""
                <html>
                <body>
                    <h1>Neue Chat-Nachricht</h1>
                    <p><strong>Session ID:</strong> {message_data.sessionId}</p>
                    <p><strong>Neue Nachricht:</strong></p>
                    <p>{message_data.message}</p>
                    <hr>
                    <p><strong>Letzte Nachrichten:</strong></p>
                    <pre>{message_history}</pre>
                    <hr>
                    <p><strong>AKTION ERFORDERLICH:</strong> Ein Kunde wartet auf Antwort.</p>
                </body>
                </html>
                """

                EmailService.send_email(
                    to=["info@safechild.mom"], 
                    subject=f"Neue Chat-Nachricht - Session {message_data.sessionId[:8]}",
                    html=email_html
                )
                logger.info(f"Chat notification email sent to admin for session {message_data.sessionId}")
            except Exception as e:
                logger.error(f"Failed to send chat notification email: {str(e)}")

        return {
            "success": True,
            "messageId": message_dict["id"],
            "timestamp": message_dict["timestamp"].isoformat()
        }
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session-status/{session_id}")
async def get_session_status(session_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Check if a session is active or closed"""
    try:
        session = await db.chat_sessions.find_one({"sessionId": session_id})
        if not session:
            return {"status": "not_found", "sessionId": session_id}
        return {"status": session.get("status", "active"), "sessionId": session_id}
    except Exception as e:
        logger.error(f"Error checking session status: {str(e)}")
        return {"status": "error", "sessionId": session_id}


@router.get("/sessions")
async def get_all_sessions(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get all chat sessions for admin panel"""
    try:
        sessions = await db.chat_sessions.find().sort("startedAt", -1).to_list(length=100)
        # Convert ObjectId to string for JSON serialization
        for session in sessions:
            if "_id" in session:
                session["_id"] = str(session["_id"])
            if "startedAt" in session:
                session["startedAt"] = session["startedAt"].isoformat() if hasattr(session["startedAt"], 'isoformat') else str(session["startedAt"])
            if "lastActivity" in session:
                session["lastActivity"] = session["lastActivity"].isoformat() if hasattr(session["lastActivity"], 'isoformat') else str(session["lastActivity"])
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error fetching sessions: {str(e)}")
        return {"sessions": []}


@router.post("/close-session")
async def close_chat_session(
    data: dict = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Close a chat session"""
    session_id = data.get("sessionId")
    if not session_id:
        raise HTTPException(status_code=400, detail="sessionId is required")

    try:
        result = await db.chat_sessions.update_one(
            {"sessionId": session_id},
            {"$set": {"status": "closed", "closedAt": datetime.utcnow()}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")

        logger.info(f"Chat session closed: {session_id}")
        return {"success": True, "message": "Session closed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}")
async def get_chat_history(session_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get chat history for a session"""
    messages = await db.chat_messages.find({"sessionId": session_id}).sort("timestamp", 1).to_list(length=None)
    # Convert ObjectId and datetime for JSON serialization
    for msg in messages:
        if "_id" in msg:
            msg["_id"] = str(msg["_id"])
        if "id" in msg:
            msg["id"] = str(msg["id"])
        if "timestamp" in msg:
            msg["timestamp"] = msg["timestamp"].isoformat() if hasattr(msg["timestamp"], 'isoformat') else str(msg["timestamp"])
    return {"messages": messages}
