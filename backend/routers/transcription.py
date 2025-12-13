"""
Transcription API Router

Provides endpoints for speech-to-text transcription using Whisper.
"""

import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from pydantic import BaseModel, Field

from ..auth import get_current_admin
from ..database import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..forensics.ai import (
    SpeechToTextEngine,
    TranscriptionResult,
    TranscriptionSource
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/transcriptions", tags=["transcription"])

# Global engine instance (lazy loaded)
_engine: Optional[SpeechToTextEngine] = None


def get_engine() -> SpeechToTextEngine:
    """Get or create speech-to-text engine"""
    global _engine
    if _engine is None:
        _engine = SpeechToTextEngine(whisper_model="base")
    return _engine


# Pydantic models

class TranscriptResponse(BaseModel):
    id: str
    caseId: str
    fileName: str
    source: str
    language: str
    duration: float
    durationFormatted: str
    fullText: str
    wordCount: int
    createdAt: str
    processingTime: float
    modelUsed: str
    keywords: List[str]
    sentimentScore: float
    riskIndicators: List[str]


class TranscriptSegmentResponse(BaseModel):
    start: float
    end: float
    text: str
    confidence: float
    startFormatted: str
    endFormatted: str


class TranscriptDetailResponse(TranscriptResponse):
    segments: List[TranscriptSegmentResponse]


class SearchResultResponse(BaseModel):
    transcriptId: str
    fileName: str
    source: str
    matchCount: int
    matchingSegments: List[TranscriptSegmentResponse]


class TranscriptionStatsResponse(BaseModel):
    totalTranscriptions: int
    totalDuration: float
    totalDurationFormatted: str
    totalWords: int
    languageBreakdown: dict
    sourceBreakdown: dict
    riskStats: dict


@router.post("/{case_id}/transcribe")
async def transcribe_audio(
    case_id: str,
    file: UploadFile = File(...),
    language: Optional[str] = Query(None, description="ISO language code (e.g., 'tr', 'en')"),
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> TranscriptDetailResponse:
    """
    Transcribe an audio file.

    Supports WhatsApp voice notes (.opus), Telegram audio, video files, etc.
    Uses OpenAI Whisper for transcription.
    """
    try:
        # Validate case exists
        case = await db.cases.find_one({"_id": case_id})
        if not case:
            case = await db.cases.find_one({"case_id": case_id})
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # Read file
        audio_data = await file.read()

        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        # Process audio
        engine = get_engine()
        result = engine.process_audio(
            audio_data=audio_data,
            file_name=file.filename or "audio",
            case_id=case_id,
            language=language
        )

        # Store in database
        transcript_doc = {
            "_id": result.id,
            "case_id": case_id,
            "file_name": result.file_name,
            "source": result.source.value,
            "language": result.language,
            "duration": result.duration,
            "full_text": result.full_text,
            "segments": [s.to_dict() for s in result.segments],
            "word_count": result.word_count,
            "processing_time": result.processing_time,
            "model_used": result.model_used,
            "keywords": result.keywords,
            "sentiment_score": result.sentiment_score,
            "risk_indicators": result.risk_indicators,
            "created_at": datetime.now(),
            "created_by": current_user.get("id")
        }

        await db.transcriptions.insert_one(transcript_doc)

        # Log activity
        await db.audit_logs.insert_one({
            "action": "audio_transcription",
            "case_id": case_id,
            "user_id": current_user.get("id"),
            "timestamp": datetime.now(),
            "details": {
                "file_name": result.file_name,
                "duration": result.duration,
                "language": result.language,
                "word_count": result.word_count
            }
        })

        return TranscriptDetailResponse(
            id=result.id,
            caseId=result.case_id,
            fileName=result.file_name,
            source=result.source.value,
            language=result.language,
            duration=result.duration,
            durationFormatted=result._format_duration(result.duration),
            fullText=result.full_text,
            wordCount=result.word_count,
            createdAt=result.created_at.isoformat(),
            processingTime=result.processing_time,
            modelUsed=result.model_used,
            keywords=result.keywords,
            sentimentScore=result.sentiment_score,
            riskIndicators=result.risk_indicators,
            segments=[
                TranscriptSegmentResponse(
                    start=s.start,
                    end=s.end,
                    text=s.text,
                    confidence=s.confidence,
                    startFormatted=s._format_time(s.start),
                    endFormatted=s._format_time(s.end)
                )
                for s in result.segments
            ]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{case_id}/batch-transcribe")
async def batch_transcribe(
    case_id: str,
    files: List[UploadFile] = File(...),
    language: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Transcribe multiple audio files.

    Processes files sequentially and returns results for each.
    """
    try:
        # Validate case
        case = await db.cases.find_one({"_id": case_id})
        if not case:
            case = await db.cases.find_one({"case_id": case_id})
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        engine = get_engine()
        results = []
        errors = []

        for file in files:
            try:
                audio_data = await file.read()
                if len(audio_data) == 0:
                    errors.append({"fileName": file.filename, "error": "Empty file"})
                    continue

                result = engine.process_audio(
                    audio_data=audio_data,
                    file_name=file.filename or "audio",
                    case_id=case_id,
                    language=language
                )

                # Store in database
                transcript_doc = {
                    "_id": result.id,
                    "case_id": case_id,
                    "file_name": result.file_name,
                    "source": result.source.value,
                    "language": result.language,
                    "duration": result.duration,
                    "full_text": result.full_text,
                    "segments": [s.to_dict() for s in result.segments],
                    "word_count": result.word_count,
                    "processing_time": result.processing_time,
                    "model_used": result.model_used,
                    "keywords": result.keywords,
                    "sentiment_score": result.sentiment_score,
                    "risk_indicators": result.risk_indicators,
                    "created_at": datetime.now(),
                    "created_by": current_user.get("id")
                }

                await db.transcriptions.insert_one(transcript_doc)
                results.append(result.to_dict())

            except Exception as e:
                errors.append({"fileName": file.filename, "error": str(e)})

        # Log activity
        await db.audit_logs.insert_one({
            "action": "batch_transcription",
            "case_id": case_id,
            "user_id": current_user.get("id"),
            "timestamp": datetime.now(),
            "details": {
                "total_files": len(files),
                "successful": len(results),
                "failed": len(errors)
            }
        })

        return {
            "success": True,
            "totalFiles": len(files),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{case_id}")
async def get_transcriptions(
    case_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> List[TranscriptResponse]:
    """Get all transcriptions for a case"""
    transcripts = await db.transcriptions.find(
        {"case_id": case_id}
    ).sort("created_at", -1).to_list(length=None)

    return [
        TranscriptResponse(
            id=t["_id"],
            caseId=t["case_id"],
            fileName=t["file_name"],
            source=t["source"],
            language=t["language"],
            duration=t["duration"],
            durationFormatted=_format_duration(t["duration"]),
            fullText=t["full_text"],
            wordCount=t["word_count"],
            createdAt=t["created_at"].isoformat() if t.get("created_at") else "",
            processingTime=t.get("processing_time", 0),
            modelUsed=t.get("model_used", "unknown"),
            keywords=t.get("keywords", []),
            sentimentScore=t.get("sentiment_score", 0),
            riskIndicators=t.get("risk_indicators", [])
        )
        for t in transcripts
    ]


@router.get("/{case_id}/transcript/{transcript_id}")
async def get_transcript_detail(
    case_id: str,
    transcript_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> TranscriptDetailResponse:
    """Get detailed transcription with segments"""
    transcript = await db.transcriptions.find_one({
        "_id": transcript_id,
        "case_id": case_id
    })

    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    return TranscriptDetailResponse(
        id=transcript["_id"],
        caseId=transcript["case_id"],
        fileName=transcript["file_name"],
        source=transcript["source"],
        language=transcript["language"],
        duration=transcript["duration"],
        durationFormatted=_format_duration(transcript["duration"]),
        fullText=transcript["full_text"],
        wordCount=transcript["word_count"],
        createdAt=transcript["created_at"].isoformat() if transcript.get("created_at") else "",
        processingTime=transcript.get("processing_time", 0),
        modelUsed=transcript.get("model_used", "unknown"),
        keywords=transcript.get("keywords", []),
        sentimentScore=transcript.get("sentiment_score", 0),
        riskIndicators=transcript.get("risk_indicators", []),
        segments=[
            TranscriptSegmentResponse(
                start=s["start"],
                end=s["end"],
                text=s["text"],
                confidence=s.get("confidence", 0),
                startFormatted=s.get("startFormatted", ""),
                endFormatted=s.get("endFormatted", "")
            )
            for s in transcript.get("segments", [])
        ]
    )


@router.get("/{case_id}/search")
async def search_transcripts(
    case_id: str,
    query: str = Query(..., min_length=2),
    case_sensitive: bool = Query(False),
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> List[SearchResultResponse]:
    """
    Search through all transcripts for a case.

    Returns matching transcripts with highlighted segments.
    """
    transcripts = await db.transcriptions.find(
        {"case_id": case_id}
    ).to_list(length=None)

    results = []
    search_query = query if case_sensitive else query.lower()

    for t in transcripts:
        full_text = t["full_text"] if case_sensitive else t["full_text"].lower()

        if search_query in full_text:
            # Find matching segments
            matching_segments = []
            for seg in t.get("segments", []):
                seg_text = seg["text"] if case_sensitive else seg["text"].lower()
                if search_query in seg_text:
                    matching_segments.append(TranscriptSegmentResponse(
                        start=seg["start"],
                        end=seg["end"],
                        text=seg["text"],
                        confidence=seg.get("confidence", 0),
                        startFormatted=seg.get("startFormatted", ""),
                        endFormatted=seg.get("endFormatted", "")
                    ))

            results.append(SearchResultResponse(
                transcriptId=t["_id"],
                fileName=t["file_name"],
                source=t["source"],
                matchCount=full_text.count(search_query),
                matchingSegments=matching_segments
            ))

    # Log search
    await db.audit_logs.insert_one({
        "action": "transcript_search",
        "case_id": case_id,
        "user_id": current_user.get("id"),
        "timestamp": datetime.now(),
        "details": {
            "query": query,
            "results_count": len(results)
        }
    })

    return results


@router.get("/{case_id}/stats")
async def get_transcription_stats(
    case_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> TranscriptionStatsResponse:
    """Get transcription statistics for a case"""
    transcripts = await db.transcriptions.find(
        {"case_id": case_id}
    ).to_list(length=None)

    if not transcripts:
        return TranscriptionStatsResponse(
            totalTranscriptions=0,
            totalDuration=0,
            totalDurationFormatted="00:00",
            totalWords=0,
            languageBreakdown={},
            sourceBreakdown={},
            riskStats={"high": 0, "medium": 0, "low": 0, "none": 0}
        )

    total_duration = sum(t.get("duration", 0) for t in transcripts)
    total_words = sum(t.get("word_count", 0) for t in transcripts)

    # Language breakdown
    language_breakdown = {}
    for t in transcripts:
        lang = t.get("language", "unknown")
        language_breakdown[lang] = language_breakdown.get(lang, 0) + 1

    # Source breakdown
    source_breakdown = {}
    for t in transcripts:
        source = t.get("source", "unknown")
        source_breakdown[source] = source_breakdown.get(source, 0) + 1

    # Risk stats
    risk_stats = {"high": 0, "medium": 0, "low": 0, "none": 0}
    for t in transcripts:
        risk_count = len(t.get("risk_indicators", []))
        if risk_count >= 5:
            risk_stats["high"] += 1
        elif risk_count >= 2:
            risk_stats["medium"] += 1
        elif risk_count >= 1:
            risk_stats["low"] += 1
        else:
            risk_stats["none"] += 1

    return TranscriptionStatsResponse(
        totalTranscriptions=len(transcripts),
        totalDuration=total_duration,
        totalDurationFormatted=_format_duration(total_duration),
        totalWords=total_words,
        languageBreakdown=language_breakdown,
        sourceBreakdown=source_breakdown,
        riskStats=risk_stats
    )


@router.delete("/{case_id}/transcript/{transcript_id}")
async def delete_transcript(
    case_id: str,
    transcript_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a transcription"""
    result = await db.transcriptions.delete_one({
        "_id": transcript_id,
        "case_id": case_id
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transcript not found")

    # Log deletion
    await db.audit_logs.insert_one({
        "action": "transcript_delete",
        "case_id": case_id,
        "user_id": current_user.get("id"),
        "timestamp": datetime.now(),
        "details": {"transcript_id": transcript_id}
    })

    return {"success": True, "message": "Transcript deleted"}


def _format_duration(seconds: float) -> str:
    """Format duration as HH:MM:SS or MM:SS"""
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"
