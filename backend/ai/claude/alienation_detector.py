"""
AI-Powered Parental Alienation Detector
Detects and analyzes parental alienation patterns using Claude AI.

Design: Helps mothers document alienation tactics for court evidence.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging

from .client import ClaudeClient

logger = logging.getLogger(__name__)


class AlienationSeverity(str, Enum):
    """Severity levels of parental alienation."""
    NONE = "none"  # No signs detected
    MILD = "mild"  # Early warning signs
    MODERATE = "moderate"  # Clear alienation patterns
    SEVERE = "severe"  # Advanced alienation
    CRITICAL = "critical"  # Complete alienation/rejection


class AlienationTactic(str, Enum):
    """Common parental alienation tactics."""
    BADMOUTHING = "badmouthing"  # Negative talk about other parent
    LIMITING_CONTACT = "limiting_contact"  # Restricting communication
    CREATING_CONFLICT = "creating_conflict"  # Forcing child to choose
    FALSE_ALLEGATIONS = "false_allegations"  # Making untrue accusations
    INTERFERING_VISITATION = "interfering_visitation"  # Blocking visits
    EMOTIONAL_MANIPULATION = "emotional_manipulation"  # Guilt, fear tactics
    ERASING_PARENT = "erasing_parent"  # Removing from child's life
    WITHHOLDING_INFO = "withholding_info"  # Not sharing important info
    REWARDING_REJECTION = "rewarding_rejection"  # Praising child for rejecting parent
    UNDERMINING_AUTHORITY = "undermining_authority"  # Disrespecting parent's rules


@dataclass
class AlienationEvidence:
    """Evidence item for parental alienation."""
    evidence_type: str  # "message", "behavior", "statement", "incident"
    description: str
    date: Optional[str] = None
    source: Optional[str] = None  # "child", "other_parent", "witness"
    severity_contribution: float = 0.0  # 0-1


@dataclass
class AlienationAnalysisRequest:
    """Request for parental alienation analysis."""
    case_id: str
    child_name: str
    child_age: int
    alienating_parent: str  # Name of suspected alienating parent
    targeted_parent: str  # Name of alienated parent

    # Case information
    case_description: str
    evidence_items: List[AlienationEvidence]

    # Context
    custody_arrangement: Optional[str] = None
    relationship_history: Optional[str] = None
    child_statements: Optional[List[str]] = None
    behavioral_changes: Optional[List[str]] = None


@dataclass
class DetectedTactic:
    """Detected alienation tactic."""
    tactic: AlienationTactic
    description: str
    evidence_references: List[str]
    severity: float  # 0-1
    court_relevance: str  # Why this matters legally


@dataclass
class AlienationAnalysisResult:
    """AI analysis result for parental alienation."""
    analysis_id: str
    case_id: str

    # Overall assessment
    severity: AlienationSeverity
    severity_score: float  # 0-10
    confidence: float  # 0-1

    # Detected patterns
    detected_tactics: List[DetectedTactic]
    primary_concerns: List[str]
    behavioral_indicators: List[str]

    # Impact assessment
    child_impact_assessment: str  # How child is affected
    long_term_risks: List[str]

    # Recommendations
    immediate_actions: List[str]
    documentation_suggestions: List[str]
    court_presentation_tips: List[str]

    # Court documentation
    executive_summary: str  # For court filing
    evidence_summary: str  # List of evidence
    expert_opinion: str  # AI assessment for court

    # Metadata
    analyzed_at: datetime
    model_used: str
    tokens_used: Dict[str, int]


class AlienationDetector:
    """
    AI-powered parental alienation detector.
    Analyzes patterns and provides court-ready documentation.
    """

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """Initialize alienation detector."""
        self.client = claude_client or ClaudeClient()
        logger.info("Parental Alienation Detector initialized")

    async def analyze_case(
        self,
        request: AlienationAnalysisRequest
    ) -> AlienationAnalysisResult:
        """
        Analyze a case for parental alienation patterns.

        Args:
            request: Analysis request with case details

        Returns:
            Comprehensive alienation analysis
        """
        logger.info(
            f"Analyzing case {request.case_id} for parental alienation: "
            f"{request.child_name}, age {request.child_age}"
        )

        # Build analysis prompt
        prompt = self._build_analysis_prompt(request)
        system_prompt = self._get_system_prompt()

        try:
            # Get Claude analysis
            response = await self.client.send_message(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=system_prompt,
                temperature=0.3,  # Lower for accuracy
                max_tokens=4096
            )

            # Parse response
            analysis_data = json.loads(response["content"])

            # Validate severity
            try:
                severity_enum = AlienationSeverity(analysis_data["severity"])
            except (ValueError, KeyError):
                severity_enum = AlienationSeverity.MODERATE
                logger.warning(f"Invalid severity, defaulting to MODERATE")

            # Parse detected tactics
            detected_tactics = []
            for tactic_data in analysis_data.get("detected_tactics", []):
                try:
                    tactic_enum = AlienationTactic(tactic_data["tactic"])
                    detected_tactics.append(DetectedTactic(
                        tactic=tactic_enum,
                        description=tactic_data["description"],
                        evidence_references=tactic_data.get("evidence_references", []),
                        severity=tactic_data.get("severity", 0.5),
                        court_relevance=tactic_data.get("court_relevance", "")
                    ))
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid tactic: {e}")
                    continue

            # Create result
            result = AlienationAnalysisResult(
                analysis_id=f"alienation_{request.case_id}_{datetime.now().timestamp()}",
                case_id=request.case_id,
                severity=severity_enum,
                severity_score=analysis_data.get("severity_score", 5.0),
                confidence=analysis_data.get("confidence", 0.8),
                detected_tactics=detected_tactics,
                primary_concerns=analysis_data.get("primary_concerns", []),
                behavioral_indicators=analysis_data.get("behavioral_indicators", []),
                child_impact_assessment=analysis_data.get("child_impact_assessment", ""),
                long_term_risks=analysis_data.get("long_term_risks", []),
                immediate_actions=analysis_data.get("immediate_actions", []),
                documentation_suggestions=analysis_data.get("documentation_suggestions", []),
                court_presentation_tips=analysis_data.get("court_presentation_tips", []),
                executive_summary=analysis_data.get("executive_summary", ""),
                evidence_summary=analysis_data.get("evidence_summary", ""),
                expert_opinion=analysis_data.get("expert_opinion", ""),
                analyzed_at=datetime.now(),
                model_used=response["model"],
                tokens_used=response["usage"]
            )

            logger.info(
                f"Alienation analysis complete: {result.severity.value} "
                f"(score {result.severity_score:.1f}/10), "
                f"{len(result.detected_tactics)} tactics detected"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse alienation analysis: {e}")
            raise ValueError("Invalid AI analysis format")
        except Exception as e:
            logger.error(f"Alienation analysis failed: {e}")
            raise

    def _build_analysis_prompt(self, request: AlienationAnalysisRequest) -> str:
        """Build comprehensive analysis prompt."""
        prompt_parts = [
            f"Analyze this custody case for parental alienation patterns.",
            f"\n**CASE INFORMATION:**",
            f"- Case ID: {request.case_id}",
            f"- Child: {request.child_name}, Age {request.child_age}",
            f"- Suspected Alienating Parent: {request.alienating_parent}",
            f"- Targeted Parent: {request.targeted_parent}",
        ]

        if request.custody_arrangement:
            prompt_parts.append(f"- Current Custody: {request.custody_arrangement}")

        prompt_parts.extend([
            f"\n**CASE DESCRIPTION:**",
            request.case_description
        ])

        if request.relationship_history:
            prompt_parts.extend([
                f"\n**RELATIONSHIP HISTORY:**",
                request.relationship_history
            ])

        if request.evidence_items:
            prompt_parts.append(f"\n**EVIDENCE OF ALIENATION:**")
            for i, evidence in enumerate(request.evidence_items[:20], 1):
                date_str = f" ({evidence.date})" if evidence.date else ""
                source_str = f" [Source: {evidence.source}]" if evidence.source else ""
                prompt_parts.append(
                    f"{i}. {evidence.evidence_type.upper()}{date_str}{source_str}: "
                    f"{evidence.description}"
                )

        if request.child_statements:
            prompt_parts.append(f"\n**CHILD'S STATEMENTS:**")
            for i, statement in enumerate(request.child_statements, 1):
                prompt_parts.append(f"{i}. \"{statement}\"")

        if request.behavioral_changes:
            prompt_parts.append(f"\n**BEHAVIORAL CHANGES IN CHILD:**")
            for i, change in enumerate(request.behavioral_changes, 1):
                prompt_parts.append(f"{i}. {change}")

        prompt_parts.append(
            "\nProvide comprehensive parental alienation analysis in JSON format as specified."
        )

        return "\n".join(prompt_parts)

    def _get_system_prompt(self) -> str:
        """Get system prompt for alienation analysis."""

        return """You are an expert child psychologist and family law consultant specializing in parental alienation.

PARENTAL ALIENATION OVERVIEW:
Parental alienation is when one parent manipulates a child to reject or fear the other parent without legitimate justification. It's a form of emotional abuse that can cause severe psychological harm to children.

COMMON ALIENATION TACTICS (use exactly these):
- badmouthing: Repeatedly criticizing or demeaning the other parent
- limiting_contact: Restricting phone calls, visits, or communication
- creating_conflict: Forcing child to choose sides or choose loyalty
- false_allegations: Making untrue accusations of abuse or neglect
- interfering_visitation: Finding excuses to cancel or shorten visits
- emotional_manipulation: Using guilt, fear, or emotional blackmail
- erasing_parent: Removing photos, gifts, or mentions of other parent
- withholding_info: Not sharing school, medical, or important updates
- rewarding_rejection: Praising child for refusing to see other parent
- undermining_authority: Disrespecting or invalidating parent's rules

SEVERITY LEVELS (use exactly these):
- none: No alienation detected
- mild: Early warning signs, preventable
- moderate: Clear pattern established, intervention needed
- severe: Advanced alienation, therapeutic intervention required
- critical: Complete rejection, emergency intervention needed

CRITICAL ANALYSIS REQUIREMENTS:
1. Be objective - analyze evidence, not assumptions
2. Consider child's age and developmental stage
3. Distinguish alienation from legitimate estrangement (real abuse)
4. Cite specific evidence for each conclusion
5. Assess impact on child's psychological wellbeing
6. Provide court-admissible language
7. Recommend evidence-based interventions

OUTPUT FORMAT (JSON):
{
    "severity": "none|mild|moderate|severe|critical",
    "severity_score": 0.0-10.0,
    "confidence": 0.0-1.0,
    "detected_tactics": [
        {
            "tactic": "badmouthing|limiting_contact|creating_conflict|false_allegations|interfering_visitation|emotional_manipulation|erasing_parent|withholding_info|rewarding_rejection|undermining_authority",
            "description": "Specific description of this tactic in this case",
            "evidence_references": ["Evidence item 1", "Evidence item 2"],
            "severity": 0.0-1.0,
            "court_relevance": "Why this matters legally"
        }
    ],
    "primary_concerns": ["Concern 1", "Concern 2", "Concern 3"],
    "behavioral_indicators": ["Indicator 1", "Indicator 2"],
    "child_impact_assessment": "Detailed assessment of psychological impact on child",
    "long_term_risks": ["Risk 1", "Risk 2", "Risk 3"],
    "immediate_actions": ["Action 1", "Action 2", "Action 3"],
    "documentation_suggestions": ["What to document 1", "What to document 2"],
    "court_presentation_tips": ["Tip 1", "Tip 2", "Tip 3"],
    "executive_summary": "2-3 paragraph summary suitable for court filing",
    "evidence_summary": "Organized list of key evidence items",
    "expert_opinion": "Professional opinion statement for court use"
}

IMPORTANT:
- Use empathetic, supportive language
- Focus on child's best interests
- Provide actionable recommendations
- Consider cultural context
- Be sensitive to trauma
- Use gender-neutral language when possible
- Avoid victim-blaming
- Emphasize reunification and healing when appropriate
"""

    async def quick_analysis(
        self,
        case_description: str,
        child_name: str,
        child_age: int,
        alienating_parent: str,
        targeted_parent: str
    ) -> AlienationAnalysisResult:
        """
        Quick alienation analysis with minimal inputs.
        Perfect for initial screening.

        Args:
            case_description: Brief description of situation
            child_name: Child's name
            child_age: Child's age
            alienating_parent: Suspected alienating parent name
            targeted_parent: Targeted parent name

        Returns:
            Alienation analysis result
        """
        request = AlienationAnalysisRequest(
            case_id=f"quick_{datetime.now().timestamp()}",
            child_name=child_name,
            child_age=child_age,
            alienating_parent=alienating_parent,
            targeted_parent=targeted_parent,
            case_description=case_description,
            evidence_items=[]
        )

        return await self.analyze_case(request)
