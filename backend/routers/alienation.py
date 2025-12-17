"""
Parental Alienation Analysis API Router
Provides endpoints for analyzing parental alienation patterns in communications.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..ai.alienation.tactics_database import AlienationTacticDB
from ..ai.alienation.pattern_matcher import PatternMatcher, MatchResult
from ..ai.alienation.severity_scorer import SeverityScorer, SeverityResult
from ..ai.alienation.timeline_analyzer import TimelineAnalyzer, TimelineEvent
from ..ai.alienation.expert_report import ExpertReportGenerator, ReportLanguage
from .. import db

router = APIRouter(
    prefix="/alienation",
    tags=["alienation"],
    responses={404: {"description": "Not found"}},
)


# =============================================================================
# Pydantic Models
# =============================================================================

class MessageInput(BaseModel):
    """Input model for a single message to analyze."""
    id: str
    content: str
    sender: str
    timestamp: datetime
    platform: Optional[str] = "unknown"


class AnalysisRequest(BaseModel):
    """Request model for alienation analysis."""
    case_id: str
    messages: List[MessageInput]
    include_timeline: bool = True
    include_severity: bool = True


class TacticMatch(BaseModel):
    """A single tactic match result."""
    tactic_id: str
    tactic_name: str
    category: str
    confidence: float
    severity: int
    matched_text: str
    context: Optional[str] = None
    literature_refs: List[str] = []


class AnalysisResponse(BaseModel):
    """Response model for alienation analysis."""
    case_id: str
    total_messages: int
    total_matches: int
    severity_score: float
    severity_level: str
    categories: Dict[str, int]
    matches: List[TacticMatch]
    timeline: Optional[List[Dict[str, Any]]] = None
    recommendations: List[str] = []
    analyzed_at: datetime


class TacticInfo(BaseModel):
    """Information about a single alienation tactic."""
    id: str
    name: str
    category: str
    description: str
    severity: int
    indicators: List[str]
    literature: List[str]


class ReportRequest(BaseModel):
    """Request model for generating expert report."""
    case_id: str
    language: str = "en"  # en, de, tr
    include_evidence: bool = True
    include_recommendations: bool = True


class ReportResponse(BaseModel):
    """Response model for expert report."""
    case_id: str
    language: str
    report_html: str
    report_text: str
    generated_at: datetime


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_messages(request: AnalysisRequest):
    """
    Analyze messages for parental alienation tactics.

    This endpoint examines a collection of messages and identifies
    potential parental alienation patterns using NLP matching and
    a database of 50+ known alienation tactics.
    """
    try:
        # Initialize components
        tactics_db = AlienationTacticDB()
        pattern_matcher = PatternMatcher(tactics_db)
        severity_scorer = SeverityScorer()

        # Analyze each message
        all_matches = []
        for msg in request.messages:
            matches = pattern_matcher.analyze_text(
                text=msg.content,
                context={
                    "sender": msg.sender,
                    "timestamp": msg.timestamp.isoformat(),
                    "platform": msg.platform
                }
            )
            for match in matches:
                tactic = tactics_db.get_tactic(match.tactic_id)
                if tactic:
                    all_matches.append(TacticMatch(
                        tactic_id=match.tactic_id,
                        tactic_name=tactic.name,
                        category=tactic.category.value,
                        confidence=match.confidence,
                        severity=tactic.severity,
                        matched_text=match.matched_text,
                        context=msg.content[:200] if len(msg.content) > 200 else msg.content,
                        literature_refs=tactic.literature_refs
                    ))

        # Calculate category counts
        categories = {}
        for match in all_matches:
            cat = match.category
            categories[cat] = categories.get(cat, 0) + 1

        # Calculate severity score
        severity_result = None
        if request.include_severity and all_matches:
            severity_result = severity_scorer.calculate_score([
                {"tactic_id": m.tactic_id, "severity": m.severity, "confidence": m.confidence}
                for m in all_matches
            ])

        # Generate timeline
        timeline = None
        if request.include_timeline and all_matches:
            timeline_analyzer = TimelineAnalyzer()
            events = [
                TimelineEvent(
                    timestamp=msg.timestamp,
                    tactic_id=m.tactic_id,
                    severity=m.severity,
                    content=m.matched_text
                )
                for msg, m in zip(request.messages, all_matches)
            ]
            timeline = timeline_analyzer.analyze(events)

        # Generate recommendations based on severity
        recommendations = []
        if severity_result:
            if severity_result.score >= 8:
                recommendations = [
                    "Immediate professional intervention recommended",
                    "Consider supervised visitation",
                    "Document all communications",
                    "Consult with child psychologist"
                ]
            elif severity_result.score >= 5:
                recommendations = [
                    "Professional evaluation recommended",
                    "Parenting coordinator may be helpful",
                    "Continue documentation"
                ]
            else:
                recommendations = [
                    "Monitor situation",
                    "Keep communication records"
                ]

        # Store analysis in database
        analysis_doc = {
            "case_id": request.case_id,
            "type": "alienation_analysis",
            "total_messages": len(request.messages),
            "total_matches": len(all_matches),
            "severity_score": severity_result.score if severity_result else 0,
            "categories": categories,
            "analyzed_at": datetime.utcnow()
        }
        await db.db.forensic_analyses.update_one(
            {"case_id": request.case_id, "type": "alienation_analysis"},
            {"$set": analysis_doc},
            upsert=True
        )

        return AnalysisResponse(
            case_id=request.case_id,
            total_messages=len(request.messages),
            total_matches=len(all_matches),
            severity_score=severity_result.score if severity_result else 0,
            severity_level=severity_result.level if severity_result else "unknown",
            categories=categories,
            matches=all_matches,
            timeline=timeline,
            recommendations=recommendations,
            analyzed_at=datetime.utcnow()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/tactics", response_model=List[TacticInfo])
async def get_tactics(
    category: Optional[str] = Query(None, description="Filter by category"),
    min_severity: Optional[int] = Query(None, ge=1, le=10, description="Minimum severity")
):
    """
    Get list of all known alienation tactics.

    Returns the complete database of parental alienation tactics
    with descriptions, indicators, and literature references.
    """
    try:
        tactics_db = AlienationTacticDB()
        tactics = tactics_db.get_all_tactics()

        result = []
        for tactic in tactics:
            # Apply filters
            if category and tactic.category.value != category:
                continue
            if min_severity and tactic.severity < min_severity:
                continue

            result.append(TacticInfo(
                id=tactic.id,
                name=tactic.name,
                category=tactic.category.value,
                description=tactic.description,
                severity=tactic.severity,
                indicators=tactic.indicators,
                literature=tactic.literature_refs
            ))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tactics: {str(e)}")


@router.get("/tactics/{tactic_id}", response_model=TacticInfo)
async def get_tactic(tactic_id: str):
    """Get details of a specific alienation tactic."""
    try:
        tactics_db = AlienationTacticDB()
        tactic = tactics_db.get_tactic(tactic_id)

        if not tactic:
            raise HTTPException(status_code=404, detail="Tactic not found")

        return TacticInfo(
            id=tactic.id,
            name=tactic.name,
            category=tactic.category.value,
            description=tactic.description,
            severity=tactic.severity,
            indicators=tactic.indicators,
            literature=tactic.literature_refs
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tactic: {str(e)}")


@router.get("/report/{case_id}")
async def get_report(
    case_id: str,
    language: str = Query("en", description="Report language: en, de, tr")
):
    """
    Generate expert witness report for a case.

    Creates a comprehensive report suitable for court proceedings,
    including all identified alienation patterns, severity assessment,
    and recommendations.
    """
    try:
        # Get analysis from database
        analysis = await db.db.forensic_analyses.find_one({
            "case_id": case_id,
            "type": "alienation_analysis"
        })

        if not analysis:
            raise HTTPException(status_code=404, detail="No analysis found for this case")

        # Map language string to enum
        lang_map = {"en": ReportLanguage.ENGLISH, "de": ReportLanguage.GERMAN, "tr": ReportLanguage.TURKISH}
        report_lang = lang_map.get(language, ReportLanguage.ENGLISH)

        # Generate report
        report_generator = ExpertReportGenerator()
        report = report_generator.generate(
            case_id=case_id,
            analysis_data=analysis,
            language=report_lang
        )

        return {
            "case_id": case_id,
            "language": language,
            "report_html": report.html,
            "report_text": report.text,
            "sections": report.sections,
            "generated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/timeline/{case_id}")
async def get_timeline(case_id: str):
    """
    Get alienation timeline for a case.

    Returns a chronological view of all identified alienation
    incidents with severity trends and escalation patterns.
    """
    try:
        # Get all analyses for this case
        analyses = await db.db.forensic_analyses.find({
            "case_id": case_id
        }).to_list(length=100)

        if not analyses:
            raise HTTPException(status_code=404, detail="No data found for this case")

        # Build timeline from analyses
        timeline_events = []
        for analysis in analyses:
            if "matches" in analysis:
                for match in analysis.get("matches", []):
                    timeline_events.append({
                        "timestamp": match.get("timestamp"),
                        "tactic": match.get("tactic_name"),
                        "category": match.get("category"),
                        "severity": match.get("severity"),
                        "content_preview": match.get("matched_text", "")[:100]
                    })

        # Sort by timestamp
        timeline_events.sort(key=lambda x: x.get("timestamp", ""))

        # Detect escalation patterns
        severities = [e.get("severity", 0) for e in timeline_events]
        escalation_trend = "stable"
        if len(severities) >= 3:
            recent_avg = sum(severities[-3:]) / 3
            older_avg = sum(severities[:3]) / 3
            if recent_avg > older_avg + 1:
                escalation_trend = "increasing"
            elif recent_avg < older_avg - 1:
                escalation_trend = "decreasing"

        return {
            "case_id": case_id,
            "total_events": len(timeline_events),
            "escalation_trend": escalation_trend,
            "events": timeline_events,
            "generated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get timeline: {str(e)}")


@router.post("/score")
async def calculate_severity(messages: List[MessageInput]):
    """
    Calculate severity score for a set of messages.

    Quick endpoint for getting just the severity score
    without full analysis details.
    """
    try:
        tactics_db = AlienationTacticDB()
        pattern_matcher = PatternMatcher(tactics_db)
        severity_scorer = SeverityScorer()

        # Analyze messages
        all_matches = []
        for msg in messages:
            matches = pattern_matcher.analyze_text(msg.content)
            for match in matches:
                tactic = tactics_db.get_tactic(match.tactic_id)
                if tactic:
                    all_matches.append({
                        "tactic_id": match.tactic_id,
                        "severity": tactic.severity,
                        "confidence": match.confidence
                    })

        # Calculate score
        if not all_matches:
            return {
                "score": 0,
                "level": "none",
                "matches": 0,
                "message": "No alienation patterns detected"
            }

        result = severity_scorer.calculate_score(all_matches)

        return {
            "score": result.score,
            "level": result.level,
            "matches": len(all_matches),
            "category_breakdown": result.category_scores if hasattr(result, "category_scores") else {}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")


@router.get("/categories")
async def get_categories():
    """
    Get list of alienation tactic categories.

    Returns all categories with their descriptions and
    typical severity ranges.
    """
    try:
        from ..ai.alienation.tactics_database import TacticCategory

        categories = []
        for cat in TacticCategory:
            # Count tactics in this category
            tactics_db = AlienationTacticDB()
            count = len([t for t in tactics_db.get_all_tactics() if t.category == cat])

            categories.append({
                "id": cat.value,
                "name": cat.value.replace("_", " ").title(),
                "tactic_count": count,
                "description": _get_category_description(cat.value)
            })

        return categories

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


def _get_category_description(category: str) -> str:
    """Get description for a tactic category."""
    descriptions = {
        "badmouthing": "Negative comments about the other parent to the child",
        "limiting_contact": "Restricting communication or visitation with the other parent",
        "erasing_parent": "Removing evidence or memory of the other parent",
        "creating_fear": "Instilling fear about the other parent in the child",
        "forcing_rejection": "Pressuring child to reject the other parent",
        "undermining_authority": "Weakening the other parent's parental authority",
        "destroying_memories": "Attacking positive memories of the other parent",
        "creating_conflict": "Encouraging conflicts between child and other parent",
        "emotional_manipulation": "Using emotional tactics to influence the child",
        "false_allegations": "Making false claims about the other parent"
    }
    return descriptions.get(category, "Alienation tactic category")
