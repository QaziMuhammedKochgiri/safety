"""
AI-Powered Case Summary Generator
Creates comprehensive case summaries for court from all available data.

Design: "Baş Yolla" one-click complete case package for court.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
import logging

from .client import ClaudeClient

logger = logging.getLogger(__name__)


@dataclass
class CaseSummaryRequest:
    """Request to generate case summary."""
    case_id: str

    # Core information
    petitioner_name: str
    respondent_name: str
    child_name: str
    child_age: int

    # Case details
    case_type: str  # "custody", "protection_order", "modification"
    case_description: str
    relief_requested: List[str]

    # Optional comprehensive data
    timeline_summary: Optional[str] = None
    evidence_summary: Optional[str] = None
    risk_analysis_summary: Optional[str] = None
    alienation_analysis_summary: Optional[str] = None

    # Additional context
    jurisdiction: Optional[str] = None
    previous_orders: Optional[List[str]] = None
    medical_concerns: Optional[List[str]] = None
    safety_concerns: Optional[List[str]] = None


@dataclass
class CaseSummaryResult:
    """Generated comprehensive case summary."""
    summary_id: str
    case_id: str

    # Executive summaries
    one_page_summary: str  # Court clerks, judges - quick overview
    detailed_summary: str  # Full case summary
    elevator_pitch: str  # 2-3 sentences for quick reference

    # Structured sections
    background: str
    key_facts: List[str]
    legal_issues: List[str]
    evidence_highlights: List[str]
    child_impact: str
    safety_concerns_summary: str

    # Legal arguments
    legal_basis: str
    supporting_precedents: List[str]
    relief_justification: str

    # Court documents
    proposed_findings_of_fact: List[str]
    proposed_conclusions_of_law: List[str]
    urgency_statement: Optional[str]

    # Communication tools
    talking_points: List[str]  # For court appearance
    questions_for_opposing_counsel: List[str]
    settlement_position: Optional[str]

    # Metadata
    generated_at: datetime
    model_used: str
    tokens_used: Dict[str, int]


class CaseSummaryGenerator:
    """
    AI-powered comprehensive case summary generator.
    Pulls together all case information for court presentation.
    """

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """Initialize case summary generator."""
        self.client = claude_client or ClaudeClient()
        logger.info("Case Summary Generator initialized")

    async def generate_summary(
        self,
        request: CaseSummaryRequest
    ) -> CaseSummaryResult:
        """
        Generate comprehensive case summary.

        Args:
            request: Case summary request

        Returns:
            Complete case summary package
        """
        logger.info(
            f"Generating case summary for {request.case_id}: "
            f"{request.petitioner_name} v. {request.respondent_name}"
        )

        # Build generation prompt
        prompt = self._build_generation_prompt(request)
        system_prompt = self._get_system_prompt(request)

        try:
            # Get Claude analysis
            response = await self.client.send_message(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=system_prompt,
                temperature=0.4,
                max_tokens=4096
            )

            # Parse response
            summary_data = json.loads(response["content"])

            # Create result
            result = CaseSummaryResult(
                summary_id=f"summary_{request.case_id}_{datetime.now().timestamp()}",
                case_id=request.case_id,
                one_page_summary=summary_data.get("one_page_summary", ""),
                detailed_summary=summary_data.get("detailed_summary", ""),
                elevator_pitch=summary_data.get("elevator_pitch", ""),
                background=summary_data.get("background", ""),
                key_facts=summary_data.get("key_facts", []),
                legal_issues=summary_data.get("legal_issues", []),
                evidence_highlights=summary_data.get("evidence_highlights", []),
                child_impact=summary_data.get("child_impact", ""),
                safety_concerns_summary=summary_data.get("safety_concerns_summary", ""),
                legal_basis=summary_data.get("legal_basis", ""),
                supporting_precedents=summary_data.get("supporting_precedents", []),
                relief_justification=summary_data.get("relief_justification", ""),
                proposed_findings_of_fact=summary_data.get("proposed_findings_of_fact", []),
                proposed_conclusions_of_law=summary_data.get("proposed_conclusions_of_law", []),
                urgency_statement=summary_data.get("urgency_statement"),
                talking_points=summary_data.get("talking_points", []),
                questions_for_opposing_counsel=summary_data.get("questions_for_opposing_counsel", []),
                settlement_position=summary_data.get("settlement_position"),
                generated_at=datetime.now(),
                model_used=response["model"],
                tokens_used=response["usage"]
            )

            logger.info(
                f"Case summary generated: {len(result.key_facts)} facts, "
                f"{len(result.legal_issues)} issues"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse case summary: {e}")
            raise ValueError("Invalid AI summary format")
        except Exception as e:
            logger.error(f"Case summary generation failed: {e}")
            raise

    def _build_generation_prompt(self, request: CaseSummaryRequest) -> str:
        """Build case summary generation prompt."""
        prompt_parts = [
            f"Create comprehensive case summary for {request.case_type} case.",
            f"\n**CASE INFORMATION:**",
            f"- Case ID: {request.case_id}",
            f"- Petitioner: {request.petitioner_name}",
            f"- Respondent: {request.respondent_name}",
            f"- Child: {request.child_name}, Age {request.child_age}"
        ]

        if request.jurisdiction:
            prompt_parts.append(f"- Jurisdiction: {request.jurisdiction}")

        prompt_parts.extend([
            f"\n**CASE DESCRIPTION:**",
            request.case_description,
            f"\n**RELIEF REQUESTED:**"
        ])

        for i, relief in enumerate(request.relief_requested, 1):
            prompt_parts.append(f"{i}. {relief}")

        if request.timeline_summary:
            prompt_parts.extend([
                f"\n**TIMELINE ANALYSIS:**",
                request.timeline_summary
            ])

        if request.evidence_summary:
            prompt_parts.extend([
                f"\n**EVIDENCE SUMMARY:**",
                request.evidence_summary
            ])

        if request.risk_analysis_summary:
            prompt_parts.extend([
                f"\n**RISK ANALYSIS:**",
                request.risk_analysis_summary
            ])

        if request.alienation_analysis_summary:
            prompt_parts.extend([
                f"\n**PARENTAL ALIENATION ANALYSIS:**",
                request.alienation_analysis_summary
            ])

        if request.safety_concerns:
            prompt_parts.append(f"\n**SAFETY CONCERNS:**")
            for concern in request.safety_concerns:
                prompt_parts.append(f"- {concern}")

        if request.medical_concerns:
            prompt_parts.append(f"\n**MEDICAL CONCERNS:**")
            for concern in request.medical_concerns:
                prompt_parts.append(f"- {concern}")

        if request.previous_orders:
            prompt_parts.append(f"\n**PREVIOUS COURT ORDERS:**")
            for order in request.previous_orders:
                prompt_parts.append(f"- {order}")

        prompt_parts.append(
            "\nGenerate comprehensive case summary in JSON format as specified."
        )

        return "\n".join(prompt_parts)

    def _get_system_prompt(self, request: CaseSummaryRequest) -> str:
        """Get system prompt for case summary generation."""

        return f"""You are an expert family law attorney preparing a comprehensive case summary for a {request.case_type} case.

CRITICAL REQUIREMENTS:
1. Be clear, concise, and persuasive
2. Focus on child's best interests
3. Present facts objectively
4. Build strong legal arguments
5. Anticipate opposing arguments
6. Maintain professional tone
7. Include actionable recommendations
8. Structure for court presentation

OUTPUT FORMAT (JSON):
{{
    "one_page_summary": "1-page executive summary for court clerk/judge",
    "detailed_summary": "Full case summary (3-5 pages worth)",
    "elevator_pitch": "2-3 sentence case summary",

    "background": "Case background and history",
    "key_facts": ["Fact 1", "Fact 2", "Fact 3"],
    "legal_issues": ["Issue 1", "Issue 2"],
    "evidence_highlights": ["Key evidence 1", "Key evidence 2"],
    "child_impact": "How this affects the child",
    "safety_concerns_summary": "Summary of safety concerns",

    "legal_basis": "Legal foundation for requested relief",
    "supporting_precedents": ["Relevant case law or statutes"],
    "relief_justification": "Why requested relief is appropriate",

    "proposed_findings_of_fact": ["Finding 1", "Finding 2"],
    "proposed_conclusions_of_law": ["Conclusion 1", "Conclusion 2"],
    "urgency_statement": "Why this needs immediate attention (if urgent)",

    "talking_points": ["Point 1 for court", "Point 2 for court"],
    "questions_for_opposing_counsel": ["Question 1", "Question 2"],
    "settlement_position": "Potential settlement approach"
}}

TONE: Professional, empathetic, focused on child safety.
AUDIENCE: Judge, court clerk, opposing counsel, mediators.
PURPOSE: Provide complete case overview for informed decision-making.

IMPORTANT:
- Use jurisdiction-specific legal terminology
- Cite relevant laws and precedents
- Focus on child's best interests standard
- Address potential counterarguments
- Provide clear, actionable recommendations
- Maintain credibility and objectivity
"""

    async def quick_summary(
        self,
        case_description: str,
        petitioner: str,
        respondent: str,
        child_name: str,
        child_age: int
    ) -> str:
        """
        Quick case summary for initial consultation.

        Args:
            case_description: Brief case description
            petitioner: Petitioner name
            respondent: Respondent name
            child_name: Child's name
            child_age: Child's age

        Returns:
            Elevator pitch summary
        """
        request = CaseSummaryRequest(
            case_id=f"quick_{datetime.now().timestamp()}",
            petitioner_name=petitioner,
            respondent_name=respondent,
            child_name=child_name,
            child_age=child_age,
            case_type="custody",
            case_description=case_description,
            relief_requested=["Appropriate custody arrangement"]
        )

        result = await self.generate_summary(request)
        return result.elevator_pitch
