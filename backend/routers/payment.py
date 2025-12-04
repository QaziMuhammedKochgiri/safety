from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
import uuid
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

# requests.py dosyanla aynı import yapısı
from .. import get_db

# Router prefix'i ve tag'i kendi içinde tanımlı (server.py'da tekrar prefix yazmaya gerek yok)
router = APIRouter(prefix="/payment", tags=["Payment"])

class CheckoutRequest(BaseModel):
    client_number: str
    amount: int
    origin_url: str

@router.post("/create-checkout")
async def create_checkout_session(
    data: CheckoutRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Vakıf/Sponsorlu Mock Ödeme Endpoint'i.
    Stripe yerine direkt başarılı session döner.
    """
    # Mock Session ID
    session_id = f"grant_{uuid.uuid4().hex}"
    
    # DB'ye 'sponsored' statüsüyle kayıt atıyoruz
    transaction_record = {
        "session_id": session_id,
        "client_number": data.client_number,
        "amount": data.amount,
        "currency": "EUR",
        "status": "sponsored",
        "provider": "FOUNDATION_GRANT",
        "created_at": datetime.utcnow()
    }
    
    await db.payment_transactions.insert_one(transaction_record)
    
    # Frontend'i doğrudan başarı sayfasına yönlendir
    return {
        "url": f"{data.origin_url}/payment/success?session_id={session_id}",
        "sessionId": session_id
    }

@router.get("/checkout/status/{session_id}")
async def get_checkout_status(
    session_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Ödeme durum kontrolü. Mock olduğu için her zaman 'paid' döner.
    """
    transaction = await db.payment_transactions.find_one({"session_id": session_id})
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return {
        "status": "complete",
        "payment_status": "paid",
        "customer_email": "grant@safechild.mom"
    }