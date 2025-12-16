"""
AI-Powered Petition & Court Document Generator
Automatically generates court petitions using Claude AI.

Design: One-click ("Baş Yolla") document generation for 40+ women.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging

from .client import ClaudeClient

logger = logging.getLogger(__name__)


class PetitionType(str, Enum):
    """Types of court petitions."""
    CUSTODY = "custody"  # Child custody petition
    PROTECTION_ORDER = "protection_order"  # Protection/restraining order
    VISITATION_MODIFICATION = "visitation_modification"  # Modify visitation rights
    CHILD_SUPPORT = "child_support"  # Child support petition
    EMERGENCY_CUSTODY = "emergency_custody"  # Emergency custody
    EVIDENCE_SUMMARY = "evidence_summary"  # Evidence summary report


class CourtJurisdiction(str, Enum):
    """Court jurisdictions."""
    GERMANY = "germany"
    TURKEY = "turkey"
    EU = "eu"
    US = "us"
    UK = "uk"


@dataclass
class PetitionRequest:
    """Request to generate a court petition."""
    petition_type: PetitionType
    case_id: str
    jurisdiction: CourtJurisdiction
    language: str  # "en", "de", "tr", etc.

    # Case information
    petitioner_name: str
    respondent_name: str
    child_name: str
    child_age: int

    # Case details
    case_description: str
    key_incidents: List[str]
    evidence_items: List[Dict[str, Any]]

    # Request details
    relief_requested: List[str]  # What they're asking for
    urgency_level: str = "normal"  # "normal", "urgent", "emergency"

    # Optional
    court_name: Optional[str] = None
    case_number: Optional[str] = None
    attorney_name: Optional[str] = None
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedPetition:
    """AI-generated petition."""
    petition_id: str
    petition_type: PetitionType
    jurisdiction: CourtJurisdiction
    language: str

    # Generated content
    title: str
    introduction: str
    statement_of_facts: str
    legal_arguments: str
    relief_requested_section: str
    conclusion: str
    full_document: str

    # Metadata
    word_count: int
    estimated_pages: int
    key_legal_points: List[str]
    supporting_evidence_refs: List[str]

    # AI metadata
    generated_at: datetime
    model_used: str
    confidence: float
    tokens_used: Dict[str, int]


class PetitionGenerator:
    """
    AI-powered petition generator using Claude.
    Generates court-ready documents in multiple jurisdictions and languages.
    """

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """Initialize petition generator."""
        self.client = claude_client or ClaudeClient()
        logger.info("Petition Generator initialized")

    async def generate_petition(
        self,
        request: PetitionRequest
    ) -> GeneratedPetition:
        """
        Generate a complete court petition using AI.

        Args:
            request: Petition generation request

        Returns:
            Complete AI-generated petition
        """
        logger.info(
            f"Generating {request.petition_type} petition for "
            f"{request.jurisdiction} in {request.language}"
        )

        # Build prompt
        prompt = self._build_petition_prompt(request)
        system_prompt = self._get_system_prompt(request)

        try:
            # Generate with Claude
            response = await self.client.send_message(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=system_prompt,
                temperature=0.4,  # More consistent for legal documents
                max_tokens=4096
            )

            # Parse response
            petition_data = json.loads(response["content"])

            # Ensure key_legal_points and evidence_references are lists
            if "key_legal_points" not in petition_data:
                petition_data["key_legal_points"] = []
            if "evidence_references" not in petition_data:
                petition_data["evidence_references"] = []

            # Build full document
            full_document = self._compile_full_document(
                petition_data, request
            )

            # Create result
            result = GeneratedPetition(
                petition_id=f"petition_{request.case_id}_{datetime.now().timestamp()}",
                petition_type=request.petition_type,
                jurisdiction=request.jurisdiction,
                language=request.language,
                title=petition_data["title"],
                introduction=petition_data["introduction"],
                statement_of_facts=petition_data["statement_of_facts"],
                legal_arguments=petition_data["legal_arguments"],
                relief_requested_section=petition_data["relief_requested"],
                conclusion=petition_data["conclusion"],
                full_document=full_document,
                word_count=len(full_document.split()),
                estimated_pages=len(full_document) // 2500,
                key_legal_points=petition_data.get("key_legal_points", []),
                supporting_evidence_refs=petition_data.get("evidence_references", []),
                generated_at=datetime.now(),
                model_used=response["model"],
                confidence=petition_data.get("confidence", 0.85),
                tokens_used=response["usage"]
            )

            logger.info(
                f"Petition generated successfully: {result.word_count} words, "
                f"~{result.estimated_pages} pages"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            raise ValueError("Invalid AI response format")
        except Exception as e:
            logger.error(f"Petition generation failed: {e}")
            raise

    def _build_petition_prompt(self, request: PetitionRequest) -> str:
        """Build comprehensive prompt for petition generation."""
        prompt_parts = [
            f"Generate a {request.petition_type.value} petition for {request.jurisdiction.value} family court.",
            f"\n**CASE INFORMATION:**",
            f"- Petitioner: {request.petitioner_name}",
            f"- Respondent: {request.respondent_name}",
            f"- Child: {request.child_name}, Age {request.child_age}",
        ]

        if request.court_name:
            prompt_parts.append(f"- Court: {request.court_name}")
        if request.case_number:
            prompt_parts.append(f"- Case Number: {request.case_number}")

        prompt_parts.extend([
            f"\n**CASE DESCRIPTION:**",
            request.case_description,
            f"\n**KEY INCIDENTS:**"
        ])

        for i, incident in enumerate(request.key_incidents, 1):
            prompt_parts.append(f"{i}. {incident}")

        prompt_parts.extend([
            f"\n**RELIEF REQUESTED:**"
        ])

        for i, relief in enumerate(request.relief_requested, 1):
            prompt_parts.append(f"{i}. {relief}")

        if request.evidence_items:
            prompt_parts.append(f"\n**AVAILABLE EVIDENCE:**")
            for i, evidence in enumerate(request.evidence_items[:10], 1):
                evidence_type = evidence.get("type", "unknown")
                description = evidence.get("description", "")[:100]
                prompt_parts.append(f"{i}. {evidence_type}: {description}")

        if request.urgency_level in ["urgent", "emergency"]:
            prompt_parts.append(
                f"\n**URGENCY:** This is an {request.urgency_level} matter requiring immediate attention."
            )

        prompt_parts.append(
            "\nGenerate a complete, court-ready petition in JSON format as specified."
        )

        return "\n".join(prompt_parts)

    def _get_system_prompt(self, request: PetitionRequest) -> str:
        """Get jurisdiction and language-specific system prompt."""

        # Base legal instructions
        base_instructions = """You are an expert family law attorney specializing in child custody cases.

CRITICAL REQUIREMENTS:
1. Use clear, professional legal language
2. Be factual and objective - no exaggeration
3. Cite relevant laws and precedents for the jurisdiction
4. Focus on child's best interests
5. Structure arguments logically
6. Reference evidence properly
7. Be empathetic but professional"""

        # Jurisdiction-specific instructions
        jurisdiction_instructions = {
            CourtJurisdiction.GERMANY: """
GERMAN FAMILY LAW FOCUS:
- Cite BGB (Bürgerliches Gesetzbuch) sections
- Reference "Kindeswohl" (child's welfare) principle
- Follow German court petition format
- Use formal German legal terminology if language is DE
- Consider § 1666 BGB (child endangerment)
- Reference § 1684 BGB (visitation rights)""",

            CourtJurisdiction.TURKEY: """
TURKISH FAMILY LAW FOCUS:
- Cite Turkish Civil Code (TMK) articles
- Reference "Çocuğun Üstün Yararı" (child's best interest)
- Follow Turkish court petition format
- Use formal Turkish legal terminology if language is TR
- Consider TMK Article 182-190 (custody)
- Reference TMK Article 323-336 (parental authority)""",

            CourtJurisdiction.EU: """
EU FAMILY LAW FOCUS:
- Cite Brussels IIa Regulation
- Reference Hague Convention on Child Abduction
- Follow EU court petition format
- Consider cross-border jurisdiction issues
- Reference child's habitual residence""",

            CourtJurisdiction.US: """
US FAMILY LAW FOCUS:
- Cite relevant state statutes
- Reference Uniform Child Custody Jurisdiction Act (UCCJEA)
- Follow US court petition format
- Consider state-specific custody factors
- Reference child's best interests standard"""
        }

        # Language instructions
        language_map = {
            "en": "Write in clear, professional English.",
            "de": "Schreiben Sie in klarem, professionellem Deutsch. Use formal legal German.",
            "tr": "Açık, profesyonel Türkçe yazın. Use formal legal Turkish.",
            "fr": "Écrivez en français clair et professionnel.",
            "es": "Escriba en español claro y profesional."
        }

        # JSON output format
        json_format = """
OUTPUT FORMAT (JSON):
{
    "title": "Petition title",
    "introduction": "Opening paragraph introducing the petition",
    "statement_of_facts": "Detailed factual account of the case (numbered paragraphs)",
    "legal_arguments": "Legal analysis and arguments supporting the petition",
    "relief_requested": "Formal statement of relief requested",
    "conclusion": "Closing statement",
    "key_legal_points": ["point 1", "point 2", "point 3"],
    "evidence_references": ["Evidence item 1", "Evidence item 2"],
    "confidence": 0.0-1.0
}"""

        # Combine all parts
        full_prompt = "\n\n".join([
            base_instructions,
            jurisdiction_instructions.get(request.jurisdiction, ""),
            language_map.get(request.language, language_map["en"]),
            json_format
        ])

        return full_prompt

    def _compile_full_document(
        self,
        petition_data: Dict[str, Any],
        request: PetitionRequest
    ) -> str:
        """Compile all sections into a full document."""

        sections = []

        # Title
        sections.append(petition_data["title"].upper())
        sections.append("=" * len(petition_data["title"]))
        sections.append("")

        # Header with case info
        if request.court_name:
            sections.append(f"Court: {request.court_name}")
        if request.case_number:
            sections.append(f"Case No: {request.case_number}")
        sections.append(f"Petitioner: {request.petitioner_name}")
        sections.append(f"Respondent: {request.respondent_name}")
        sections.append("")

        # Introduction
        sections.append("I. INTRODUCTION")
        intro = petition_data["introduction"]
        sections.append(intro if isinstance(intro, str) else "\n".join(intro))
        sections.append("")

        # Statement of Facts
        sections.append("II. STATEMENT OF FACTS")
        facts = petition_data["statement_of_facts"]
        sections.append(facts if isinstance(facts, str) else "\n".join(facts))
        sections.append("")

        # Legal Arguments
        sections.append("III. LEGAL ARGUMENTS")
        args = petition_data["legal_arguments"]
        sections.append(args if isinstance(args, str) else "\n".join(args))
        sections.append("")

        # Relief Requested
        sections.append("IV. RELIEF REQUESTED")
        relief = petition_data["relief_requested"]
        sections.append(relief if isinstance(relief, str) else "\n".join(relief))
        sections.append("")

        # Conclusion
        sections.append("V. CONCLUSION")
        conclusion = petition_data["conclusion"]
        sections.append(conclusion if isinstance(conclusion, str) else "\n".join(conclusion))
        sections.append("")

        # Signature block
        sections.append(f"\nRespectfully submitted,")
        sections.append(f"\nDate: {datetime.now().strftime('%Y-%m-%d')}")
        if request.attorney_name:
            sections.append(f"\n{request.attorney_name}")
            sections.append("Attorney for Petitioner")
        else:
            sections.append(f"\n{request.petitioner_name}")
            sections.append("Petitioner, Pro Se")

        return "\n".join(sections)

    async def generate_quick_petition(
        self,
        petition_type: PetitionType,
        case_description: str,
        petitioner_name: str,
        respondent_name: str,
        child_name: str,
        child_age: int,
        relief_requested: List[str],
        jurisdiction: CourtJurisdiction = CourtJurisdiction.TURKEY,
        language: str = "en"
    ) -> GeneratedPetition:
        """
        Quick petition generation with minimal inputs.
        Perfect for "Baş Yolla" one-click workflow.

        Args:
            petition_type: Type of petition
            case_description: Brief case description
            petitioner_name: Petitioner's name
            respondent_name: Respondent's name
            child_name: Child's name
            child_age: Child's age
            relief_requested: List of requested relief
            jurisdiction: Court jurisdiction
            language: Document language

        Returns:
            Generated petition
        """
        # Build minimal request
        request = PetitionRequest(
            petition_type=petition_type,
            case_id=f"quick_{datetime.now().timestamp()}",
            jurisdiction=jurisdiction,
            language=language,
            petitioner_name=petitioner_name,
            respondent_name=respondent_name,
            child_name=child_name,
            child_age=child_age,
            case_description=case_description,
            key_incidents=[case_description],  # Use description as incident
            evidence_items=[],
            relief_requested=relief_requested,
            urgency_level="normal"
        )

        return await self.generate_petition(request)
