# -*- coding: utf-8 -*-
"""
Data Pool Router - Otomatik Forensic Veri Havuzu
Muvekkil siteye baglandiginda tarayici/cihaz verilerini otomatik toplar
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Body
from datetime import datetime, timezone
from typing import Optional, List, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
import uuid
import logging

from .. import get_db

router = APIRouter(prefix="/data-pool", tags=["Data Pool"])
logger = logging.getLogger(__name__)


# =============================================================================
# Pydantic Models
# =============================================================================

class BrowserFingerprint(BaseModel):
    """Tarayici parmak izi verileri"""
    userAgent: str
    language: str
    languages: List[str] = []
    platform: str
    screenResolution: str
    colorDepth: int = 0
    timezone: str
    timezoneOffset: int = 0
    cookiesEnabled: bool = True
    doNotTrack: Optional[str] = None
    plugins: List[str] = []
    canvas: Optional[str] = None  # Canvas fingerprint hash
    webGL: Optional[str] = None   # WebGL renderer info
    fonts: List[str] = []
    audioContext: Optional[str] = None


class LocationData(BaseModel):
    """Konum verileri"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    altitudeAccuracy: Optional[float] = None
    heading: Optional[float] = None
    speed: Optional[float] = None
    timestamp: Optional[str] = None
    # Reverse geocoding sonucu
    country: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    postalCode: Optional[str] = None
    address: Optional[str] = None


class DeviceInfo(BaseModel):
    """Cihaz bilgileri"""
    isMobile: bool = False
    deviceType: str = "desktop"  # desktop, mobile, tablet
    os: Optional[str] = None
    osVersion: Optional[str] = None
    browser: Optional[str] = None
    browserVersion: Optional[str] = None
    deviceMemory: Optional[int] = None  # GB
    hardwareConcurrency: Optional[int] = None  # CPU cores
    maxTouchPoints: Optional[int] = None
    connection: Optional[Dict] = None  # Network info


class ConsentPermissions(BaseModel):
    """Verilen izinler"""
    location: bool = False
    camera: bool = False
    microphone: bool = False
    notifications: bool = False
    storage: bool = False
    forensic: bool = False


class DataPoolCreate(BaseModel):
    """Veri havuzu olusturma istegi"""
    sessionId: str
    clientNumber: Optional[str] = None  # Eger biliniyorsa
    fingerprint: BrowserFingerprint
    location: Optional[LocationData] = None
    device: DeviceInfo
    permissions: ConsentPermissions
    referrer: Optional[str] = None
    landingPage: Optional[str] = None
    connectionHistory: List[Dict] = []  # Sayfa gecis kayitlari


class DataPoolUpdate(BaseModel):
    """Veri havuzu guncelleme (ek veri ekleme)"""
    sessionId: str
    location: Optional[LocationData] = None
    newPages: List[Dict] = []
    interactions: List[Dict] = []  # Kullanici etkilesimleri
    formData: Optional[Dict] = None  # Form verileri (beyan bilgileri)


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/create")
async def create_data_pool(
    data: DataPoolCreate,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Yeni veri havuzu olustur - consent kabul edildiginde cagirilir
    Bu endpoint public'tir - chat basladiginda otomatik cagrilir
    """
    try:
        # IP adresini al
        ip_address = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()

        pool_id = f"POOL_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8].upper()}"

        data_pool_doc = {
            "pool_id": pool_id,
            "session_id": data.sessionId,
            "client_number": data.clientNumber,  # Bos olabilir, sonra eslestirilebilir
            "status": "active",

            # IP ve Baglanti Bilgileri
            "ip_address": ip_address,
            "referrer": data.referrer,
            "landing_page": data.landingPage,

            # Tarayici Parmak Izi
            "fingerprint": data.fingerprint.model_dump(),

            # Cihaz Bilgileri
            "device": data.device.model_dump(),

            # Konum Verileri
            "locations": [data.location.model_dump()] if data.location else [],

            # Izinler
            "permissions": data.permissions.model_dump(),

            # Sayfa Gecisleri
            "page_visits": data.connectionHistory,

            # Kullanici Etkilesimleri
            "interactions": [],

            # Form Verileri (beyan bilgileri)
            "form_data": {},

            # Chain of Custody
            "chain_of_custody": [{
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actor": "System: Browser Data Collector",
                "action": "DATA_POOL_CREATED",
                "details": f"Automatic data collection started. IP: {ip_address}, Device: {data.device.deviceType}",
                "ip_address": ip_address
            }],

            # Zaman Damgalari
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "last_activity": datetime.now(timezone.utc)
        }

        await db.data_pools.insert_one(data_pool_doc)

        logger.info(f"Data pool created: {pool_id} for session {data.sessionId}")

        return {
            "success": True,
            "pool_id": pool_id,
            "session_id": data.sessionId,
            "message": "Data pool created successfully"
        }

    except Exception as e:
        logger.error(f"Error creating data pool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update")
async def update_data_pool(
    data: DataPoolUpdate,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Veri havuzunu guncelle - ek veri ekle
    Kullanici sitede gezindikce, konum degistikce veri eklenir
    """
    try:
        pool = await db.data_pools.find_one({"session_id": data.sessionId})
        if not pool:
            raise HTTPException(status_code=404, detail="Data pool not found for this session")

        update_fields = {
            "updated_at": datetime.now(timezone.utc),
            "last_activity": datetime.now(timezone.utc)
        }

        push_operations = {}

        # Yeni konum verisi
        if data.location:
            push_operations["locations"] = data.location.model_dump()

        # Yeni sayfa gecisleri
        if data.newPages:
            push_operations["page_visits"] = {"$each": data.newPages}

        # Kullanici etkilesimleri
        if data.interactions:
            push_operations["interactions"] = {"$each": data.interactions}

        # Form verileri
        if data.formData:
            update_fields["form_data"] = {**pool.get("form_data", {}), **data.formData}

        update_query = {"$set": update_fields}
        if push_operations:
            update_query["$push"] = push_operations

        await db.data_pools.update_one(
            {"session_id": data.sessionId},
            update_query
        )

        return {"success": True, "message": "Data pool updated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating data pool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-location")
async def add_location(
    data: dict = Body(...),
    request: Request = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Konum verisi ekle - GPS izni verildiginde periyodik olarak cagrilir
    """
    session_id = data.get("sessionId")
    location = data.get("location")

    if not session_id or not location:
        raise HTTPException(status_code=400, detail="sessionId and location required")

    try:
        location_doc = {
            **location,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        result = await db.data_pools.update_one(
            {"session_id": session_id},
            {
                "$push": {"locations": location_doc},
                "$set": {
                    "updated_at": datetime.now(timezone.utc),
                    "last_activity": datetime.now(timezone.utc)
                }
            }
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Data pool not found")

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding location: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/link-client")
async def link_client_to_pool(
    data: dict = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Session'i bir client_number ile eslestir
    Chat sirasinda veya kayit sirasinda kullanilir
    """
    session_id = data.get("sessionId")
    client_number = data.get("clientNumber")

    if not session_id or not client_number:
        raise HTTPException(status_code=400, detail="sessionId and clientNumber required")

    try:
        # Client'in var olup olmadigini kontrol et
        client = await db.clients.find_one({"clientNumber": client_number})

        result = await db.data_pools.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "client_number": client_number,
                    "client_name": f"{client.get('firstName', '')} {client.get('lastName', '')}" if client else None,
                    "updated_at": datetime.now(timezone.utc)
                },
                "$push": {
                    "chain_of_custody": {
                        "id": str(uuid.uuid4()),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "actor": "System: Client Linker",
                        "action": "CLIENT_LINKED",
                        "details": f"Session linked to client: {client_number}"
                    }
                }
            }
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Data pool not found")

        # Ayrica forensic_analyses'e de kayit olustur
        pool = await db.data_pools.find_one({"session_id": session_id})
        if pool:
            case_id = f"BROWSER_{client_number}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

            forensic_record = {
                "case_id": case_id,
                "client_number": client_number,
                "source": "browser_data_pool",
                "pool_id": pool.get("pool_id"),
                "session_id": session_id,
                "status": "completed",
                "data_type": "browser_forensics",
                "device_info": pool.get("device", {}),
                "fingerprint": pool.get("fingerprint", {}),
                "locations": pool.get("locations", []),
                "ip_address": pool.get("ip_address"),
                "statistics": {
                    "location_points": len(pool.get("locations", [])),
                    "page_visits": len(pool.get("page_visits", [])),
                    "interactions": len(pool.get("interactions", []))
                },
                "chain_of_custody": [{
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.now(timezone.utc),
                    "actor": "System: Browser Forensics",
                    "action": "BROWSER_DATA_CAPTURED",
                    "details": f"Browser forensic data linked to client case. Pool ID: {pool.get('pool_id')}"
                }],
                "created_at": datetime.now(timezone.utc)
            }

            await db.forensic_analyses.insert_one(forensic_record)

        return {"success": True, "message": f"Client {client_number} linked to session"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking client: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-session/{session_id}")
async def get_pool_by_session(
    session_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Session ID ile veri havuzunu getir
    """
    pool = await db.data_pools.find_one(
        {"session_id": session_id},
        {"_id": 0}
    )

    if not pool:
        raise HTTPException(status_code=404, detail="Data pool not found")

    # datetime nesnelerini string'e cevir
    if pool.get("created_at"):
        pool["created_at"] = pool["created_at"].isoformat()
    if pool.get("updated_at"):
        pool["updated_at"] = pool["updated_at"].isoformat()
    if pool.get("last_activity"):
        pool["last_activity"] = pool["last_activity"].isoformat()

    return pool


@router.get("/by-client/{client_number}")
async def get_pools_by_client(
    client_number: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Client number ile tum veri havuzlarini getir
    """
    pools = await db.data_pools.find(
        {"client_number": client_number},
        {"_id": 0}
    ).sort("created_at", -1).to_list(length=100)

    for pool in pools:
        if pool.get("created_at"):
            pool["created_at"] = pool["created_at"].isoformat()
        if pool.get("updated_at"):
            pool["updated_at"] = pool["updated_at"].isoformat()

    return {"pools": pools, "total": len(pools)}


@router.get("/summary/{session_id}")
async def get_pool_summary(
    session_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Beyan dogrulama icin veri havuzu ozeti
    """
    pool = await db.data_pools.find_one({"session_id": session_id})

    if not pool:
        raise HTTPException(status_code=404, detail="Data pool not found")

    # Ozet bilgileri olustur
    summary = {
        "pool_id": pool.get("pool_id"),
        "session_id": session_id,
        "client_number": pool.get("client_number"),
        "status": pool.get("status"),

        # Cihaz Ozeti
        "device_summary": {
            "type": pool.get("device", {}).get("deviceType", "unknown"),
            "os": pool.get("device", {}).get("os"),
            "browser": pool.get("device", {}).get("browser"),
            "is_mobile": pool.get("device", {}).get("isMobile", False)
        },

        # Konum Ozeti
        "location_summary": {
            "total_points": len(pool.get("locations", [])),
            "last_location": pool.get("locations", [])[-1] if pool.get("locations") else None,
            "countries": list(set(loc.get("country") for loc in pool.get("locations", []) if loc.get("country"))),
            "cities": list(set(loc.get("city") for loc in pool.get("locations", []) if loc.get("city")))
        },

        # IP ve Baglanti
        "connection_info": {
            "ip_address": pool.get("ip_address"),
            "referrer": pool.get("referrer"),
            "landing_page": pool.get("landing_page")
        },

        # Aktivite Ozeti
        "activity_summary": {
            "page_visits": len(pool.get("page_visits", [])),
            "interactions": len(pool.get("interactions", [])),
            "has_form_data": bool(pool.get("form_data"))
        },

        # Izinler
        "permissions": pool.get("permissions", {}),

        # Zaman Bilgisi
        "created_at": pool.get("created_at").isoformat() if pool.get("created_at") else None,
        "last_activity": pool.get("last_activity").isoformat() if pool.get("last_activity") else None
    }

    return summary
