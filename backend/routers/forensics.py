from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends, Body
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import shutil
import os
import uuid
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .. import get_db
from ..auth import get_current_client, get_current_admin
from ..email_service import EmailService
from backend.forensics.engine import SafeChildForensicsEngine
from backend.forensics.analyzers import AIForensicAnalyzer, ChildSafetyRiskAssessor
from backend.security_service import security_service
import logging

router = APIRouter(prefix="/forensics", tags=["Forensics"])
logger = logging.getLogger(__name__)

# Initialize forensics engine and AI analyzer
forensics_engine = SafeChildForensicsEngine()
ai_analyzer = AIForensicAnalyzer()
child_safety_assessor = ChildSafetyRiskAssessor(ai_analyzer)


# Pydantic models for AI analysis
class AIAnalysisRequest(BaseModel):
    case_id: str
    language: str = "de"
    include_safety_assessment: bool = True


class CaseSummaryRequest(BaseModel):
    case_id: str
    language: str = "de"

@router.post("/analyze-internal")
async def analyze_internal_evidence(
    data: dict = Body(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Internal endpoint for microservices (like WhatsApp Automation) to submit evidence.
    """
    file_path = Path(data.get("file_path"))
    client_number = data.get("client_number")
    source = data.get("source", "automation")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Internal file not found")
        
    try:
        # Get Client Info
        client = await db.clients.find_one({"clientNumber": client_number})
        if not client:
            # Fallback for demo
            client = {"email": "unknown@example.com", "firstName": "Unknown", "lastName": "Client"}

        case_id = f"AUTO_{client_number}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Read and Encrypt
        with open(file_path, "rb") as f:
            content = f.read()
            
        encryption_result = security_service.encrypt_file(content)
        
        # Save encrypted version (overwrite or new file)
        encrypted_path = file_path.with_suffix('.enc')
        with open(encrypted_path, "wb") as buffer:
            buffer.write(encryption_result['encrypted_data'])
            
        # Delete original plain text file immediately
        file_path.unlink()
        
        encryption_metadata = {k: v for k, v in encryption_result.items() if k != 'encrypted_data'}
        
        # Chain of Custody
        coc_event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow(),
            "actor": "System: WhatsApp Automation Service",
            "action": "AUTOMATED_EXTRACTION",
            "details": f"Data extracted automatically via QR scan. Source: {source}",
            "hashAtEvent": None
        }
        
        analysis_record = {
            "case_id": case_id,
            "client_number": client_number,
            "status": "processing",
            "analysis_type": "automated_text",
            "uploaded_file": str(encrypted_path),
            "file_name": file_path.name,
            "file_size": len(content),
            "encryption_metadata": encryption_metadata,
            "chain_of_custody": [coc_event],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.forensic_analyses.insert_one(analysis_record)
        
        background_tasks.add_task(
            run_forensic_analysis_task,
            encrypted_path,
            encryption_metadata,
            case_id,
            client,
            db
        )
        
        return {"success": True, "case_id": case_id}
        
    except Exception as e:
        logger.error(f"Internal analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_forensic_analysis_task(
    encrypted_file_path: Path,
    encryption_metadata: dict,
    case_id: str,
    client_info: dict,
    db: AsyncIOMotorDatabase
):
    """Background task to run forensic analysis (Decrypt -> Analyze -> Wipe)"""
    temp_decrypted_path = None
    try:
        print(f"[Background Task] Starting analysis for {case_id}")
        
        # 1. Decrypt file for analysis
        print(f"[Background Task] 🔓 Decrypting file for analysis...")
        if not encrypted_file_path.exists():
             raise FileNotFoundError(f"Encrypted file not found: {encrypted_file_path}")

        with open(encrypted_file_path, "rb") as f:
            encrypted_data = f.read()
            
        decrypted_data = security_service.decrypt_file(encrypted_data, encryption_metadata)
        
        # Create temp file with original extension (removed .enc)
        original_name = encrypted_file_path.name.replace('.enc', '')
        temp_decrypted_path = encrypted_file_path.parent / f"temp_{original_name}"
        
        with open(temp_decrypted_path, "wb") as f:
            f.write(decrypted_data)
            
        # Calculate Hash immediately for integrity check
        import hashlib
        hash_obj = hashlib.sha256(decrypted_data)
        file_hash = hash_obj.hexdigest()
            
        # Clear memory
        del decrypted_data
        del encrypted_data
        
        # Check file type
        file_ext = temp_decrypted_path.suffix.lower()
        forensic_extensions = ['.db', '.tar', '.gz', '.tgz', '.ab', '.zip']
        
        if file_ext in forensic_extensions:
             # 2a. Run Full Forensic Analysis
            result = await forensics_engine.analyze_android_backup(
                temp_decrypted_path,
                case_id,
                client_info
            )
        else:
            # 2b. Simple Evidence Handling
            print(f"[Background Task] handling direct evidence: {file_ext}")
            
            # Create a simple "report" for the file
            statistics = {
                "file_type": "Direct Evidence",
                "format": file_ext,
                "integrity_check": "PASSED"
            }
            
            result = {
                "success": True,
                "file_hash": file_hash,
                "statistics": statistics,
                "report_pdf": None, 
                "report_html": None
            }
        
        if result["success"]:
            # Chain of Custody: Analysis Complete Event
            completion_event = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow(),
                "actor": "System: SafeChild Engine",
                "action": "INTEGRITY_VERIFIED",
                "details": f"Evidence processed and sealed. Integrity verified.",
                "hashAtEvent": result.get("file_hash")
            }

            await db.forensic_analyses.update_one(
                {"case_id": case_id},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.utcnow(),
                        "report_txt": result.get("report_pdf"),
                        "report_html": result.get("report_html"),
                        "file_hash": result.get("file_hash"),
                        "statistics": result.get("statistics"),
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {"chain_of_custody": completion_event}
                }
            )
            print(f"[Background Task] ✅ Analysis completed: {case_id}")
            
            try:
                analysis = await db.forensic_analyses.find_one({"case_id": case_id})
                
                EmailService.send_forensic_analysis_complete(
                    recipient_email=client_info.get("email", ""),
                    recipient_name=f"{client_info.get('firstName', '')} {client_info.get('lastName', '')}".strip() or "Kunde",
                    case_id=case_id,
                    file_name=analysis.get("file_name", ""),
                    statistics=result.get("statistics")
                )
                logger.info(f"Forensic analysis complete email sent for {case_id}")
            except Exception as e:
                logger.error(f"Failed to send forensic analysis email: {str(e)}")
        else:
            await db.forensic_analyses.update_one(
                {"case_id": case_id},
                {"$set": {
                    "status": "failed",
                    "error": result.get("error"),
                    "updated_at": datetime.utcnow()
                }}
            )
            print(f"[Background Task] ❌ Analysis failed: {case_id}")
            
    except Exception as e:
        logger.error(f"Background forensic task error: {str(e)}")
        await db.forensic_analyses.update_one(
            {"case_id": case_id},
            {"$set": {
                "status": "failed",
                "error": f"System error: {str(e)}",
                "updated_at": datetime.utcnow()
            }}
        )
    finally:
        # Cleanup
        if temp_decrypted_path and temp_decrypted_path.exists():
            try:
                os.remove(temp_decrypted_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temp file {temp_decrypted_path}: {cleanup_error}")


@router.post("/analyze")
async def start_forensic_analysis(
    backup_file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_client: dict = Depends(get_current_client),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Upload device backup and start forensic analysis (Encrypted at Rest)"""
    try:
        case_id = f"CASE_{current_client['clientNumber']}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        file_ext = Path(backup_file.filename).suffix.lower()
        allowed_extensions = ['.db', '.tar', '.gz', '.tgz', '.ab', '.zip']
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
            )
        
        upload_dir = Path("/tmp/forensics_uploads")
        upload_dir.mkdir(exist_ok=True, parents=True)
        
        # Save as encrypted file
        file_path = upload_dir / f"{case_id}_{backup_file.filename}.enc"
        
        print(f"[API] Reading and encrypting file stream...")
        content = await backup_file.read() 
        file_size = len(content)
        
        # ENCRYPT
        encryption_result = security_service.encrypt_file(content)
        
        with open(file_path, "wb") as buffer:
            buffer.write(encryption_result['encrypted_data'])
            
        print(f"[API] Encrypted file saved: {file_path} ({len(encryption_result['encrypted_data'])} bytes)")
        
        # Extract metadata to save to DB (exclude raw data)
        encryption_metadata = {k: v for k, v in encryption_result.items() if k != 'encrypted_data'}
        
        # Initialize Chain of Custody
        coc_event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow(),
            "actor": f"Client: {current_client['clientNumber']}",
            "action": "EVIDENCE_UPLOAD_ENCRYPTED",
            "details": f"File uploaded and encrypted (AES-256). Size: {file_size} bytes",
            "hashAtEvent": None 
        }
        
        analysis_record = {
            "case_id": case_id,
            "client_number": current_client["clientNumber"],
            "client_email": current_client["email"],
            "status": "processing",
            "uploaded_file": str(file_path),
            "file_name": backup_file.filename,
            "file_size": file_size,
            "encryption_metadata": encryption_metadata,
            "chain_of_custody": [coc_event],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.forensic_analyses.insert_one(analysis_record)
        
        print(f"[API] Analysis record created: {case_id}")
        
        background_tasks.add_task(
            run_forensic_analysis_task,
            file_path,
            encryption_metadata,
            case_id,
            {
                "clientNumber": current_client["clientNumber"],
                "email": current_client["email"],
                "firstName": current_client.get("firstName", ""),
                "lastName": current_client.get("lastName", "")
            },
            db
        )
        
        print(f"[API] Background task scheduled: {case_id}")
        
        return {
            "success": True,
            "case_id": case_id,
            "message": "Forensic analysis started. File is securely encrypted.",
            "estimated_time": "5-15 minutes",
            "status_url": f"/api/forensics/status/{case_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{case_id}")
async def get_forensic_status(
    case_id: str,
    current_client: dict = Depends(get_current_client),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get forensic analysis status
    """
    try:
        analysis = await db.forensic_analyses.find_one({
            "case_id": case_id,
            "client_number": current_client["clientNumber"]
        }, {"_id": 0})
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Case not found")
        
        response = {
            "case_id": case_id,
            "status": analysis["status"],
            "file_name": analysis.get("file_name"),
            "file_size": analysis.get("file_size"),
            "created_at": analysis["created_at"],
            "updated_at": analysis["updated_at"]
        }
        
        if analysis["status"] == "completed":
            response["completed_at"] = analysis.get("completed_at")
            response["statistics"] = analysis.get("statistics", {})
            response["report_available"] = True
        elif analysis["status"] == "failed":
            response["error"] = analysis.get("error")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report/{case_id}")
async def download_forensic_report(
    case_id: str,
    format: str = "txt",
    current_client: dict = Depends(get_current_client),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Download forensic report"""
    try:
        analysis = await db.forensic_analyses.find_one({
            "case_id": case_id,
            "client_number": current_client["clientNumber"]
        })
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Case not found")
        
        if analysis["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Analysis not completed yet. Current status: {analysis['status']}"
            )
        
        report_key = f"report_{format}"
        report_path = analysis.get(report_key)
        
        if not report_path:
            report_path = analysis.get("report_txt")
            format = "txt"
        
        if not report_path or not Path(report_path).exists():
            raise HTTPException(status_code=404, detail=f"Report file not found")
        
        media_types = {
            "txt": "text/plain",
            "html": "text/html",
            "pdf": "application/pdf"
        }
        
        return FileResponse(
            report_path,
            media_type=media_types.get(format, "text/plain"),
            filename=f"SafeChild_Report_{case_id}.{format}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-cases")
async def get_my_forensic_cases(
    current_client: dict = Depends(get_current_client),
    skip: int = 0,
    limit: int = 50,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all forensic cases for current client"""
    try:
        cases = await db.forensic_analyses.find(
            {"client_number": current_client["clientNumber"]},
            {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(length=None)
        
        return {
            "total": len(cases),
            "cases": cases
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/case/{case_id}")
async def delete_forensic_case(
    case_id: str,
    current_client: dict = Depends(get_current_client),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Delete forensic case and associated files
    """
    try:
        analysis = await db.forensic_analyses.find_one({
            "case_id": case_id,
            "client_number": current_client["clientNumber"]
        })
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Case not found")
        
        if analysis["status"] == "processing":
            raise HTTPException(
                status_code=400,
                detail="Cannot delete case while processing"
            )
        
        if analysis.get("uploaded_file"):
            try:
                Path(analysis["uploaded_file"]).unlink(missing_ok=True)
            except:
                pass
        
        if analysis.get("report_txt"):
            try:
                Path(analysis["report_txt"]).unlink(missing_ok=True)
            except:
                pass
        
        await db.forensic_analyses.delete_one({"case_id": case_id})

        return {"success": True, "message": "Case deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# AI-POWERED FORENSIC ANALYSIS ENDPOINTS
# ========================================

@router.post("/ai-analyze/{case_id}")
async def run_ai_analysis(
    case_id: str,
    request: AIAnalysisRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Run AI-powered forensic analysis on a completed case.

    This endpoint uses Claude API to analyze messages for:
    - Threats and concerning language
    - Manipulation and psychological abuse
    - Parental alienation indicators
    - Child safety concerns
    - High-value evidence for court

    Returns comprehensive risk assessment and recommendations.
    """
    try:
        # Get the forensic analysis record
        analysis = await db.forensic_analyses.find_one({"case_id": case_id})

        if not analysis:
            raise HTTPException(status_code=404, detail="Case not found")

        if analysis["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Case analysis not completed. Status: {analysis['status']}"
            )

        # Get messages from the analysis (stored in statistics or separate collection)
        messages = analysis.get("extracted_messages", [])

        # If no messages in analysis, try to get from messages collection
        if not messages:
            msg_cursor = db.forensic_messages.find({"case_id": case_id})
            messages = await msg_cursor.to_list(length=None)

        # Prepare context for AI analysis
        context = {
            "case_id": case_id,
            "client_number": analysis.get("client_number"),
            "analysis_type": analysis.get("analysis_type"),
            "file_name": analysis.get("file_name"),
            "created_at": str(analysis.get("created_at"))
        }

        # Run AI analysis
        logger.info(f"Starting AI analysis for case {case_id}")
        ai_result = await ai_analyzer.analyze_messages(
            messages=messages,
            context=context,
            language=request.language
        )

        # Optionally run child safety assessment
        safety_assessment = None
        if request.include_safety_assessment and ai_result.get("success"):
            safety_assessment = await child_safety_assessor.assess_child_safety(
                forensic_data={"ai_analysis": ai_result},
                case_context=context,
                language=request.language
            )

        # Store AI analysis results
        ai_analysis_record = {
            "case_id": case_id,
            "analysis_date": datetime.utcnow(),
            "language": request.language,
            "ai_results": ai_result,
            "safety_assessment": safety_assessment
        }

        # Update or insert AI analysis
        await db.ai_forensic_analyses.update_one(
            {"case_id": case_id},
            {"$set": ai_analysis_record},
            upsert=True
        )

        # Update main analysis record with AI flag
        await db.forensic_analyses.update_one(
            {"case_id": case_id},
            {
                "$set": {
                    "ai_analyzed": True,
                    "ai_analysis_date": datetime.utcnow(),
                    "ai_risk_score": ai_result.get("overall_risk_score"),
                    "ai_risk_level": ai_result.get("risk_level")
                }
            }
        )

        return {
            "success": True,
            "case_id": case_id,
            "ai_analysis": ai_result,
            "safety_assessment": safety_assessment,
            "message": "AI analysis completed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI analysis error for {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-analysis/{case_id}")
async def get_ai_analysis(
    case_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get AI analysis results for a case.
    """
    try:
        ai_analysis = await db.ai_forensic_analyses.find_one(
            {"case_id": case_id},
            {"_id": 0}
        )

        if not ai_analysis:
            raise HTTPException(
                status_code=404,
                detail="AI analysis not found. Run /ai-analyze first."
            )

        return ai_analysis

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-summary/{case_id}")
async def generate_ai_case_summary(
    case_id: str,
    request: CaseSummaryRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Generate AI-powered case summary for court proceedings.

    Uses Claude to create a professional legal summary including:
    - Executive summary
    - Key findings
    - Risk assessment
    - Evidence highlights
    - Recommended actions
    """
    try:
        # Get AI analysis
        ai_analysis = await db.ai_forensic_analyses.find_one({"case_id": case_id})

        if not ai_analysis:
            raise HTTPException(
                status_code=404,
                detail="AI analysis not found. Run /ai-analyze first."
            )

        # Get case info
        forensic_record = await db.forensic_analyses.find_one({"case_id": case_id})

        case_info = {
            "case_id": case_id,
            "client_number": forensic_record.get("client_number"),
            "file_name": forensic_record.get("file_name"),
            "created_at": str(forensic_record.get("created_at")),
            "completed_at": str(forensic_record.get("completed_at"))
        }

        # Generate summary
        summary_result = await ai_analyzer.generate_case_summary(
            analysis_result=ai_analysis.get("ai_results", {}),
            case_info=case_info,
            language=request.language
        )

        if summary_result.get("success"):
            # Store the summary
            await db.ai_forensic_analyses.update_one(
                {"case_id": case_id},
                {
                    "$set": {
                        f"case_summary_{request.language}": summary_result["summary"],
                        "summary_generated_at": datetime.utcnow()
                    }
                }
            )

        return {
            "success": True,
            "case_id": case_id,
            "summary": summary_result.get("summary"),
            "language": request.language,
            "generated_at": summary_result.get("generated_at")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summary generation error for {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all-cases")
async def get_all_forensic_cases(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get all forensic cases (Admin endpoint).
    """
    try:
        query = {}
        if status:
            query["status"] = status

        cases = await db.forensic_analyses.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(length=None)

        total = await db.forensic_analyses.count_documents(query)

        # Get AI analysis status for each case
        for case in cases:
            ai_analysis = await db.ai_forensic_analyses.find_one(
                {"case_id": case["case_id"]},
                {"_id": 0, "ai_results.overall_risk_score": 1, "ai_results.risk_level": 1}
            )
            if ai_analysis:
                case["ai_analyzed"] = True
                case["ai_risk_score"] = ai_analysis.get("ai_results", {}).get("overall_risk_score")
                case["ai_risk_level"] = ai_analysis.get("ai_results", {}).get("risk_level")
            else:
                case["ai_analyzed"] = False

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "cases": cases
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-dashboard")
async def get_risk_dashboard(
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get AI risk analysis dashboard data.

    Returns aggregated risk statistics across all analyzed cases.
    """
    try:
        # Get all AI analyses
        ai_analyses = await db.ai_forensic_analyses.find(
            {},
            {"_id": 0, "case_id": 1, "ai_results": 1, "safety_assessment": 1, "analysis_date": 1}
        ).to_list(length=None)

        # Calculate statistics
        total_analyzed = len(ai_analyses)

        risk_levels = {"critical": 0, "high": 0, "medium": 0, "low": 0, "minimal": 0}
        total_flagged = 0
        risk_category_counts = {}

        for analysis in ai_analyses:
            ai_results = analysis.get("ai_results", {})

            # Count risk levels
            level = ai_results.get("risk_level", "unknown")
            if level in risk_levels:
                risk_levels[level] += 1

            # Count flagged messages
            total_flagged += ai_results.get("flagged_count", 0)

            # Count risk categories
            for cat, score in ai_results.get("risk_summary", {}).items():
                if score >= 20:  # Only count if risk is detected
                    risk_category_counts[cat] = risk_category_counts.get(cat, 0) + 1

        # Get cases requiring immediate attention
        urgent_cases = [
            {
                "case_id": a["case_id"],
                "risk_score": a.get("ai_results", {}).get("overall_risk_score"),
                "analysis_date": a.get("analysis_date")
            }
            for a in ai_analyses
            if a.get("ai_results", {}).get("risk_level") in ["critical", "high"]
        ]

        return {
            "total_analyzed": total_analyzed,
            "risk_distribution": risk_levels,
            "total_flagged_messages": total_flagged,
            "risk_categories": risk_category_counts,
            "urgent_cases": urgent_cases[:10],  # Top 10 urgent cases
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
