"""
Advanced AI Module for SafeChild

Provides:
- Self-hosted LLM integration (Ollama + Claude fallback)
- Enhanced risk detection
- Parental alienation detection
- Court-ready summary generation
"""

import logging
import os
import json
import httpx
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RiskCategory(Enum):
    """Risk categories for child safety"""
    THREATS = "threats"
    MANIPULATION = "manipulation"
    ALIENATION = "alienation"
    EMOTIONAL_ABUSE = "emotional_abuse"
    COERCION = "coercion"
    NEGLECT = "neglect"
    VIOLENCE = "violence"
    INAPPROPRIATE_CONTENT = "inappropriate_content"


class AlienationTactic(Enum):
    """Parental alienation tactics taxonomy"""
    BADMOUTHING = "badmouthing"              # Speaking negatively about other parent
    LIMITING_CONTACT = "limiting_contact"    # Restricting communication
    INTERFERENCE = "interference"            # Interfering with visits/calls
    ERASURE = "erasure"                      # Erasing other parent from child's life
    TRIANGULATION = "triangulation"          # Using child as messenger
    UNDERMINING = "undermining"              # Undermining other parent's authority
    GATEKEEPING = "gatekeeping"              # Controlling access to child
    LOYALTY_CONFLICT = "loyalty_conflict"    # Creating loyalty conflicts
    PARENTIFICATION = "parentification"      # Making child into confidant
    FALSE_ACCUSATIONS = "false_accusations"  # Making false abuse claims


@dataclass
class RiskIndicator:
    """Individual risk indicator with evidence"""
    category: RiskCategory
    severity: int  # 1-10
    description: str
    evidence_text: str
    timestamp: Optional[datetime] = None
    source_file: Optional[str] = None
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity,
            "description": self.description,
            "evidenceText": self.evidence_text,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "sourceFile": self.source_file,
            "confidence": self.confidence
        }


@dataclass
class AlienationEvidence:
    """Evidence of parental alienation"""
    tactic: AlienationTactic
    severity: int  # 1-10
    description: str
    evidence_text: str
    pattern_frequency: int  # How often this pattern appears
    literature_reference: Optional[str] = None
    expert_opinion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tactic": self.tactic.value,
            "severity": self.severity,
            "description": self.description,
            "evidenceText": self.evidence_text,
            "patternFrequency": self.pattern_frequency,
            "literatureReference": self.literature_reference,
            "expertOpinion": self.expert_opinion
        }


@dataclass
class RiskAssessment:
    """Complete risk assessment result"""
    case_id: str
    overall_risk_level: str  # "low", "medium", "high", "critical"
    overall_score: int  # 1-100
    indicators: List[RiskIndicator] = field(default_factory=list)
    alienation_evidence: List[AlienationEvidence] = field(default_factory=list)
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "caseId": self.case_id,
            "overallRiskLevel": self.overall_risk_level,
            "overallScore": self.overall_score,
            "indicators": [i.to_dict() for i in self.indicators],
            "alienationEvidence": [e.to_dict() for e in self.alienation_evidence],
            "summary": self.summary,
            "recommendations": self.recommendations,
            "createdAt": self.created_at.isoformat()
        }


class OllamaClient:
    """
    Client for Ollama self-hosted LLM.
    Provides local inference with Llama/Mistral models.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama2"
    ):
        self.base_url = base_url
        self.model = model
        self._available = False
        self._check_availability()

    def _check_availability(self):
        """Check if Ollama is running"""
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self._available = True
                models = response.json().get("models", [])
                logger.info(f"Ollama available with models: {[m['name'] for m in models]}")
            else:
                self._available = False
        except Exception as e:
            logger.info(f"Ollama not available: {e}")
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate text using Ollama"""
        if not self._available:
            raise RuntimeError("Ollama not available")

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }

                if system:
                    payload["system"] = system

                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )

                if response.status_code == 200:
                    return response.json().get("response", "")
                else:
                    logger.error(f"Ollama error: {response.text}")
                    return ""

        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return ""


class ClaudeClient:
    """
    Claude API client (fallback when funded).
    Uses Anthropic API.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._available = bool(self.api_key)

    @property
    def is_available(self) -> bool:
        return self._available

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 1000
    ) -> str:
        """Generate text using Claude API"""
        if not self._available:
            raise RuntimeError("Claude API not configured")

        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=self.api_key)

            messages = [{"role": "user", "content": prompt}]

            response = await client.messages.create(
                model="claude-3-haiku-20240307",  # Use cheapest model
                max_tokens=max_tokens,
                system=system or "",
                messages=messages
            )

            return response.content[0].text

        except ImportError:
            logger.error("anthropic library not installed")
            return ""
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return ""


class LLMRouter:
    """
    Routes LLM requests to available providers.
    Priority: Ollama (free) -> Claude (paid fallback)
    """

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        ollama_model: str = "llama2"
    ):
        self.ollama = OllamaClient(ollama_url, ollama_model)
        self.claude = ClaudeClient()

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Tuple[str, str]:
        """
        Generate text using available LLM.

        Returns:
            Tuple of (response_text, provider_used)
        """
        # Try Ollama first (free)
        if self.ollama.is_available:
            try:
                response = await self.ollama.generate(
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                if response:
                    return response, "ollama"
            except Exception as e:
                logger.warning(f"Ollama failed, trying Claude: {e}")

        # Fallback to Claude (paid)
        if self.claude.is_available:
            try:
                response = await self.claude.generate(
                    prompt=prompt,
                    system=system,
                    max_tokens=max_tokens
                )
                if response:
                    return response, "claude"
            except Exception as e:
                logger.error(f"Claude also failed: {e}")

        return "", "none"


class RiskDetector:
    """
    Enhanced risk detection using pattern matching and LLM analysis.
    """

    # Risk keywords with severity (Turkish + English)
    RISK_PATTERNS = {
        RiskCategory.THREATS: {
            "keywords": [
                ("öldüreceğim", 10), ("kill", 10), ("harm", 8),
                ("vuracağım", 8), ("döveceğim", 7), ("hurt", 7),
                ("seni mahvedeceğim", 9), ("destroy", 8)
            ],
            "patterns": [
                r"seni (öldür|döv|vur)",
                r"(kill|hurt|harm) you",
                r"pişman (olacak|edece)"
            ]
        },
        RiskCategory.MANIPULATION: {
            "keywords": [
                ("seni seviyor muyum biliyor musun", 6),
                ("beni sevmezsen", 7),
                ("if you don't love me", 7),
                ("baban/annen seni sevmiyor", 8),
                ("doesn't love you", 8)
            ],
            "patterns": [
                r"(anne|baba)n seni (sevmiyor|istemiyor)",
                r"(mom|dad) doesn't (love|want)"
            ]
        },
        RiskCategory.ALIENATION: {
            "keywords": [
                ("onlara gitme", 7), ("onları arama", 7),
                ("don't visit", 7), ("don't call", 6),
                ("seninle olmak istemiyorlar", 8),
                ("onları unutmalısın", 9)
            ],
            "patterns": [
                r"(anne|baba)n?ı (görme|arama|gitme)",
                r"don't (see|call|visit) (mom|dad)"
            ]
        },
        RiskCategory.EMOTIONAL_ABUSE: {
            "keywords": [
                ("aptal", 5), ("salak", 5), ("stupid", 5),
                ("işe yaramaz", 6), ("worthless", 7),
                ("keşke olmasaydın", 9), ("wish you weren't born", 10),
                ("seni istemiyorum", 8)
            ],
            "patterns": [
                r"(aptal|salak|geri zekalı)",
                r"(stupid|idiot|worthless)"
            ]
        },
        RiskCategory.COERCION: {
            "keywords": [
                ("kimseye söyleme", 7), ("don't tell", 7),
                ("aramızda kalsın", 8), ("our secret", 8),
                ("söylersen", 6), ("if you tell", 6),
                ("cezalandırırım", 8)
            ],
            "patterns": [
                r"(söyler|anlatır)san",
                r"if you (tell|say)"
            ]
        }
    }

    # Parental alienation patterns
    ALIENATION_PATTERNS = {
        AlienationTactic.BADMOUTHING: [
            ("baban/annen kötü", "kötüleme"),
            ("your dad/mom is bad", "badmouthing"),
            ("seni hiç sevmedi", "never loved you"),
            ("her şey onun suçu", "it's all their fault")
        ],
        AlienationTactic.LIMITING_CONTACT: [
            ("bugün arayamazsın", "can't call today"),
            ("görüşemezsin", "can't see"),
            ("telefon yok", "no phone"),
            ("mesaj atma", "don't text")
        ],
        AlienationTactic.LOYALTY_CONFLICT: [
            ("beni mi onu mu seviyorsun", "who do you love more"),
            ("kimi tercih edersin", "who do you choose"),
            ("bizi seçmelisin", "you must choose us")
        ],
        AlienationTactic.TRIANGULATION: [
            ("babana/annene söyle", "tell your dad/mom"),
            ("ona sor", "ask them"),
            ("ona mesaj at", "message them")
        ]
    }

    def __init__(self):
        import re
        self._re = re
        self._compiled_patterns = self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns"""
        compiled = {}
        for category, data in self.RISK_PATTERNS.items():
            compiled[category] = [
                self._re.compile(p, self._re.IGNORECASE)
                for p in data.get("patterns", [])
            ]
        return compiled

    def detect_risks(
        self,
        text: str,
        source_file: Optional[str] = None
    ) -> List[RiskIndicator]:
        """Detect risk indicators in text"""
        indicators = []
        text_lower = text.lower()

        for category, data in self.RISK_PATTERNS.items():
            # Check keywords
            for keyword, severity in data["keywords"]:
                if keyword.lower() in text_lower:
                    indicators.append(RiskIndicator(
                        category=category,
                        severity=severity,
                        description=f"Found risk keyword: {keyword}",
                        evidence_text=self._extract_context(text, keyword),
                        source_file=source_file,
                        confidence=0.9
                    ))

            # Check patterns
            for pattern in self._compiled_patterns.get(category, []):
                matches = pattern.findall(text)
                if matches:
                    for match in matches:
                        indicators.append(RiskIndicator(
                            category=category,
                            severity=7,
                            description=f"Found risk pattern match",
                            evidence_text=match if isinstance(match, str) else match[0],
                            source_file=source_file,
                            confidence=0.85
                        ))

        return indicators

    def detect_alienation(
        self,
        text: str,
        source_file: Optional[str] = None
    ) -> List[AlienationEvidence]:
        """Detect parental alienation patterns"""
        evidence = []
        text_lower = text.lower()

        for tactic, patterns in self.ALIENATION_PATTERNS.items():
            for pattern_tr, pattern_en in patterns:
                if pattern_tr.lower() in text_lower or pattern_en.lower() in text_lower:
                    evidence.append(AlienationEvidence(
                        tactic=tactic,
                        severity=7,
                        description=f"Detected {tactic.value} pattern",
                        evidence_text=self._extract_context(text, pattern_tr),
                        pattern_frequency=1,
                        literature_reference="Gardner (1985) - Parental Alienation Syndrome"
                    ))

        return evidence

    def _extract_context(self, text: str, keyword: str, context_chars: int = 100) -> str:
        """Extract context around a keyword"""
        text_lower = text.lower()
        keyword_lower = keyword.lower()

        idx = text_lower.find(keyword_lower)
        if idx == -1:
            return keyword

        start = max(0, idx - context_chars)
        end = min(len(text), idx + len(keyword) + context_chars)

        return "..." + text[start:end] + "..."


class CourtReportGenerator:
    """
    Generate court-ready reports and summaries.
    """

    REPORT_TEMPLATE = """
# DIGITAL EVIDENCE FORENSIC REPORT

## Case Information
- **Case ID:** {case_id}
- **Report Date:** {report_date}
- **Analysis Period:** {analysis_period}

## Executive Summary
{executive_summary}

## Risk Assessment
- **Overall Risk Level:** {risk_level}
- **Risk Score:** {risk_score}/100

## Key Findings

### Risk Indicators ({indicator_count})
{risk_indicators}

### Parental Alienation Evidence ({alienation_count})
{alienation_evidence}

## Recommendations
{recommendations}

## Evidence Appendix
{evidence_appendix}

---
*This report was generated using SafeChild Digital Forensics Platform*
*For court use - Chain of custody maintained*
"""

    def generate_report(
        self,
        assessment: RiskAssessment,
        include_evidence: bool = True
    ) -> str:
        """Generate formatted court report"""

        # Format risk indicators
        indicators_text = ""
        for i, ind in enumerate(assessment.indicators, 1):
            indicators_text += f"""
{i}. **{ind.category.value.upper()}** (Severity: {ind.severity}/10)
   - {ind.description}
   - Evidence: "{ind.evidence_text[:200]}..."
   - Confidence: {ind.confidence:.0%}
"""

        # Format alienation evidence
        alienation_text = ""
        for i, ev in enumerate(assessment.alienation_evidence, 1):
            alienation_text += f"""
{i}. **{ev.tactic.value.upper()}** (Severity: {ev.severity}/10)
   - {ev.description}
   - Evidence: "{ev.evidence_text[:200]}..."
   - Literature: {ev.literature_reference or 'N/A'}
"""

        # Format recommendations
        recommendations_text = "\n".join(
            f"- {rec}" for rec in assessment.recommendations
        )

        return self.REPORT_TEMPLATE.format(
            case_id=assessment.case_id,
            report_date=datetime.now().strftime("%Y-%m-%d"),
            analysis_period="[Analysis Period]",
            executive_summary=assessment.summary,
            risk_level=assessment.overall_risk_level.upper(),
            risk_score=assessment.overall_score,
            indicator_count=len(assessment.indicators),
            risk_indicators=indicators_text or "No risk indicators detected.",
            alienation_count=len(assessment.alienation_evidence),
            alienation_evidence=alienation_text or "No alienation evidence detected.",
            recommendations=recommendations_text or "No specific recommendations.",
            evidence_appendix="[Detailed evidence attached separately]"
        )


class AdvancedAIEngine:
    """
    Main Advanced AI engine combining all components.
    """

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        ollama_model: str = "llama2"
    ):
        self.llm = LLMRouter(ollama_url, ollama_model)
        self.risk_detector = RiskDetector()
        self.report_generator = CourtReportGenerator()

    async def analyze_text(
        self,
        text: str,
        case_id: str,
        source_file: Optional[str] = None,
        use_llm: bool = True
    ) -> RiskAssessment:
        """
        Perform complete AI analysis on text.

        Args:
            text: Text to analyze
            case_id: Associated case ID
            source_file: Source file name
            use_llm: Whether to use LLM for enhanced analysis

        Returns:
            RiskAssessment with findings
        """
        # Detect risks using pattern matching
        indicators = self.risk_detector.detect_risks(text, source_file)

        # Detect alienation patterns
        alienation_evidence = self.risk_detector.detect_alienation(text, source_file)

        # Calculate overall score
        overall_score = self._calculate_overall_score(indicators, alienation_evidence)

        # Determine risk level
        if overall_score >= 80:
            risk_level = "critical"
        elif overall_score >= 60:
            risk_level = "high"
        elif overall_score >= 40:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Generate summary using LLM if available
        summary = ""
        if use_llm and (indicators or alienation_evidence):
            summary = await self._generate_summary(indicators, alienation_evidence)

        # Generate recommendations
        recommendations = self._generate_recommendations(indicators, alienation_evidence)

        return RiskAssessment(
            case_id=case_id,
            overall_risk_level=risk_level,
            overall_score=overall_score,
            indicators=indicators,
            alienation_evidence=alienation_evidence,
            summary=summary,
            recommendations=recommendations
        )

    def _calculate_overall_score(
        self,
        indicators: List[RiskIndicator],
        alienation: List[AlienationEvidence]
    ) -> int:
        """Calculate overall risk score (0-100)"""
        if not indicators and not alienation:
            return 0

        # Weight indicators
        indicator_score = sum(i.severity * i.confidence for i in indicators)
        max_indicator = len(indicators) * 10 if indicators else 1

        # Weight alienation
        alienation_score = sum(e.severity for e in alienation)
        max_alienation = len(alienation) * 10 if alienation else 1

        # Combine (70% indicators, 30% alienation)
        combined = (
            0.7 * (indicator_score / max_indicator * 100) +
            0.3 * (alienation_score / max_alienation * 100)
        )

        return min(100, int(combined))

    async def _generate_summary(
        self,
        indicators: List[RiskIndicator],
        alienation: List[AlienationEvidence]
    ) -> str:
        """Generate AI summary of findings"""
        # Build prompt
        findings = []
        for ind in indicators[:5]:  # Top 5
            findings.append(f"- {ind.category.value}: {ind.description}")
        for ev in alienation[:5]:  # Top 5
            findings.append(f"- Alienation ({ev.tactic.value}): {ev.description}")

        prompt = f"""Analyze these child safety risk findings and provide a brief professional summary:

Findings:
{chr(10).join(findings)}

Write a 2-3 sentence executive summary suitable for a court report. Be objective and factual."""

        system = "You are a forensic analyst specializing in child safety. Provide objective, professional analysis."

        response, _ = await self.llm.generate(prompt, system, max_tokens=200)
        return response.strip() if response else "Analysis pending LLM availability."

    def _generate_recommendations(
        self,
        indicators: List[RiskIndicator],
        alienation: List[AlienationEvidence]
    ) -> List[str]:
        """Generate recommendations based on findings"""
        recommendations = []

        # Check for critical risks
        critical_categories = {
            i.category for i in indicators if i.severity >= 8
        }

        if RiskCategory.THREATS in critical_categories:
            recommendations.append("Immediate safety assessment recommended")
            recommendations.append("Consider supervised visitation pending investigation")

        if RiskCategory.ALIENATION in critical_categories or alienation:
            recommendations.append("Family therapy with alienation-aware therapist recommended")
            recommendations.append("Parent education program may be beneficial")

        if RiskCategory.EMOTIONAL_ABUSE in critical_categories:
            recommendations.append("Child psychological evaluation recommended")
            recommendations.append("Parenting capacity assessment may be warranted")

        if len(indicators) >= 5:
            recommendations.append("Comprehensive forensic analysis of all communications")

        if not recommendations:
            recommendations.append("Continue monitoring")
            recommendations.append("Maintain documentation of concerns")

        return recommendations

    def generate_court_report(
        self,
        assessment: RiskAssessment
    ) -> str:
        """Generate formatted court report"""
        return self.report_generator.generate_report(assessment)


# Export convenience function
async def analyze_for_risks(
    text: str,
    case_id: str,
    source_file: Optional[str] = None
) -> RiskAssessment:
    """
    Convenience function to analyze text for risks.

    Usage:
        assessment = await analyze_for_risks(message_text, case_id)
    """
    engine = AdvancedAIEngine()
    return await engine.analyze_text(text, case_id, source_file)
