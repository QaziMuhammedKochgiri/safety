"""
AI-Powered Risk Analysis for Child Safety Cases
Uses Claude to analyze case narratives and predict risk levels.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging

from .client import ClaudeClient

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk severity levels."""
    MINIMAL = "minimal"  # 0-2
    LOW = "low"  # 2-4
    MODERATE = "moderate"  # 4-6
    HIGH = "high"  # 6-8
    CRITICAL = "critical"  # 8-10


class RiskCategory(str, Enum):
    """Categories of risk factors."""
    PHYSICAL_HARM = "physical_harm"
    EMOTIONAL_ABUSE = "emotional_abuse"
    NEGLECT = "neglect"
    PARENTAL_ALIENATION = "parental_alienation"
    SUBSTANCE_ABUSE = "substance_abuse"
    DOMESTIC_VIOLENCE = "domestic_violence"
    ABDUCTION_RISK = "abduction_risk"
    MENTAL_HEALTH = "mental_health"
    SUPERVISION = "supervision"
    STABILITY = "stability"


@dataclass
class RiskFactor:
    """Individual risk factor identified by AI."""
    category: RiskCategory
    description: str
    severity: float  # 0-10
    evidence: List[str]
    confidence: float  # 0-1


@dataclass
class RiskAnalysisResult:
    """Complete AI-powered risk analysis."""
    case_id: str
    overall_risk_score: float  # 0-10
    risk_level: RiskLevel
    confidence: float  # 0-1

    # Risk factors
    risk_factors: List[RiskFactor]
    top_concerns: List[str]

    # Protective factors
    protective_factors: List[str]
    strengths: List[str]

    # Recommendations
    immediate_actions: List[str]
    monitoring_recommendations: List[str]

    # AI metadata
    analysis_timestamp: datetime
    model_used: str
    tokens_used: Dict[str, int]

    # User-friendly summary
    parent_friendly_summary: str
    next_steps: List[str]


class RiskAnalyzer:
    """
    AI-powered risk analyzer using Claude.
    Designed for non-technical users (40+ women).
    """

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """Initialize risk analyzer."""
        self.client = claude_client or ClaudeClient()
        logger.info("Risk Analyzer initialized")

    async def analyze_case(
        self,
        case_id: str,
        case_description: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> RiskAnalysisResult:
        """
        Analyze a case and generate comprehensive risk assessment.

        Args:
            case_id: Unique case identifier
            case_description: Narrative description of the case
            additional_context: Optional additional information

        Returns:
            Complete risk analysis result
        """
        logger.info(f"Starting risk analysis for case {case_id}")

        # Build comprehensive prompt
        prompt = self._build_analysis_prompt(case_description, additional_context)

        # System prompt for Claude
        system_prompt = """You are a child safety risk analyst with expertise in family law.
Your goal is to help parents (especially women 40+) understand risks to their children's safety.

IMPORTANT:
- Use simple, clear language (avoid legal jargon)
- Be empathetic and supportive
- Focus on actionable steps
- Explain risks in plain terms
- Provide hope and next steps

VALID RISK CATEGORIES (use exactly these):
- physical_harm
- emotional_abuse
- neglect
- parental_alienation
- substance_abuse
- domestic_violence
- abduction_risk
- mental_health
- supervision
- stability

Format your response as JSON with these fields:
{
    "overall_risk_score": 0-10,
    "risk_level": "minimal|low|moderate|high|critical",
    "confidence": 0-1,
    "risk_factors": [
        {
            "category": "substance_abuse",
            "description": "simple explanation",
            "severity": 0-10,
            "evidence": ["evidence 1", "evidence 2"],
            "confidence": 0-1
        }
    ],
    "top_concerns": ["concern 1", "concern 2", "concern 3"],
    "protective_factors": ["strength 1", "strength 2"],
    "strengths": ["what's going well"],
    "immediate_actions": ["action 1", "action 2"],
    "monitoring_recommendations": ["what to watch"],
    "parent_friendly_summary": "2-3 sentences in simple language",
    "next_steps": ["step 1", "step 2", "step 3"]
}"""

        try:
            # Get Claude's analysis
            response = await self.client.send_message(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=system_prompt,
                temperature=0.3  # Lower temperature for consistent risk assessment
            )

            # Parse JSON response
            analysis_data = json.loads(response["content"])

            # Convert to RiskAnalysisResult
            result = self._parse_analysis_result(
                case_id=case_id,
                analysis_data=analysis_data,
                response_metadata=response
            )

            logger.info(
                f"Risk analysis complete for case {case_id}: "
                f"Risk level = {result.risk_level}, "
                f"Score = {result.overall_risk_score:.1f}"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            raise ValueError("Invalid AI response format")
        except Exception as e:
            logger.error(f"Risk analysis failed for case {case_id}: {e}")
            raise

    def _build_analysis_prompt(
        self,
        case_description: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build comprehensive analysis prompt."""
        prompt_parts = [
            "Analyze this child custody/safety case:\n",
            f"Case Description:\n{case_description}\n"
        ]

        if additional_context:
            prompt_parts.append("\nAdditional Information:")

            if "child_age" in additional_context:
                prompt_parts.append(f"Child's Age: {additional_context['child_age']}")

            if "custody_arrangement" in additional_context:
                prompt_parts.append(
                    f"Current Custody: {additional_context['custody_arrangement']}"
                )

            if "previous_incidents" in additional_context:
                prompt_parts.append(
                    f"Previous Incidents: {additional_context['previous_incidents']}"
                )

            if "evidence_available" in additional_context:
                prompt_parts.append(
                    f"Evidence: {additional_context['evidence_available']}"
                )

        prompt_parts.append("\nPlease provide a comprehensive risk analysis in JSON format.")

        return "\n".join(prompt_parts)

    def _parse_analysis_result(
        self,
        case_id: str,
        analysis_data: Dict[str, Any],
        response_metadata: Dict[str, Any]
    ) -> RiskAnalysisResult:
        """Parse Claude's JSON response into RiskAnalysisResult."""

        # Parse risk factors
        risk_factors = [
            RiskFactor(
                category=RiskCategory(rf["category"]),
                description=rf["description"],
                severity=rf["severity"],
                evidence=rf["evidence"],
                confidence=rf["confidence"]
            )
            for rf in analysis_data.get("risk_factors", [])
        ]

        return RiskAnalysisResult(
            case_id=case_id,
            overall_risk_score=analysis_data["overall_risk_score"],
            risk_level=RiskLevel(analysis_data["risk_level"]),
            confidence=analysis_data["confidence"],
            risk_factors=risk_factors,
            top_concerns=analysis_data.get("top_concerns", []),
            protective_factors=analysis_data.get("protective_factors", []),
            strengths=analysis_data.get("strengths", []),
            immediate_actions=analysis_data.get("immediate_actions", []),
            monitoring_recommendations=analysis_data.get("monitoring_recommendations", []),
            analysis_timestamp=datetime.now(),
            model_used=response_metadata["model"],
            tokens_used=response_metadata["usage"],
            parent_friendly_summary=analysis_data.get("parent_friendly_summary", ""),
            next_steps=analysis_data.get("next_steps", [])
        )

    async def quick_risk_check(self, situation: str) -> str:
        """
        Quick risk check for urgent situations.
        Returns simple yes/no + immediate action.

        Args:
            situation: Brief description of immediate concern

        Returns:
            Simple guidance in 2-3 sentences
        """
        prompt = f"""A parent is asking about this urgent situation:

"{situation}"

Is this a high-risk situation that needs immediate action?
Respond in 2-3 simple sentences with:
1. Yes/No + why
2. What to do right now

Use simple language for a worried parent."""

        response = await self.client.simple_prompt(
            prompt=prompt,
            temperature=0.1,  # Very consistent for safety
            max_tokens=200
        )

        return response
