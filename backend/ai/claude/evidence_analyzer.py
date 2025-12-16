"""
AI-Powered Evidence Analyzer
Analyzes evidence items (messages, photos, documents) for court cases.

Design: Helps mothers organize and present evidence effectively.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging

from .client import ClaudeClient

logger = logging.getLogger(__name__)


class EvidenceType(str, Enum):
    """Types of evidence."""
    TEXT_MESSAGE = "text_message"  # SMS, WhatsApp, etc.
    EMAIL = "email"
    PHOTO = "photo"  # Images showing abuse, conditions
    VIDEO = "video"
    AUDIO = "audio"  # Voice recordings
    DOCUMENT = "document"  # Legal docs, medical records
    SOCIAL_MEDIA = "social_media"  # Facebook, Instagram posts
    WITNESS_STATEMENT = "witness_statement"
    MEDICAL_RECORD = "medical_record"
    POLICE_REPORT = "police_report"
    SCHOOL_RECORD = "school_record"


class EvidenceRelevance(str, Enum):
    """How relevant evidence is to the case."""
    CRITICAL = "critical"  # Essential to the case
    HIGH = "high"  # Very important
    MODERATE = "moderate"  # Supportive
    LOW = "low"  # Background context
    MINIMAL = "minimal"  # Not very relevant


class EvidenceCategory(str, Enum):
    """Legal categories for evidence."""
    ABUSE = "abuse"  # Physical/emotional abuse
    NEGLECT = "neglect"  # Child neglect
    ALIENATION = "alienation"  # Parental alienation
    THREAT = "threat"  # Threats or harassment
    VIOLATION = "violation"  # Custody order violations
    SUBSTANCE_ABUSE = "substance_abuse"  # Drug/alcohol issues
    SAFETY_CONCERN = "safety_concern"  # Safety hazards
    POSITIVE = "positive"  # Positive evidence for petitioner
    NEUTRAL = "neutral"  # Neutral/contextual


@dataclass
class EvidenceItem:
    """Single piece of evidence."""
    evidence_id: str
    evidence_type: EvidenceType
    title: str
    description: str
    date_occurred: Optional[str] = None
    date_collected: Optional[str] = None
    source: Optional[str] = None  # Who provided it
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceAnalysisRequest:
    """Request to analyze evidence."""
    case_id: str
    evidence_items: List[EvidenceItem]
    case_context: Optional[str] = None  # Brief case summary
    analysis_purpose: str = "custody"  # custody, protection_order, etc.


@dataclass
class AnalyzedEvidence:
    """AI analysis of single evidence item."""
    evidence_id: str
    relevance: EvidenceRelevance
    relevance_score: float  # 0-1
    categories: List[EvidenceCategory]

    # Analysis
    key_findings: List[str]
    legal_significance: str
    court_presentation: str  # How to present in court
    potential_challenges: List[str]  # Opposing counsel objections
    corroboration_needed: bool

    # Context
    related_evidence: List[str]  # IDs of related items
    timeline_position: str


@dataclass
class EvidenceAnalysisResult:
    """Complete evidence analysis result."""
    analysis_id: str
    case_id: str

    # Overall assessment
    total_items: int
    critical_items: int
    evidence_strength: float  # 0-10
    confidence: float  # 0-1

    # Analyzed items
    analyzed_items: List[AnalyzedEvidence]

    # Summaries
    executive_summary: str
    evidence_timeline: List[Dict[str, str]]
    strength_analysis: str
    gaps_identified: List[str]
    recommendations: List[str]

    # Court presentation
    presentation_order: List[str]  # Evidence IDs in recommended order
    opening_statement_points: List[str]

    # Metadata
    analyzed_at: datetime
    model_used: str
    tokens_used: Dict[str, int]


class EvidenceAnalyzer:
    """
    AI-powered evidence analyzer for family law cases.
    Helps organize and present evidence effectively.
    """

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """Initialize evidence analyzer."""
        self.client = claude_client or ClaudeClient()
        logger.info("Evidence Analyzer initialized")

    async def analyze_evidence(
        self,
        request: EvidenceAnalysisRequest
    ) -> EvidenceAnalysisResult:
        """
        Analyze all evidence items for a case.

        Args:
            request: Evidence analysis request

        Returns:
            Comprehensive evidence analysis
        """
        logger.info(
            f"Analyzing {len(request.evidence_items)} evidence items "
            f"for case {request.case_id}"
        )

        # Build analysis prompt
        prompt = self._build_analysis_prompt(request)
        system_prompt = self._get_system_prompt()

        try:
            # Get Claude analysis
            response = await self.client.send_message(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=4096
            )

            # Parse response
            analysis_data = json.loads(response["content"])

            # Parse analyzed items
            analyzed_items = []
            for item_data in analysis_data.get("analyzed_items", []):
                try:
                    # Validate relevance
                    relevance = EvidenceRelevance(item_data.get("relevance", "moderate"))

                    # Parse categories
                    categories = []
                    for cat in item_data.get("categories", []):
                        try:
                            categories.append(EvidenceCategory(cat))
                        except ValueError:
                            continue

                    analyzed_items.append(AnalyzedEvidence(
                        evidence_id=item_data["evidence_id"],
                        relevance=relevance,
                        relevance_score=item_data.get("relevance_score", 0.5),
                        categories=categories,
                        key_findings=item_data.get("key_findings", []),
                        legal_significance=item_data.get("legal_significance", ""),
                        court_presentation=item_data.get("court_presentation", ""),
                        potential_challenges=item_data.get("potential_challenges", []),
                        corroboration_needed=item_data.get("corroboration_needed", False),
                        related_evidence=item_data.get("related_evidence", []),
                        timeline_position=item_data.get("timeline_position", "")
                    ))
                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping invalid evidence item: {e}")
                    continue

            # Create result
            result = EvidenceAnalysisResult(
                analysis_id=f"evidence_{request.case_id}_{datetime.now().timestamp()}",
                case_id=request.case_id,
                total_items=len(request.evidence_items),
                critical_items=sum(1 for item in analyzed_items if item.relevance == EvidenceRelevance.CRITICAL),
                evidence_strength=analysis_data.get("evidence_strength", 5.0),
                confidence=analysis_data.get("confidence", 0.8),
                analyzed_items=analyzed_items,
                executive_summary=analysis_data.get("executive_summary", ""),
                evidence_timeline=analysis_data.get("evidence_timeline", []),
                strength_analysis=analysis_data.get("strength_analysis", ""),
                gaps_identified=analysis_data.get("gaps_identified", []),
                recommendations=analysis_data.get("recommendations", []),
                presentation_order=analysis_data.get("presentation_order", []),
                opening_statement_points=analysis_data.get("opening_statement_points", []),
                analyzed_at=datetime.now(),
                model_used=response["model"],
                tokens_used=response["usage"]
            )

            logger.info(
                f"Evidence analysis complete: {result.total_items} items, "
                f"{result.critical_items} critical, "
                f"strength {result.evidence_strength:.1f}/10"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse evidence analysis: {e}")
            raise ValueError("Invalid AI analysis format")
        except Exception as e:
            logger.error(f"Evidence analysis failed: {e}")
            raise

    def _build_analysis_prompt(self, request: EvidenceAnalysisRequest) -> str:
        """Build evidence analysis prompt."""
        prompt_parts = [
            f"Analyze evidence for a {request.analysis_purpose} case.",
            f"\n**CASE ID:** {request.case_id}",
            f"**TOTAL EVIDENCE ITEMS:** {len(request.evidence_items)}"
        ]

        if request.case_context:
            prompt_parts.extend([
                f"\n**CASE CONTEXT:**",
                request.case_context
            ])

        prompt_parts.append(f"\n**EVIDENCE TO ANALYZE:**")

        for i, item in enumerate(request.evidence_items, 1):
            date_str = f" (Date: {item.date_occurred})" if item.date_occurred else ""
            prompt_parts.append(
                f"\n{i}. [{item.evidence_type.value.upper()}] {item.title}{date_str}"
            )
            prompt_parts.append(f"   Description: {item.description}")
            if item.source:
                prompt_parts.append(f"   Source: {item.source}")

        prompt_parts.append(
            "\nProvide comprehensive evidence analysis in JSON format as specified."
        )

        return "\n".join(prompt_parts)

    def _get_system_prompt(self) -> str:
        """Get system prompt for evidence analysis."""

        return """You are an expert legal evidence analyst specializing in family law cases.

EVIDENCE RELEVANCE LEVELS (use exactly these):
- critical: Essential to proving the case, game-changing evidence
- high: Very important, strongly supports the case
- moderate: Supportive, adds to the overall picture
- low: Provides background context
- minimal: Not very relevant to core issues

EVIDENCE CATEGORIES (use exactly these):
- abuse: Physical or emotional abuse
- neglect: Child neglect or endangerment
- alienation: Parental alienation tactics
- threat: Threats, harassment, intimidation
- violation: Custody order or legal violations
- substance_abuse: Drug or alcohol abuse
- safety_concern: Safety hazards or risks
- positive: Positive evidence for petitioner
- neutral: Neutral or contextual information

CRITICAL ANALYSIS REQUIREMENTS:
1. Assess each piece of evidence objectively
2. Consider admissibility and potential challenges
3. Identify patterns and corroboration
4. Suggest presentation strategy
5. Note gaps that need additional evidence
6. Consider opposing counsel's likely objections
7. Organize chronologically for timeline
8. Focus on child's best interests

OUTPUT FORMAT (JSON):
{
    "evidence_strength": 0.0-10.0,
    "confidence": 0.0-1.0,
    "analyzed_items": [
        {
            "evidence_id": "1",
            "relevance": "critical|high|moderate|low|minimal",
            "relevance_score": 0.0-1.0,
            "categories": ["abuse", "neglect", ...],
            "key_findings": ["Finding 1", "Finding 2"],
            "legal_significance": "Why this matters legally",
            "court_presentation": "How to present this in court",
            "potential_challenges": ["Possible objection 1", "Possible objection 2"],
            "corroboration_needed": true/false,
            "related_evidence": ["2", "5"],
            "timeline_position": "Early/mid/recent pattern"
        }
    ],
    "executive_summary": "2-3 paragraph summary of all evidence",
    "evidence_timeline": [
        {"date": "2024-01-15", "event": "Incident description", "evidence_id": "1"}
    ],
    "strength_analysis": "Overall assessment of evidence strength",
    "gaps_identified": ["Gap 1", "Gap 2"],
    "recommendations": ["Recommendation 1", "Recommendation 2"],
    "presentation_order": ["3", "1", "5", "2", "4"],
    "opening_statement_points": ["Point 1", "Point 2", "Point 3"]
}

IMPORTANT:
- Be objective and honest about evidence quality
- Consider both strengths and weaknesses
- Suggest strategies to overcome weak points
- Organize for maximum impact
- Use clear, professional language
- Focus on child safety and wellbeing
"""

    async def quick_analysis(
        self,
        case_id: str,
        evidence_descriptions: List[str],
        case_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Quick evidence analysis from text descriptions.

        Args:
            case_id: Case identifier
            evidence_descriptions: List of evidence descriptions
            case_context: Brief case summary

        Returns:
            Quick analysis summary
        """
        # Convert descriptions to evidence items
        evidence_items = []
        for i, desc in enumerate(evidence_descriptions, 1):
            evidence_items.append(EvidenceItem(
                evidence_id=str(i),
                evidence_type=EvidenceType.DOCUMENT,
                title=f"Evidence {i}",
                description=desc
            ))

        request = EvidenceAnalysisRequest(
            case_id=case_id,
            evidence_items=evidence_items,
            case_context=case_context,
            analysis_purpose="custody"
        )

        result = await self.analyze_evidence(request)

        return {
            "total_items": result.total_items,
            "critical_items": result.critical_items,
            "evidence_strength": result.evidence_strength,
            "executive_summary": result.executive_summary,
            "top_recommendations": result.recommendations[:3]
        }
