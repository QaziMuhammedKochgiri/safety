from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse
import shutil
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase
from .. import get_db
from ..models import Document
from ..utils import (
    generate_document_number,
    get_upload_directory,
    sanitize_filename,
    is_allowed_file_type
)
from ..auth import get_current_client
from ..email_service import EmailService
import logging

router = APIRouter(prefix="/documents", tags=["Document Management"])
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.txt']

@router.post("/upload")
async def upload_document(
    clientNumber: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Upload document for a client"""
    try:
        client = await db.clients.find_one({"clientNumber": clientNumber})
        if not client:
            raise HTTPException(status_code=404, detail="Invalid client number")
        
        if not is_allowed_file_type(file.filename, ALLOWED_FILE_TYPES):
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_FILE_TYPES)}"
            )
        
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        doc_number = generate_document_number()
        safe_filename = sanitize_filename(file.filename)
        
        client_dir = get_upload_directory(clientNumber)
        file_path = Path(client_dir) / f"{doc_number}_{safe_filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        document = Document(
            documentNumber=doc_number,
            clientNumber=clientNumber,
            fileName=safe_filename,
            fileSize=file_size,
            fileType=Path(safe_filename).suffix,
            filePath=str(file_path),
            uploadedBy="client"
        )
        
        await db.documents.insert_one(document.model_dump())
        
        return {
            "success": True,
            "documentNumber": doc_number,
            "fileName": safe_filename,
            "uploadedAt": document.uploadedAt
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_number}/download")
async def download_document(document_number: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Download document by document number"""
    document = await db.documents.find_one({"documentNumber": document_number}, {"_id": 0})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = Path(document['filePath'])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")
    
    return FileResponse(
        path=file_path,
        filename=document['fileName'],
        media_type='application/octet-stream'
    )

@router.get("/client/{client_number}")
async def get_client_documents(client_number: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get all documents for a client"""
    documents = await db.documents.find({"clientNumber": client_number}, {"_id": 0}).to_list(length=None)
    return {"documents": documents}

@router.get("/portal/my-documents")
async def get_my_documents(current_client: dict = Depends(get_current_client), db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get authenticated client's documents (protected route)"""
    try:
        documents = await db.documents.find(
            {"clientNumber": current_client["clientNumber"]},
            {"_id": 0}
        ).to_list(length=None)
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/all")
async def get_all_documents(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get all documents (admin only)"""
    try:
        documents = await db.documents.find({}, {"_id": 0}).sort("uploadedAt", -1).to_list(length=None)
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{document_number}")
async def delete_document(document_number: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Delete a document by document number"""
    try:
        document = await db.documents.find_one({"documentNumber": document_number})
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete file from disk
        file_path = Path(document.get('filePath', ''))
        if file_path.exists():
            file_path.unlink()

        # Delete from database
        await db.documents.delete_one({"documentNumber": document_number})

        return {"success": True, "message": "Document deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/portal/upload")
async def upload_my_document(
    file: UploadFile = File(...),
    current_client: dict = Depends(get_current_client),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Upload document for authenticated client (protected route)"""
    try:
        client_number = current_client["clientNumber"]
        
        if not is_allowed_file_type(file.filename, ALLOWED_FILE_TYPES):
            raise HTTPException(status_code=400, detail=f"File type not allowed.")
        
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        doc_number = generate_document_number()
        safe_filename = sanitize_filename(file.filename)
        
        client_dir = get_upload_directory(client_number)
        file_path = Path(client_dir) / f"{doc_number}_{safe_filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        document = Document(
            documentNumber=doc_number,
            clientNumber=client_number,
            fileName=safe_filename,
            fileSize=file_size,
            fileType=Path(safe_filename).suffix,
            filePath=str(file_path),
            uploadedBy="client"
        )
        
        await db.documents.insert_one(document.model_dump())
        
        try:
            client_info = await db.clients.find_one({"clientNumber": client_number})
            recipient_name = f"{client_info.get('firstName', '')} {client_info.get('lastName', '')}".strip()
            
            EmailService.send_document_uploaded(
                recipient_email=current_client["email"],
                recipient_name=recipient_name or "Client",
                document_name=safe_filename,
                document_number=doc_number,
                uploaded_at=document.uploadedAt.strftime('%d.%m.%Y %H:%M') if document.uploadedAt else ""
            )
            logger.info(f"Document upload confirmation sent to {current_client['email']}")
        except Exception as e:
            logger.error(f"Failed to send document upload email: {str(e)}")
        
        return {
            "success": True,
            "documentNumber": doc_number,
            "fileName": safe_filename,
            "uploadedAt": document.uploadedAt
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
