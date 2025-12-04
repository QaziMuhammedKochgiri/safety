"""
Beyan Doğrulama (Statement Verification) Router
Müvekkil beyanlarını dijital kanıtlarla karşılaştırma sistemi
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field
import uuid
import json
import os

from .. import get_db
from ..auth import get_current_admin

router = APIRouter(prefix="/verification", tags=["Beyan Doğrulama"])


# =============================================================================
# Pydantic Models
# =============================================================================

class StatementItem(BaseModel):
    """Tek bir beyan maddesi"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str  # communication, custody, violence, financial, other
    statement: str  # Müvekkilin beyanı
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    involves_person: Optional[str] = None  # İlgili kişi (eş, çocuk, vs)

class CreateVerificationRequest(BaseModel):
    """Yeni doğrulama talebi"""
    client_number: str
    case_id: Optional[str] = None  # Forensic case ID (varsa)
    session_id: Optional[str] = None  # Chat session ID (varsa)
    statements: List[StatementItem]
    notes: Optional[str] = None

class VerificationResult(BaseModel):
    """Tek bir beyan için doğrulama sonucu"""
    statement_id: str
    status: str  # verified, contradicted, partially_verified, insufficient_data
    confidence: float  # 0-100
    evidence_summary: str
    evidence_details: List[dict]
    recommendation: str


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/create")
async def create_verification(
    request: CreateVerificationRequest,
    background_tasks: BackgroundTasks,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Yeni beyan doğrulama talebi oluştur"""

    # Müvekkil kontrolü
    client = await db.clients.find_one({"clientNumber": request.client_number})
    if not client:
        raise HTTPException(status_code=404, detail="Müvekkil bulunamadı")

    verification_id = f"VER-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

    verification_doc = {
        "verification_id": verification_id,
        "client_number": request.client_number,
        "client_name": f"{client.get('firstName', '')} {client.get('lastName', '')}".strip(),
        "case_id": request.case_id,
        "session_id": request.session_id,
        "statements": [s.dict() for s in request.statements],
        "status": "pending",  # pending, analyzing, completed, failed
        "results": [],
        "summary": None,
        "notes": request.notes,
        "created_by": str(current_admin.get("_id", "admin")),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "analyzed_at": None
    }

    await db.verifications.insert_one(verification_doc)

    # Arka planda analizi başlat
    background_tasks.add_task(
        analyze_statements,
        db,
        verification_id,
        request.client_number,
        request.case_id,
        request.session_id,
        [s.dict() for s in request.statements]
    )

    return {
        "success": True,
        "verification_id": verification_id,
        "message": "Doğrulama talebi oluşturuldu, analiz başlatıldı"
    }


@router.get("/list")
async def list_verifications(
    client_number: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Tüm doğrulama taleplerini listele"""

    query = {}
    if client_number:
        query["client_number"] = client_number
    if status:
        query["status"] = status

    verifications = await db.verifications.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(length=None)

    total = await db.verifications.count_documents(query)

    return {
        "verifications": verifications,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{verification_id}")
async def get_verification(
    verification_id: str,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Tek bir doğrulama talebinin detaylarını getir"""

    verification = await db.verifications.find_one(
        {"verification_id": verification_id},
        {"_id": 0}
    )

    if not verification:
        raise HTTPException(status_code=404, detail="Doğrulama talebi bulunamadı")

    return verification


@router.post("/{verification_id}/reanalyze")
async def reanalyze_verification(
    verification_id: str,
    background_tasks: BackgroundTasks,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Doğrulama talebini tekrar analiz et"""

    verification = await db.verifications.find_one({"verification_id": verification_id})

    if not verification:
        raise HTTPException(status_code=404, detail="Doğrulama talebi bulunamadı")

    # Durumu güncelle
    await db.verifications.update_one(
        {"verification_id": verification_id},
        {"$set": {"status": "pending", "updated_at": datetime.now(timezone.utc)}}
    )

    # Tekrar analiz başlat
    background_tasks.add_task(
        analyze_statements,
        db,
        verification_id,
        verification["client_number"],
        verification.get("case_id"),
        verification.get("session_id"),
        verification["statements"]
    )

    return {"success": True, "message": "Tekrar analiz başlatıldı"}


@router.delete("/{verification_id}")
async def delete_verification(
    verification_id: str,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Doğrulama talebini sil"""

    result = await db.verifications.delete_one({"verification_id": verification_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Doğrulama talebi bulunamadı")

    return {"success": True, "message": "Doğrulama talebi silindi"}


# =============================================================================
# Analiz Fonksiyonları
# =============================================================================

async def analyze_statements(
    db: AsyncIOMotorDatabase,
    verification_id: str,
    client_number: str,
    case_id: Optional[str],
    session_id: Optional[str],
    statements: List[dict]
):
    """Beyanları dijital kanıtlarla karşılaştır"""

    try:
        # Durumu güncelle
        await db.verifications.update_one(
            {"verification_id": verification_id},
            {"$set": {"status": "analyzing", "updated_at": datetime.now(timezone.utc)}}
        )

        # Forensic verilerini topla (data pool dahil)
        forensic_data = await collect_forensic_data(db, client_number, case_id, session_id)

        # Her beyan için analiz yap
        results = []
        for statement in statements:
            result = await analyze_single_statement(statement, forensic_data)
            results.append(result)

        # Genel özet oluştur
        summary = generate_summary(statements, results)

        # Sonuçları kaydet
        await db.verifications.update_one(
            {"verification_id": verification_id},
            {
                "$set": {
                    "status": "completed",
                    "results": results,
                    "summary": summary,
                    "analyzed_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )

    except Exception as e:
        await db.verifications.update_one(
            {"verification_id": verification_id},
            {
                "$set": {
                    "status": "failed",
                    "error": str(e),
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )


async def collect_forensic_data(
    db: AsyncIOMotorDatabase,
    client_number: str,
    case_id: Optional[str],
    session_id: Optional[str] = None
) -> dict:
    """Müvekkile ait tüm forensic verilerini topla (data_pools dahil)"""
    import os
    from pathlib import Path

    data = {
        "sms_messages": [],
        "call_logs": [],
        "whatsapp_messages": [],
        "photos": [],
        "contacts": [],
        "locations": [],
        "browser_data": [],      # Yeni: Tarayıcı verileri
        "device_info": [],       # Yeni: Cihaz bilgileri
        "ip_addresses": [],      # Yeni: IP adresleri
        "fingerprints": []       # Yeni: Browser fingerprints
    }

    # 0. Data Pools'dan verileri al (Browser/Cihaz verileri)
    pool_query = {}
    if client_number:
        pool_query["client_number"] = client_number
    elif session_id:
        pool_query["session_id"] = session_id

    if pool_query:
        data_pools = await db.data_pools.find(pool_query).to_list(length=None)

        for pool in data_pools:
            # Konum verileri
            for loc in pool.get("locations", []):
                if loc.get("latitude") and loc.get("longitude"):
                    data["locations"].append({
                        "latitude": loc.get("latitude"),
                        "longitude": loc.get("longitude"),
                        "accuracy": loc.get("accuracy"),
                        "country": loc.get("country"),
                        "city": loc.get("city"),
                        "timestamp": loc.get("timestamp"),
                        "source": "browser_geolocation"
                    })

            # Cihaz bilgisi
            if pool.get("device"):
                data["device_info"].append({
                    "device_type": pool["device"].get("deviceType"),
                    "os": pool["device"].get("os"),
                    "os_version": pool["device"].get("osVersion"),
                    "browser": pool["device"].get("browser"),
                    "browser_version": pool["device"].get("browserVersion"),
                    "is_mobile": pool["device"].get("isMobile"),
                    "session_id": pool.get("session_id"),
                    "timestamp": pool.get("created_at")
                })

            # IP adresi
            if pool.get("ip_address"):
                data["ip_addresses"].append({
                    "ip": pool.get("ip_address"),
                    "session_id": pool.get("session_id"),
                    "timestamp": pool.get("created_at")
                })

            # Browser fingerprint
            if pool.get("fingerprint"):
                data["fingerprints"].append({
                    "user_agent": pool["fingerprint"].get("userAgent"),
                    "language": pool["fingerprint"].get("language"),
                    "platform": pool["fingerprint"].get("platform"),
                    "timezone": pool["fingerprint"].get("timezone"),
                    "screen_resolution": pool["fingerprint"].get("screenResolution"),
                    "session_id": pool.get("session_id"),
                    "timestamp": pool.get("created_at")
                })

            # Browser data özeti
            data["browser_data"].append({
                "pool_id": pool.get("pool_id"),
                "session_id": pool.get("session_id"),
                "referrer": pool.get("referrer"),
                "landing_page": pool.get("landing_page"),
                "page_visits": len(pool.get("page_visits", [])),
                "permissions": pool.get("permissions", {}),
                "timestamp": pool.get("created_at")
            })

    # 1. forensic_analyses collection'ından verileri al (mobile collection + forensic tools)
    query = {"client_number": client_number}
    if case_id:
        query = {"$or": [{"client_number": client_number}, {"case_id": case_id}]}

    forensic_records = await db.forensic_analyses.find(query).to_list(length=None)

    for record in forensic_records:
        source = record.get("source", "")
        extracted_dir = record.get("extracted_dir")

        # Android Agent verilerini oku (extracted_dir'den JSON dosyalarını)
        if extracted_dir and os.path.exists(extracted_dir):
            extracted_path = Path(extracted_dir)

            # SMS verilerini oku
            sms_file = extracted_path / "sms.json"
            if sms_file.exists():
                try:
                    with open(sms_file, 'r', encoding='utf-8') as f:
                        sms_data = json.load(f)
                        if isinstance(sms_data, list):
                            data["sms_messages"].extend(sms_data)
                except Exception:
                    pass

            # Arama kayıtlarını oku
            calls_file = extracted_path / "call_log.json"
            if calls_file.exists():
                try:
                    with open(calls_file, 'r', encoding='utf-8') as f:
                        calls_data = json.load(f)
                        if isinstance(calls_data, list):
                            data["call_logs"].extend(calls_data)
                except Exception:
                    pass

            # Kişileri oku
            contacts_file = extracted_path / "contacts.json"
            if contacts_file.exists():
                try:
                    with open(contacts_file, 'r', encoding='utf-8') as f:
                        contacts_data = json.load(f)
                        if isinstance(contacts_data, list):
                            data["contacts"].extend(contacts_data)
                except Exception:
                    pass

            # Medya listesini oku
            media_file = extracted_path / "media_list.json"
            if media_file.exists():
                try:
                    with open(media_file, 'r', encoding='utf-8') as f:
                        media_data = json.load(f)
                        if isinstance(media_data, list):
                            data["photos"].extend(media_data)
                except Exception:
                    pass

        # extracted_data varsa onu da ekle (eski format desteği)
        if record.get("extracted_data"):
            extracted = record["extracted_data"]
            if "sms" in extracted:
                data["sms_messages"].extend(extracted["sms"])
            if "calls" in extracted:
                data["call_logs"].extend(extracted["calls"])
            if "whatsapp" in extracted:
                data["whatsapp_messages"].extend(extracted["whatsapp"])
            if "photos" in extracted:
                data["photos"].extend(extracted["photos"])
            if "contacts" in extracted:
                data["contacts"].extend(extracted["contacts"])

    # 2. WhatsApp/Telegram session verilerini al
    social_sessions = await db.social_sessions.find(
        {"client_number": client_number, "status": "completed"}
    ).to_list(length=None)

    for session in social_sessions:
        platform = session.get("platform", "")
        messages = session.get("collected_messages", [])

        if platform == "whatsapp":
            data["whatsapp_messages"].extend(messages)
        # Telegram mesajları da eklenebilir

    # 3. Magic link ile yüklenen dosyaları kontrol et
    evidence_requests = await db.evidence_requests.find(
        {"clientNumber": client_number, "status": "completed"}
    ).to_list(length=None)

    for req in evidence_requests:
        uploaded_files = req.get("uploadedFiles", [])
        for file_info in uploaded_files:
            if file_info.get("type", "").startswith("image/"):
                data["photos"].append({
                    "filename": file_info.get("originalName"),
                    "path": file_info.get("path"),
                    "date": req.get("uploadedAt")
                })

    return data


async def analyze_single_statement(statement: dict, forensic_data: dict) -> dict:
    """Tek bir beyanı analiz et"""

    category = statement.get("category", "other")
    statement_text = statement.get("statement", "")
    date_start = statement.get("date_range_start")
    date_end = statement.get("date_range_end")
    involves_person = statement.get("involves_person")

    evidence_details = []
    evidence_count = 0
    contradicting_count = 0
    supporting_count = 0

    # Kategori bazlı analiz
    if category == "communication":
        # İletişim beyanları: SMS, arama, WhatsApp analizi
        result = analyze_communication(
            statement_text,
            forensic_data,
            date_start,
            date_end,
            involves_person
        )
        evidence_details = result["details"]
        evidence_count = result["total"]
        contradicting_count = result["contradicting"]
        supporting_count = result["supporting"]

    elif category == "custody":
        # Velayet beyanları: Konum, fotoğraf analizi
        result = analyze_custody(
            statement_text,
            forensic_data,
            date_start,
            date_end
        )
        evidence_details = result["details"]
        evidence_count = result["total"]
        contradicting_count = result["contradicting"]
        supporting_count = result["supporting"]

    elif category == "violence":
        # Şiddet beyanları: Mesaj içeriği, arama sıklığı analizi
        result = analyze_violence_claims(
            statement_text,
            forensic_data,
            date_start,
            date_end,
            involves_person
        )
        evidence_details = result["details"]
        evidence_count = result["total"]
        contradicting_count = result["contradicting"]
        supporting_count = result["supporting"]

    elif category == "financial":
        # Finansal beyanlar
        result = analyze_financial_claims(
            statement_text,
            forensic_data,
            date_start,
            date_end
        )
        evidence_details = result["details"]
        evidence_count = result["total"]
        contradicting_count = result["contradicting"]
        supporting_count = result["supporting"]

    else:
        # Genel analiz
        result = analyze_general(
            statement_text,
            forensic_data,
            date_start,
            date_end
        )
        evidence_details = result["details"]
        evidence_count = result["total"]
        contradicting_count = result["contradicting"]
        supporting_count = result["supporting"]

    # Sonuç durumunu belirle
    if evidence_count == 0:
        status = "insufficient_data"
        confidence = 0
        evidence_summary = "Bu beyanı doğrulayacak veya çürütecek yeterli dijital kanıt bulunamadı."
        recommendation = "Ek kanıt toplanması önerilir."
    elif contradicting_count > supporting_count:
        status = "contradicted"
        confidence = min(95, (contradicting_count / evidence_count) * 100)
        evidence_summary = f"{evidence_count} kanıt incelendi, {contradicting_count} tanesi beyanla çelişiyor."
        recommendation = "⚠️ DİKKAT: Bu beyan dijital kanıtlarla çelişiyor. Müvekkille tekrar görüşülmeli."
    elif supporting_count > contradicting_count:
        status = "verified"
        confidence = min(95, (supporting_count / evidence_count) * 100)
        evidence_summary = f"{evidence_count} kanıt incelendi, {supporting_count} tanesi beyanı destekliyor."
        recommendation = "✓ Beyan dijital kanıtlarla tutarlı görünüyor."
    else:
        status = "partially_verified"
        confidence = 50
        evidence_summary = f"{evidence_count} kanıt incelendi, sonuçlar karışık."
        recommendation = "Beyan kısmen doğrulanabildi. Ek inceleme önerilir."

    return {
        "statement_id": statement.get("id"),
        "statement_text": statement_text,
        "category": category,
        "status": status,
        "confidence": round(confidence, 1),
        "evidence_summary": evidence_summary,
        "evidence_details": evidence_details[:10],  # İlk 10 kanıt
        "evidence_count": evidence_count,
        "supporting_count": supporting_count,
        "contradicting_count": contradicting_count,
        "recommendation": recommendation
    }


def analyze_communication(statement: str, data: dict, date_start, date_end, person) -> dict:
    """İletişim beyanlarını analiz et"""

    details = []
    total = 0
    supporting = 0
    contradicting = 0

    statement_lower = statement.lower()

    # "iletişim kuramıyorum", "engelliyor", "cevap vermiyor" gibi ifadeler
    no_contact_keywords = ["iletişim kur", "engel", "cevap ver", "ulaşamıyorum", "aramıyor", "yazmıyor"]
    claims_no_contact = any(kw in statement_lower for kw in no_contact_keywords)

    # SMS analizi
    for sms in data.get("sms_messages", []):
        if person and person.lower() not in str(sms).lower():
            continue
        total += 1
        if claims_no_contact:
            contradicting += 1
            details.append({
                "type": "sms",
                "date": sms.get("date", "Tarih yok"),
                "summary": f"SMS kaydı bulundu",
                "supports_statement": False
            })
        else:
            supporting += 1

    # Arama analizi
    for call in data.get("call_logs", []):
        if person and person.lower() not in str(call).lower():
            continue
        total += 1
        duration = call.get("duration", 0)
        if claims_no_contact:
            contradicting += 1
            details.append({
                "type": "call",
                "date": call.get("date", "Tarih yok"),
                "summary": f"Arama kaydı: {duration} saniye",
                "supports_statement": False
            })
        else:
            supporting += 1

    # WhatsApp analizi
    for msg in data.get("whatsapp_messages", []):
        if person and person.lower() not in str(msg).lower():
            continue
        total += 1
        if claims_no_contact:
            contradicting += 1
            details.append({
                "type": "whatsapp",
                "date": msg.get("date", "Tarih yok"),
                "summary": "WhatsApp mesajı bulundu",
                "supports_statement": False
            })
        else:
            supporting += 1

    return {
        "details": details,
        "total": total,
        "supporting": supporting,
        "contradicting": contradicting
    }


def analyze_custody(statement: str, data: dict, date_start, date_end) -> dict:
    """Velayet beyanlarını analiz et"""

    details = []
    total = 0
    supporting = 0
    contradicting = 0

    statement_lower = statement.lower()

    # "çocukla ilgilenmiyor", "görüşmüyor", "hiç görmedi" gibi ifadeler
    no_custody_keywords = ["ilgilenm", "görüşm", "görme", "ziyaret", "almıyor", "getirmiyor"]
    claims_no_custody = any(kw in statement_lower for kw in no_custody_keywords)

    # Fotoğraf analizi (çocukla birlikte fotoğraflar)
    for photo in data.get("photos", []):
        # Metadata'dan konum ve tarih bilgisi
        photo_date = photo.get("date")
        photo_location = photo.get("location")

        total += 1
        if claims_no_custody:
            # Fotoğraf varsa çelişki olabilir
            contradicting += 1
            details.append({
                "type": "photo",
                "date": photo_date or "Tarih yok",
                "location": photo_location,
                "summary": "Fotoğraf kaydı bulundu",
                "supports_statement": False
            })
        else:
            supporting += 1

    # Konum analizi
    for loc in data.get("locations", []):
        total += 1
        details.append({
            "type": "location",
            "date": loc.get("date", "Tarih yok"),
            "summary": f"Konum: {loc.get('address', 'Adres yok')}",
            "supports_statement": not claims_no_custody
        })
        if claims_no_custody:
            contradicting += 1
        else:
            supporting += 1

    return {
        "details": details,
        "total": total,
        "supporting": supporting,
        "contradicting": contradicting
    }


def analyze_violence_claims(statement: str, data: dict, date_start, date_end, person) -> dict:
    """Şiddet iddialarını analiz et"""

    details = []
    total = 0
    supporting = 0
    contradicting = 0

    # Tehdit içeren mesaj analizi
    threat_keywords = ["öldür", "döv", "vur", "kes", "yakala", "pişman", "görürsün", "bekle"]

    for sms in data.get("sms_messages", []):
        content = str(sms.get("body", "")).lower()
        if any(kw in content for kw in threat_keywords):
            total += 1
            supporting += 1
            details.append({
                "type": "sms_threat",
                "date": sms.get("date", "Tarih yok"),
                "summary": "Tehdit içerikli SMS tespit edildi",
                "supports_statement": True,
                "content_preview": content[:100] + "..." if len(content) > 100 else content
            })

    for msg in data.get("whatsapp_messages", []):
        content = str(msg.get("message", "")).lower()
        if any(kw in content for kw in threat_keywords):
            total += 1
            supporting += 1
            details.append({
                "type": "whatsapp_threat",
                "date": msg.get("date", "Tarih yok"),
                "summary": "Tehdit içerikli WhatsApp mesajı tespit edildi",
                "supports_statement": True,
                "content_preview": content[:100] + "..." if len(content) > 100 else content
            })

    return {
        "details": details,
        "total": total,
        "supporting": supporting,
        "contradicting": contradicting
    }


def analyze_financial_claims(statement: str, data: dict, date_start, date_end) -> dict:
    """Finansal beyanları analiz et"""

    # Şimdilik temel analiz
    return {
        "details": [],
        "total": 0,
        "supporting": 0,
        "contradicting": 0
    }


def analyze_general(statement: str, data: dict, date_start, date_end) -> dict:
    """Genel beyan analizi"""

    details = []
    total = 0

    # Toplam veri sayısını hesapla
    total += len(data.get("sms_messages", []))
    total += len(data.get("call_logs", []))
    total += len(data.get("whatsapp_messages", []))
    total += len(data.get("photos", []))

    if total > 0:
        details.append({
            "type": "summary",
            "summary": f"Toplam {total} dijital kayıt bulundu",
            "supports_statement": None
        })

    return {
        "details": details,
        "total": total,
        "supporting": 0,
        "contradicting": 0
    }


def generate_summary(statements: List[dict], results: List[dict]) -> dict:
    """Genel özet oluştur"""

    total_statements = len(statements)
    verified = sum(1 for r in results if r["status"] == "verified")
    contradicted = sum(1 for r in results if r["status"] == "contradicted")
    partial = sum(1 for r in results if r["status"] == "partially_verified")
    insufficient = sum(1 for r in results if r["status"] == "insufficient_data")

    avg_confidence = sum(r["confidence"] for r in results) / len(results) if results else 0

    # Risk seviyesi belirleme
    if contradicted > 0:
        risk_level = "high"
        risk_message = f"⚠️ YÜKSEK RİSK: {contradicted} beyan dijital kanıtlarla çelişiyor!"
    elif insufficient > total_statements / 2:
        risk_level = "medium"
        risk_message = "⚡ ORTA RİSK: Yeterli dijital kanıt bulunamadı, ek veri gerekli."
    elif partial > 0:
        risk_level = "low"
        risk_message = "ℹ️ DÜŞÜK RİSK: Bazı beyanlar kısmen doğrulanabildi."
    else:
        risk_level = "minimal"
        risk_message = "✓ MİNİMAL RİSK: Beyanlar dijital kanıtlarla tutarlı."

    return {
        "total_statements": total_statements,
        "verified": verified,
        "contradicted": contradicted,
        "partially_verified": partial,
        "insufficient_data": insufficient,
        "average_confidence": round(avg_confidence, 1),
        "risk_level": risk_level,
        "risk_message": risk_message,
        "recommendation": generate_recommendation(risk_level, contradicted, insufficient)
    }


def generate_recommendation(risk_level: str, contradicted: int, insufficient: int) -> str:
    """Avukata öneri oluştur"""

    if risk_level == "high":
        return """
ACIL EYLEM GEREKLİ:
1. Müvekkille yüz yüze görüşme yapın
2. Çelişen beyanlar hakkında açıklama isteyin
3. Mahkemeye sunmadan önce beyanları revize edin
4. Karşı tarafın bu verilere erişim ihtimalini değerlendirin
"""
    elif risk_level == "medium":
        return """
EK VERİ TOPLANMASI ÖNERİLİR:
1. Müvekkilden ek dijital cihaz verisi toplayın
2. Sosyal medya hesaplarını inceleyin
3. Banka kayıtları ve konum verisi talep edin
4. Tanık ifadeleriyle destekleyin
"""
    elif risk_level == "low":
        return """
İNCELEME ÖNERİLİR:
1. Kısmen doğrulanan beyanları gözden geçirin
2. Eksik kısımlar için ek kanıt arayın
3. Beyanları daha spesifik hale getirin
"""
    else:
        return """
OLUMLU DURUM:
1. Beyanlar dijital kanıtlarla tutarlı
2. Mahkemeye güvenle sunulabilir
3. Kanıt dosyasını hazırlayın
"""
