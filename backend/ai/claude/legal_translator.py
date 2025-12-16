"""
AI-Powered Legal Document Translator
Dynamic legal translation with cultural context using Claude AI.

Enhances static terminology database with AI-powered translation.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging

from .client import ClaudeClient

logger = logging.getLogger(__name__)


class TranslationType(str, Enum):
    """Types of legal translation."""
    DOCUMENT = "document"  # Full document translation
    TERMINOLOGY = "terminology"  # Legal term translation
    EVIDENCE = "evidence"  # Evidence description
    PETITION = "petition"  # Court petition
    CORRESPONDENCE = "correspondence"  # Legal correspondence


@dataclass
class TranslationRequest:
    """Request for legal translation."""
    source_text: str
    source_language: str  # ISO 639-1: en, tr, de, etc.
    target_language: str
    translation_type: TranslationType

    # Jurisdiction context
    source_jurisdiction: Optional[str] = None  # "turkey", "germany", etc.
    target_jurisdiction: Optional[str] = None

    # Domain context
    legal_domain: Optional[str] = None  # "custody", "child_protection", etc.
    formality_level: str = "formal"  # "formal", "informal", "technical"

    # Additional context
    preserve_legal_force: bool = True  # Maintain legal equivalence
    include_annotations: bool = False  # Add translator notes
    cultural_adaptation: bool = True  # Adapt cultural references


@dataclass
class TranslationResult:
    """AI-generated translation result."""
    translation_id: str
    original_text: str
    translated_text: str
    source_language: str
    target_language: str

    # Quality metrics
    confidence: float  # 0-1
    legal_accuracy: float  # 0-1
    cultural_appropriateness: float  # 0-1

    # Annotations
    terminology_notes: List[Dict[str, str]]  # Term-specific notes
    cultural_notes: List[str]  # Cultural adaptation notes
    warnings: List[str]  # Important warnings
    false_friends: List[Dict[str, str]]  # Potential misunderstandings

    # Metadata
    translated_at: datetime
    model_used: str
    tokens_used: Dict[str, int]


class LegalTranslator:
    """
    AI-powered legal translator for family law documents.
    Provides culturally-aware, jurisdiction-specific translations.
    """

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """Initialize legal translator."""
        self.client = claude_client or ClaudeClient()
        logger.info("Legal Translator initialized")

    async def translate(
        self,
        request: TranslationRequest
    ) -> TranslationResult:
        """
        Translate legal text with cultural and jurisdictional awareness.

        Args:
            request: Translation request

        Returns:
            AI-generated translation with annotations
        """
        logger.info(
            f"Translating {request.translation_type} from "
            f"{request.source_language} to {request.target_language}"
        )

        # Build translation prompt
        prompt = self._build_translation_prompt(request)
        system_prompt = self._get_system_prompt(request)

        try:
            # Get Claude translation
            response = await self.client.send_message(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=system_prompt,
                temperature=0.3,  # Lower for accuracy
                max_tokens=4096
            )

            # Parse response
            translation_data = json.loads(response["content"])

            # Create result
            result = TranslationResult(
                translation_id=f"trans_{datetime.now().timestamp()}",
                original_text=request.source_text,
                translated_text=translation_data["translated_text"],
                source_language=request.source_language,
                target_language=request.target_language,
                confidence=translation_data.get("confidence", 0.9),
                legal_accuracy=translation_data.get("legal_accuracy", 0.9),
                cultural_appropriateness=translation_data.get("cultural_appropriateness", 0.9),
                terminology_notes=translation_data.get("terminology_notes", []),
                cultural_notes=translation_data.get("cultural_notes", []),
                warnings=translation_data.get("warnings", []),
                false_friends=translation_data.get("false_friends", []),
                translated_at=datetime.now(),
                model_used=response["model"],
                tokens_used=response["usage"]
            )

            logger.info(
                f"Translation complete: {len(result.translated_text)} chars, "
                f"confidence {result.confidence:.2f}"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse translation response: {e}")
            raise ValueError("Invalid AI translation format")
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise

    def _build_translation_prompt(self, request: TranslationRequest) -> str:
        """Build translation prompt with context."""
        prompt_parts = [
            f"Translate the following legal text from {request.source_language} to {request.target_language}.",
            f"\n**Document Type:** {request.translation_type.value}",
        ]

        if request.source_jurisdiction:
            prompt_parts.append(f"**Source Jurisdiction:** {request.source_jurisdiction}")
        if request.target_jurisdiction:
            prompt_parts.append(f"**Target Jurisdiction:** {request.target_jurisdiction}")
        if request.legal_domain:
            prompt_parts.append(f"**Legal Domain:** {request.legal_domain}")

        prompt_parts.extend([
            f"**Formality Level:** {request.formality_level}",
            f"**Preserve Legal Force:** {'Yes' if request.preserve_legal_force else 'No'}",
            f"**Cultural Adaptation:** {'Yes' if request.cultural_adaptation else 'No'}",
            f"\n**TEXT TO TRANSLATE:**",
            f"\n{request.source_text}",
            f"\nProvide translation in JSON format as specified."
        ])

        return "\n".join(prompt_parts)

    def _get_system_prompt(self, request: TranslationRequest) -> str:
        """Get language and context-specific system prompt."""

        # Language pair instructions
        language_instructions = {
            ("tr", "en"): """Turkish to English Legal Translation:
- Translate formal Turkish legal language to professional English
- Maintain legal precision: "velayet" = "custody", "nafaka" = "child support/alimony"
- Adapt Turkish formalities to English legal style
- Note cultural differences (e.g., "Sayın Hakim" = "Your Honor")""",

            ("en", "tr"): """English to Turkish Legal Translation:
- Translate to formal, professional Turkish legal language
- Use correct legal terminology: "custody" = "velayet", "visitation" = "kişisel ilişki kurma hakkı"
- Adapt to Turkish court formalities and structure
- Use respectful forms: "the court" = "Sayın Mahkeme""",

            ("de", "en"): """German to English Legal Translation:
- Translate formal German legal language (BGB, FamFG) to English
- Legal terms: "Sorgerecht" = "parental authority/custody", "Umgangsrecht" = "visitation rights"
- Adapt German legal concepts to English common law equivalents
- Note differences: German "Kindeswohl" is broader than "best interests""",

            ("en", "de"): """English to German Legal Translation:
- Translate to formal German legal language
- Use correct legal terminology and cite relevant laws (BGB, FamFG)
- Adapt common law concepts to German civil law
- Maintain formal German court style""",

            ("tr", "de"): """Turkish to German Legal Translation:
- Translate between two civil law systems
- Find equivalent concepts: TMK ↔ BGB
- Maintain legal precision across jurisdictions
- Note procedural differences between Turkish and German family courts""",
        }

        pair_key = (request.source_language, request.target_language)
        language_instruction = language_instructions.get(
            pair_key,
            f"Translate from {request.source_language} to {request.target_language} with legal precision."
        )

        # Jurisdiction-specific instructions
        jurisdiction_notes = {
            "turkey": """Turkish Legal Context:
- Reference TMK (Turkish Civil Code) where applicable
- Use formal Turkish court petition style
- Consider Turkish family law procedures
- Adapt to Turkish cultural norms around family""",

            "germany": """German Legal Context:
- Reference BGB, FamFG where applicable
- Use formal German court document style (Schriftsatz)
- Consider German Familiengericht procedures
- Distinguish Sorgerecht, Umgangsrecht, Aufenthaltsbestimmungsrecht""",

            "eu": """EU Legal Context:
- Reference Brussels IIa/IIb Regulation
- Consider Hague Convention provisions
- Maintain cross-border legal clarity
- Use EU terminology consistently"""
        }

        target_jurisdiction_note = ""
        if request.target_jurisdiction:
            target_jurisdiction_note = jurisdiction_notes.get(request.target_jurisdiction, "")

        # JSON format
        json_format = """
OUTPUT FORMAT (JSON):
{
    "translated_text": "The translated legal text maintaining legal precision and cultural appropriateness",
    "confidence": 0.0-1.0,
    "legal_accuracy": 0.0-1.0,
    "cultural_appropriateness": 0.0-1.0,
    "terminology_notes": [
        {"term": "original term", "translation": "translated term", "note": "explanation"}
    ],
    "cultural_notes": ["Cultural adaptation note 1", "Cultural adaptation note 2"],
    "warnings": ["Warning about potential misunderstanding"],
    "false_friends": [
        {"term": "false friend term", "warning": "Common mistranslation warning"}
    ]
}

CRITICAL REQUIREMENTS:
1. Maintain legal precision - do not simplify legal concepts
2. Use correct jurisdiction-specific terminology
3. Preserve legal force and meaning
4. Note any untranslatable concepts
5. Warn about false friends and common errors
6. Provide terminology notes for key legal terms
7. Adapt cultural references appropriately
"""

        # Combine all parts
        full_prompt = "\n\n".join(filter(None, [
            "You are an expert legal translator specializing in family law.",
            language_instruction,
            target_jurisdiction_note,
            json_format
        ]))

        return full_prompt

    async def translate_batch(
        self,
        texts: List[str],
        source_language: str,
        target_language: str,
        translation_type: TranslationType = TranslationType.DOCUMENT,
        **kwargs
    ) -> List[TranslationResult]:
        """
        Translate multiple texts in batch.

        Args:
            texts: List of texts to translate
            source_language: Source language code
            target_language: Target language code
            translation_type: Type of translation
            **kwargs: Additional TranslationRequest parameters

        Returns:
            List of translation results
        """
        results = []

        for text in texts:
            request = TranslationRequest(
                source_text=text,
                source_language=source_language,
                target_language=target_language,
                translation_type=translation_type,
                **kwargs
            )

            result = await self.translate(request)
            results.append(result)

        return results

    async def quick_translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """
        Quick translation without detailed annotations.
        Perfect for simple queries.

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Translated text only
        """
        request = TranslationRequest(
            source_text=text,
            source_language=source_lang,
            target_language=target_lang,
            translation_type=TranslationType.CORRESPONDENCE,
            include_annotations=False
        )

        result = await self.translate(request)
        return result.translated_text
