"""
Document Templates Router
Legal document templates with variable substitution and PDF generation
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import Response
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
import uuid
import re
import json

from ..auth import get_current_admin_user, get_current_user
from .. import db

router = APIRouter(prefix="/templates", tags=["Document Templates"])


# =============================================================================
# Template Categories
# =============================================================================

TEMPLATE_CATEGORIES = {
    "custody": "Velayet Davaları",
    "hague": "Lahey Sözleşmesi",
    "forensic": "Adli Raporlar",
    "consent": "Muvafakatnameler",
    "correspondence": "Yazışmalar",
    "court": "Mahkeme Belgeleri",
    "agreement": "Anlaşmalar",
    "notification": "Bildirimler"
}

# Built-in template definitions
BUILT_IN_TEMPLATES = [
    {
        "template_id": "custody_petition",
        "name": "Velayet Davası Dilekçesi",
        "category": "custody",
        "description": "Standart velayet davası açılış dilekçesi",
        "language": "tr",
        "variables": [
            {"key": "client_name", "label": "Müvekkil Adı", "type": "text", "required": True},
            {"key": "client_tc", "label": "T.C. Kimlik No", "type": "text", "required": True},
            {"key": "client_address", "label": "Müvekkil Adresi", "type": "textarea", "required": True},
            {"key": "defendant_name", "label": "Davalı Adı", "type": "text", "required": True},
            {"key": "defendant_address", "label": "Davalı Adresi", "type": "textarea", "required": True},
            {"key": "child_name", "label": "Çocuğun Adı", "type": "text", "required": True},
            {"key": "child_birthdate", "label": "Çocuğun Doğum Tarihi", "type": "date", "required": True},
            {"key": "court_name", "label": "Mahkeme Adı", "type": "text", "required": True},
            {"key": "case_facts", "label": "Dava Olayları", "type": "textarea", "required": True},
            {"key": "request_details", "label": "Talep Detayları", "type": "textarea", "required": True}
        ],
        "content": """
{{court_name}} SAYIN HAKİMLİĞİ'NE

DAVACI: {{client_name}}
T.C. Kimlik No: {{client_tc}}
Adres: {{client_address}}

DAVALI: {{defendant_name}}
Adres: {{defendant_address}}

KONU: Velayet hakkının davacıya verilmesi talebi hakkındadır.

AÇIKLAMALAR:

1. Müşterek çocuğumuz {{child_name}} (Doğum Tarihi: {{child_birthdate}}) hakkında velayet hakkının tarafıma verilmesini talep etmekteyim.

2. {{case_facts}}

HUKUKİ NEDENLER: TMK md. 182, 183, 336 ve ilgili mevzuat.

DELİLLER: Nüfus kayıtları, tanık beyanları, uzman raporları ve her türlü yasal delil.

SONUÇ VE TALEP:
{{request_details}}

Saygılarımla,

{{client_name}}
Tarih: {{current_date}}
"""
    },
    {
        "template_id": "hague_application",
        "name": "Lahey Sözleşmesi Başvurusu",
        "category": "hague",
        "description": "Uluslararası çocuk kaçırma davası başvuru formu",
        "language": "en",
        "variables": [
            {"key": "applicant_name", "label": "Applicant Name", "type": "text", "required": True},
            {"key": "applicant_nationality", "label": "Nationality", "type": "text", "required": True},
            {"key": "applicant_address", "label": "Address", "type": "textarea", "required": True},
            {"key": "child_name", "label": "Child's Name", "type": "text", "required": True},
            {"key": "child_dob", "label": "Child's Date of Birth", "type": "date", "required": True},
            {"key": "child_nationality", "label": "Child's Nationality", "type": "text", "required": True},
            {"key": "respondent_name", "label": "Respondent Name", "type": "text", "required": True},
            {"key": "habitual_residence", "label": "Habitual Residence Country", "type": "text", "required": True},
            {"key": "current_location", "label": "Current Location", "type": "text", "required": True},
            {"key": "removal_date", "label": "Date of Removal", "type": "date", "required": True},
            {"key": "circumstances", "label": "Circumstances of Removal", "type": "textarea", "required": True}
        ],
        "content": """
APPLICATION UNDER THE HAGUE CONVENTION ON THE CIVIL ASPECTS
OF INTERNATIONAL CHILD ABDUCTION

To: Central Authority of {{current_location}}

I. IDENTITY OF THE APPLICANT

Name: {{applicant_name}}
Nationality: {{applicant_nationality}}
Address: {{applicant_address}}

II. IDENTITY OF THE CHILD

Name: {{child_name}}
Date of Birth: {{child_dob}}
Nationality: {{child_nationality}}

III. IDENTITY OF THE RESPONDENT

Name: {{respondent_name}}

IV. DETAILS OF WRONGFUL REMOVAL

Habitual Residence: {{habitual_residence}}
Current Location: {{current_location}}
Date of Removal: {{removal_date}}

V. CIRCUMSTANCES OF REMOVAL

{{circumstances}}

VI. LEGAL BASIS

The applicant requests the return of the child under Articles 3 and 12 of the Hague Convention.

Date: {{current_date}}

Signature: _____________________
{{applicant_name}}
"""
    },
    {
        "template_id": "forensic_report",
        "name": "Adli Analiz Raporu",
        "category": "forensic",
        "description": "Dijital delil analiz raporu şablonu",
        "language": "tr",
        "variables": [
            {"key": "report_number", "label": "Rapor No", "type": "text", "required": True},
            {"key": "case_id", "label": "Dava No", "type": "text", "required": True},
            {"key": "examiner_name", "label": "İncelemeyi Yapan", "type": "text", "required": True},
            {"key": "examination_date", "label": "İnceleme Tarihi", "type": "date", "required": True},
            {"key": "device_info", "label": "Cihaz Bilgileri", "type": "textarea", "required": True},
            {"key": "findings", "label": "Bulgular", "type": "textarea", "required": True},
            {"key": "conclusion", "label": "Sonuç ve Değerlendirme", "type": "textarea", "required": True}
        ],
        "content": """
ADLİ DİJİTAL ANALİZ RAPORU

Rapor No: {{report_number}}
Dava No: {{case_id}}
Düzenleme Tarihi: {{current_date}}

1. İNCELEMEYİ YAPAN

Ad Soyad: {{examiner_name}}
Tarih: {{examination_date}}

2. İNCELENEN MATERYAL

{{device_info}}

3. BULGULAR

{{findings}}

4. SONUÇ VE DEĞERLENDİRME

{{conclusion}}

5. EKLER

- Hash değerleri ve doğrulama kayıtları
- Ekran görüntüleri
- Zaman çizelgesi

İşbu rapor, adli inceleme standartlarına uygun olarak hazırlanmıştır.

{{examiner_name}}
Adli Bilişim Uzmanı
"""
    },
    {
        "template_id": "consent_form",
        "name": "Veri Toplama Muvafakatnamesi",
        "category": "consent",
        "description": "Dijital delil toplama için müvekkil onay formu",
        "language": "tr",
        "variables": [
            {"key": "client_name", "label": "Müvekkil Adı", "type": "text", "required": True},
            {"key": "client_tc", "label": "T.C. Kimlik No", "type": "text", "required": True},
            {"key": "case_number", "label": "Dava/Dosya No", "type": "text", "required": True},
            {"key": "data_types", "label": "Toplanacak Veri Türleri", "type": "textarea", "required": True},
            {"key": "platforms", "label": "Platformlar", "type": "text", "required": True},
            {"key": "purpose", "label": "Kullanım Amacı", "type": "textarea", "required": True}
        ],
        "content": """
DİJİTAL VERİ TOPLAMA MUVAFAKATNAMESİ

Ben, aşağıda imzası bulunan {{client_name}} (T.C. Kimlik No: {{client_tc}}),
{{case_number}} numaralı dosya kapsamında;

1. TOPLANACAK VERİLER

Aşağıdaki platformlardan dijital verilerin toplanmasına muvafakat ediyorum:

Platformlar: {{platforms}}

Veri Türleri:
{{data_types}}

2. KULLANIM AMACI

{{purpose}}

3. ONAY

Yukarıda belirtilen verilerin toplanması, işlenmesi ve hukuki süreçlerde
delil olarak kullanılmasına açık rızam ile muvafakat ediyorum.

Bu muvafakat, tarafımca her zaman geri alınabilir niteliktedir.

Tarih: {{current_date}}

Ad Soyad: {{client_name}}
İmza: _____________________
"""
    },
    {
        "template_id": "court_motion",
        "name": "Ara Karar Talebi",
        "category": "court",
        "description": "Tedbir kararı talep dilekçesi",
        "language": "tr",
        "variables": [
            {"key": "court_name", "label": "Mahkeme Adı", "type": "text", "required": True},
            {"key": "case_number", "label": "Esas No", "type": "text", "required": True},
            {"key": "client_name", "label": "Davacı/Davalı Adı", "type": "text", "required": True},
            {"key": "motion_type", "label": "Talep Türü", "type": "select", "options": ["Tedbir Kararı", "Bilirkişi İncelemesi", "Tanık Dinleme", "Keşif"], "required": True},
            {"key": "motion_reason", "label": "Talep Gerekçesi", "type": "textarea", "required": True},
            {"key": "request_details", "label": "Talep Detayları", "type": "textarea", "required": True}
        ],
        "content": """
{{court_name}} SAYIN HAKİMLİĞİ'NE

DOSYA NO: {{case_number}}

TALEPTE BULUNAN: {{client_name}}

TALEP KONUSU: {{motion_type}} hakkındadır.

AÇIKLAMALAR:

1. Sayın Mahkemenizde görülmekte olan yukarıda esas numarası yazılı dava
   kapsamında aşağıdaki talebimizi sunmaktayız.

2. TALEP GEREKÇESİ:

{{motion_reason}}

3. TALEP DETAYLARI:

{{request_details}}

SONUÇ VE TALEP:

Yukarıda açıklanan nedenlerle, {{motion_type}} talebimizin kabulüne
karar verilmesini saygılarımla arz ve talep ederim.

Tarih: {{current_date}}

{{client_name}}
"""
    },
    {
        "template_id": "client_notification",
        "name": "Müvekkil Bilgilendirme Yazısı",
        "category": "notification",
        "description": "Dava gelişmeleri hakkında müvekkil bilgilendirmesi",
        "language": "tr",
        "variables": [
            {"key": "client_name", "label": "Müvekkil Adı", "type": "text", "required": True},
            {"key": "case_number", "label": "Dosya No", "type": "text", "required": True},
            {"key": "subject", "label": "Konu", "type": "text", "required": True},
            {"key": "update_content", "label": "Güncelleme İçeriği", "type": "textarea", "required": True},
            {"key": "next_steps", "label": "Sonraki Adımlar", "type": "textarea", "required": True},
            {"key": "lawyer_name", "label": "Avukat Adı", "type": "text", "required": True}
        ],
        "content": """
SAFECHILD HUKUK BÜROSU
Müvekkil Bilgilendirme Yazısı

Tarih: {{current_date}}

Sayın {{client_name}},

Dosya No: {{case_number}}
Konu: {{subject}}

{{update_content}}

SONRAKİ ADIMLAR:

{{next_steps}}

Herhangi bir sorunuz olması halinde bizimle iletişime geçmekten çekinmeyiniz.

Saygılarımızla,

{{lawyer_name}}
SafeChild Hukuk Bürosu

---
Bu belge gizlidir ve yalnızca alıcısı tarafından kullanılmak üzere gönderilmiştir.
"""
    }
]


# =============================================================================
# Template CRUD Operations
# =============================================================================

@router.get("/categories")
async def get_template_categories(
    current_user: dict = Depends(get_current_user)
):
    """Get all template categories."""
    return {
        "categories": [
            {"id": k, "name": v} for k, v in TEMPLATE_CATEGORIES.items()
        ]
    }


@router.get("")
async def list_templates(
    category: Optional[str] = None,
    language: Optional[str] = None,
    search: Optional[str] = None,
    include_builtin: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """List all available templates."""

    templates = []

    # Add built-in templates
    if include_builtin:
        for t in BUILT_IN_TEMPLATES:
            if category and t["category"] != category:
                continue
            if language and t.get("language") != language:
                continue
            if search and search.lower() not in t["name"].lower():
                continue
            templates.append({
                **t,
                "is_builtin": True,
                "created_at": None
            })

    # Add custom templates from database
    query = {"is_deleted": {"$ne": True}}
    if category:
        query["category"] = category
    if language:
        query["language"] = language
    if search:
        query["name"] = {"$regex": search, "$options": "i"}

    custom = await db.db.document_templates.find(query).to_list(100)

    for t in custom:
        templates.append({
            "template_id": t["template_id"],
            "name": t["name"],
            "category": t["category"],
            "description": t.get("description", ""),
            "language": t.get("language", "tr"),
            "variables": t.get("variables", []),
            "is_builtin": False,
            "created_at": t.get("created_at"),
            "created_by": t.get("created_by")
        })

    return {
        "templates": templates,
        "total": len(templates)
    }


@router.get("/{template_id}")
async def get_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific template by ID."""

    # Check built-in templates
    for t in BUILT_IN_TEMPLATES:
        if t["template_id"] == template_id:
            return {**t, "is_builtin": True}

    # Check custom templates
    template = await db.db.document_templates.find_one({
        "template_id": template_id,
        "is_deleted": {"$ne": True}
    })

    if not template:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")

    return {
        "template_id": template["template_id"],
        "name": template["name"],
        "category": template["category"],
        "description": template.get("description", ""),
        "language": template.get("language", "tr"),
        "variables": template.get("variables", []),
        "content": template.get("content", ""),
        "is_builtin": False,
        "created_at": template.get("created_at"),
        "updated_at": template.get("updated_at")
    }


@router.post("")
async def create_template(
    data: dict = Body(...),
    current_user: dict = Depends(get_current_admin_user)
):
    """Create a new custom template."""

    required = ["name", "category", "content", "variables"]
    for field in required:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"{field} zorunludur")

    template_id = f"custom_{uuid.uuid4().hex[:12]}"

    template = {
        "template_id": template_id,
        "name": data["name"],
        "category": data["category"],
        "description": data.get("description", ""),
        "language": data.get("language", "tr"),
        "variables": data["variables"],
        "content": data["content"],
        "created_at": datetime.utcnow(),
        "created_by": current_user.get("email"),
        "updated_at": datetime.utcnow(),
        "is_deleted": False
    }

    await db.db.document_templates.insert_one(template)

    return {
        "success": True,
        "template_id": template_id,
        "message": "Şablon oluşturuldu"
    }


@router.put("/{template_id}")
async def update_template(
    template_id: str,
    data: dict = Body(...),
    current_user: dict = Depends(get_current_admin_user)
):
    """Update a custom template."""

    # Cannot update built-in templates
    for t in BUILT_IN_TEMPLATES:
        if t["template_id"] == template_id:
            raise HTTPException(status_code=400, detail="Yerleşik şablonlar düzenlenemez")

    update_data = {
        "updated_at": datetime.utcnow(),
        "updated_by": current_user.get("email")
    }

    for field in ["name", "category", "description", "language", "variables", "content"]:
        if field in data:
            update_data[field] = data[field]

    result = await db.db.document_templates.update_one(
        {"template_id": template_id, "is_deleted": {"$ne": True}},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")

    return {"success": True, "message": "Şablon güncellendi"}


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """Delete a custom template (soft delete)."""

    # Cannot delete built-in templates
    for t in BUILT_IN_TEMPLATES:
        if t["template_id"] == template_id:
            raise HTTPException(status_code=400, detail="Yerleşik şablonlar silinemez")

    result = await db.db.document_templates.update_one(
        {"template_id": template_id},
        {"$set": {"is_deleted": True, "deleted_at": datetime.utcnow()}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")

    return {"success": True, "message": "Şablon silindi"}


# =============================================================================
# Document Generation
# =============================================================================

@router.post("/{template_id}/generate")
async def generate_document(
    template_id: str,
    data: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Generate a document from a template with variable substitution."""

    # Get template
    template = None

    # Check built-in
    for t in BUILT_IN_TEMPLATES:
        if t["template_id"] == template_id:
            template = t
            break

    # Check custom
    if not template:
        template = await db.db.document_templates.find_one({
            "template_id": template_id,
            "is_deleted": {"$ne": True}
        })

    if not template:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")

    variables = data.get("variables", {})

    # Validate required variables
    for var in template.get("variables", []):
        if var.get("required") and var["key"] not in variables:
            raise HTTPException(
                status_code=400,
                detail=f"Zorunlu alan eksik: {var['label']}"
            )

    # Add automatic variables
    variables["current_date"] = datetime.now().strftime("%d.%m.%Y")
    variables["current_time"] = datetime.now().strftime("%H:%M")
    variables["current_year"] = datetime.now().strftime("%Y")

    # Perform variable substitution
    content = template.get("content", "")

    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        content = content.replace(placeholder, str(value) if value else "")

    # Check for any remaining unsubstituted variables
    remaining = re.findall(r'\{\{(\w+)\}\}', content)

    # Save generated document record
    doc_record = {
        "document_id": f"doc_{uuid.uuid4().hex[:12]}",
        "template_id": template_id,
        "template_name": template.get("name"),
        "variables_used": variables,
        "content": content,
        "generated_at": datetime.utcnow(),
        "generated_by": current_user.get("email"),
        "client_number": data.get("client_number"),
        "case_id": data.get("case_id")
    }

    await db.db.generated_documents.insert_one(doc_record)

    return {
        "success": True,
        "document_id": doc_record["document_id"],
        "content": content,
        "warnings": remaining if remaining else None,
        "generated_at": doc_record["generated_at"].isoformat()
    }


@router.get("/generated/list")
async def list_generated_documents(
    client_number: Optional[str] = None,
    case_id: Optional[str] = None,
    template_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    """List generated documents."""

    query = {}
    if client_number:
        query["client_number"] = client_number
    if case_id:
        query["case_id"] = case_id
    if template_id:
        query["template_id"] = template_id

    docs = await db.db.generated_documents.find(query).sort(
        "generated_at", -1
    ).limit(limit).to_list(limit)

    return {
        "documents": [
            {
                "document_id": d["document_id"],
                "template_name": d.get("template_name"),
                "client_number": d.get("client_number"),
                "case_id": d.get("case_id"),
                "generated_at": d["generated_at"],
                "generated_by": d.get("generated_by")
            }
            for d in docs
        ],
        "total": len(docs)
    }


@router.get("/generated/{document_id}")
async def get_generated_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific generated document."""

    doc = await db.db.generated_documents.find_one({"document_id": document_id})

    if not doc:
        raise HTTPException(status_code=404, detail="Belge bulunamadı")

    return {
        "document_id": doc["document_id"],
        "template_id": doc.get("template_id"),
        "template_name": doc.get("template_name"),
        "content": doc.get("content"),
        "variables_used": doc.get("variables_used"),
        "client_number": doc.get("client_number"),
        "case_id": doc.get("case_id"),
        "generated_at": doc["generated_at"],
        "generated_by": doc.get("generated_by")
    }


# =============================================================================
# Template Preview
# =============================================================================

@router.post("/{template_id}/preview")
async def preview_template(
    template_id: str,
    data: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Preview a template with sample data without saving."""

    # Get template
    template = None

    for t in BUILT_IN_TEMPLATES:
        if t["template_id"] == template_id:
            template = t
            break

    if not template:
        template = await db.db.document_templates.find_one({
            "template_id": template_id,
            "is_deleted": {"$ne": True}
        })

    if not template:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")

    variables = data.get("variables", {})

    # Add automatic variables
    variables["current_date"] = datetime.now().strftime("%d.%m.%Y")
    variables["current_time"] = datetime.now().strftime("%H:%M")
    variables["current_year"] = datetime.now().strftime("%Y")

    content = template.get("content", "")

    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        content = content.replace(placeholder, str(value) if value else "")

    return {
        "preview": content,
        "template_name": template.get("name")
    }


# =============================================================================
# Auto-fill from Case/Client Data
# =============================================================================

@router.get("/{template_id}/autofill")
async def get_autofill_data(
    template_id: str,
    client_number: Optional[str] = None,
    case_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get auto-fill suggestions based on client/case data."""

    autofill = {}

    # Get client data
    if client_number:
        client = await db.db.clients.find_one({"clientNumber": client_number})
        if client:
            autofill["client_name"] = client.get("name", "")
            autofill["client_tc"] = client.get("tcNo", "")
            autofill["client_address"] = client.get("address", "")
            autofill["client_email"] = client.get("email", "")
            autofill["client_phone"] = client.get("phone", "")
            autofill["applicant_name"] = client.get("name", "")
            autofill["applicant_address"] = client.get("address", "")

    # Get case data
    if case_id:
        case = await db.db.cases.find_one({"case_id": case_id})
        if case:
            autofill["case_number"] = case.get("case_id", "")
            autofill["case_id"] = case.get("case_id", "")
            autofill["court_name"] = case.get("court_name", "")
            autofill["child_name"] = case.get("child_name", "")
            autofill["defendant_name"] = case.get("defendant_name", "")

    return {
        "autofill": autofill,
        "message": "Oto-doldurma verileri hazır"
    }
