"""
Multilingual AI API Router
Provides endpoints for language detection, translation, and cultural context analysis.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..ai.multilingual.language_detector import LanguageDetector
from ..ai.multilingual.idiom_translator import IdiomTranslator
from ..ai.multilingual.cultural_context import CulturalContextAnalyzer
from ..ai.multilingual.cultural_analyzer import CulturalAnalyzer
from ..ai.multilingual.legal_terminology import LegalTerminologyManager
from .. import db

router = APIRouter(
    prefix="/multilingual",
    tags=["multilingual"],
    responses={404: {"description": "Not found"}},
)


# =============================================================================
# Pydantic Models
# =============================================================================

class LanguageDetectionRequest(BaseModel):
    """Request for language detection."""
    text: str
    detailed: bool = False


class LanguageDetectionResult(BaseModel):
    """Language detection result."""
    detected_language: str
    language_name: str
    confidence: float
    script: Optional[str] = None
    alternative_languages: Optional[List[Dict[str, Any]]] = None


class TranslationRequest(BaseModel):
    """Request for translation."""
    text: str
    source_language: Optional[str] = None  # Auto-detect if not provided
    target_language: str
    preserve_legal_terms: bool = True
    include_idiom_explanations: bool = False


class TranslationResult(BaseModel):
    """Translation result."""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    legal_terms_preserved: List[Dict[str, str]]
    idiom_explanations: Optional[List[Dict[str, str]]] = None
    confidence: float


class LegalTermRequest(BaseModel):
    """Request for legal terminology lookup."""
    term: str
    source_jurisdiction: str  # german, turkish, eu, uk, us
    target_jurisdiction: Optional[str] = None


class LegalTermResult(BaseModel):
    """Legal term translation result."""
    original_term: str
    source_jurisdiction: str
    translations: Dict[str, Dict[str, str]]  # jurisdiction -> {term, definition, context}
    usage_notes: List[str]
    related_terms: List[str]


class CulturalContextRequest(BaseModel):
    """Request for cultural context analysis."""
    text: str
    source_culture: Optional[str] = None  # Auto-detect if not provided
    analysis_depth: str = "standard"  # brief, standard, detailed


class CulturalContextResult(BaseModel):
    """Cultural context analysis result."""
    text: str
    detected_culture: str
    cultural_elements: List[Dict[str, Any]]
    sensitivity_flags: List[str]
    recommendations: List[str]
    context_score: float


# =============================================================================
# Language Detection Endpoints
# =============================================================================

@router.post("/detect", response_model=LanguageDetectionResult)
async def detect_language(request: LanguageDetectionRequest):
    """
    Detect language of text.

    Identifies the language and script of the provided text,
    with support for mixed-language content detection.
    """
    try:
        detector = LanguageDetector()

        result = detector.detect(
            text=request.text,
            detailed=request.detailed
        )

        return LanguageDetectionResult(
            detected_language=result.language_code,
            language_name=result.language_name,
            confidence=result.confidence,
            script=result.script,
            alternative_languages=[
                {"code": alt.code, "name": alt.name, "confidence": alt.confidence}
                for alt in result.alternatives
            ] if request.detailed and result.alternatives else None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Language detection failed: {str(e)}")


@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages.

    Returns all languages supported for detection and translation.
    """
    return {
        "languages": [
            {"code": "en", "name": "English", "script": "Latin", "direction": "ltr"},
            {"code": "de", "name": "German", "script": "Latin", "direction": "ltr"},
            {"code": "tr", "name": "Turkish", "script": "Latin", "direction": "ltr"},
            {"code": "ar", "name": "Arabic", "script": "Arabic", "direction": "rtl"},
            {"code": "fa", "name": "Persian (Farsi)", "script": "Arabic", "direction": "rtl"},
            {"code": "ku", "name": "Kurdish (Kurmanji)", "script": "Latin", "direction": "ltr"},
            {"code": "ckb", "name": "Kurdish (Sorani)", "script": "Arabic", "direction": "rtl"},
            {"code": "ru", "name": "Russian", "script": "Cyrillic", "direction": "ltr"},
            {"code": "fr", "name": "French", "script": "Latin", "direction": "ltr"},
            {"code": "es", "name": "Spanish", "script": "Latin", "direction": "ltr"},
            {"code": "it", "name": "Italian", "script": "Latin", "direction": "ltr"},
            {"code": "nl", "name": "Dutch", "script": "Latin", "direction": "ltr"}
        ],
        "total_supported": 12
    }


# =============================================================================
# Translation Endpoints
# =============================================================================

@router.post("/translate", response_model=TranslationResult)
async def translate_text(request: TranslationRequest):
    """
    Translate text with legal term preservation.

    Translates text while preserving legal terminology and
    providing idiom explanations when needed.
    """
    try:
        detector = LanguageDetector()
        translator = IdiomTranslator()
        legal_manager = LegalTerminologyManager()

        # Auto-detect source language if not provided
        source_lang = request.source_language
        if not source_lang:
            detection = detector.detect(request.text)
            source_lang = detection.language_code

        # Identify legal terms
        legal_terms = []
        if request.preserve_legal_terms:
            terms = legal_manager.identify_terms(request.text, source_lang)
            legal_terms = [
                {"original": t.term, "translated": legal_manager.get_equivalent(t, request.target_language)}
                for t in terms
            ]

        # Translate
        translation = translator.translate(
            text=request.text,
            source_lang=source_lang,
            target_lang=request.target_language,
            preserve_terms=[t["original"] for t in legal_terms]
        )

        # Get idiom explanations if requested
        idiom_explanations = None
        if request.include_idiom_explanations:
            idioms = translator.identify_idioms(request.text, source_lang)
            idiom_explanations = [
                {"idiom": i.text, "meaning": i.meaning, "translation": i.target_equivalent}
                for i in idioms
            ]

        return TranslationResult(
            original_text=request.text,
            translated_text=translation.text,
            source_language=source_lang,
            target_language=request.target_language,
            legal_terms_preserved=legal_terms,
            idiom_explanations=idiom_explanations,
            confidence=translation.confidence
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


# =============================================================================
# Legal Terminology Endpoints
# =============================================================================

@router.post("/terminology", response_model=LegalTermResult)
async def lookup_legal_term(request: LegalTermRequest):
    """
    Look up legal terminology across jurisdictions.

    Finds equivalent terms and definitions across different
    legal systems (German, Turkish, EU, UK, US).
    """
    try:
        legal_manager = LegalTerminologyManager()

        result = legal_manager.lookup(
            term=request.term,
            source_jurisdiction=request.source_jurisdiction,
            target_jurisdiction=request.target_jurisdiction
        )

        return LegalTermResult(
            original_term=request.term,
            source_jurisdiction=request.source_jurisdiction,
            translations=result.translations,
            usage_notes=result.usage_notes,
            related_terms=result.related_terms
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terminology lookup failed: {str(e)}")


@router.get("/terminology/jurisdictions")
async def get_jurisdictions():
    """Get supported legal jurisdictions."""
    return {
        "jurisdictions": [
            {
                "code": "german",
                "name": "German Law",
                "system": "Civil Law",
                "family_law_type": "Familienrecht"
            },
            {
                "code": "turkish",
                "name": "Turkish Law",
                "system": "Civil Law",
                "family_law_type": "Aile Hukuku"
            },
            {
                "code": "eu",
                "name": "EU Law",
                "system": "Supranational",
                "family_law_type": "Brussels IIa"
            },
            {
                "code": "uk",
                "name": "UK Law",
                "system": "Common Law",
                "family_law_type": "Family Law"
            },
            {
                "code": "us",
                "name": "US Law",
                "system": "Common Law",
                "family_law_type": "Family Law (State)"
            }
        ]
    }


@router.get("/terminology/categories")
async def get_term_categories():
    """Get legal terminology categories."""
    return {
        "categories": [
            {"id": "custody", "name": "Custody & Visitation", "example_terms": ["joint custody", "visitation rights", "parental authority"]},
            {"id": "evidence", "name": "Evidence & Proof", "example_terms": ["admissibility", "burden of proof", "expert witness"]},
            {"id": "procedure", "name": "Court Procedure", "example_terms": ["motion", "hearing", "appeal"]},
            {"id": "protection", "name": "Child Protection", "example_terms": ["child welfare", "protective custody", "safeguarding"]},
            {"id": "financial", "name": "Financial Matters", "example_terms": ["child support", "alimony", "asset division"]}
        ]
    }


# =============================================================================
# Cultural Context Endpoints
# =============================================================================

@router.post("/cultural-context", response_model=CulturalContextResult)
async def analyze_cultural_context(request: CulturalContextRequest):
    """
    Analyze cultural context of text.

    Identifies cultural elements, sensitivity issues, and
    provides recommendations for cross-cultural communication.
    """
    try:
        cultural_analyzer = CulturalAnalyzer()
        context_analyzer = CulturalContextAnalyzer()
        detector = LanguageDetector()

        # Detect culture if not provided
        culture = request.source_culture
        if not culture:
            detection = detector.detect(request.text)
            culture = _language_to_culture(detection.language_code)

        # Analyze cultural elements
        elements = cultural_analyzer.analyze(
            text=request.text,
            culture=culture,
            depth=request.analysis_depth
        )

        # Check for sensitivity flags
        sensitivity_flags = context_analyzer.check_sensitivity(
            text=request.text,
            culture=culture
        )

        # Generate recommendations
        recommendations = context_analyzer.generate_recommendations(
            elements=elements,
            flags=sensitivity_flags
        )

        # Calculate context score
        context_score = _calculate_context_score(elements, sensitivity_flags)

        return CulturalContextResult(
            text=request.text,
            detected_culture=culture,
            cultural_elements=[
                {
                    "type": e.type,
                    "content": e.content,
                    "significance": e.significance,
                    "explanation": e.explanation
                }
                for e in elements
            ],
            sensitivity_flags=sensitivity_flags,
            recommendations=recommendations,
            context_score=context_score
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cultural analysis failed: {str(e)}")


@router.get("/cultural-context/cultures")
async def get_supported_cultures():
    """Get supported cultural contexts."""
    return {
        "cultures": [
            {
                "code": "turkish",
                "name": "Turkish",
                "region": "Turkey",
                "key_elements": ["honor culture", "family hierarchy", "religious references"]
            },
            {
                "code": "kurdish",
                "name": "Kurdish",
                "region": "Kurdistan Region",
                "key_elements": ["tribal structure", "honor traditions", "diaspora context"]
            },
            {
                "code": "german",
                "name": "German",
                "region": "Germany",
                "key_elements": ["directness", "privacy", "formal/informal distinction"]
            },
            {
                "code": "arabic",
                "name": "Arabic",
                "region": "Middle East/North Africa",
                "key_elements": ["honor/shame", "extended family", "religious context"]
            },
            {
                "code": "persian",
                "name": "Persian",
                "region": "Iran/Afghanistan",
                "key_elements": ["ta'arof politeness", "indirect communication", "poetry references"]
            }
        ]
    }


# =============================================================================
# Batch Operations
# =============================================================================

@router.post("/batch/detect")
async def batch_detect_languages(texts: List[str] = Body(...)):
    """
    Detect languages for multiple texts.

    Efficiently processes multiple texts for language detection.
    """
    try:
        detector = LanguageDetector()

        results = []
        for text in texts[:50]:  # Limit to 50 texts
            try:
                result = detector.detect(text)
                results.append({
                    "text_preview": text[:100] + "..." if len(text) > 100 else text,
                    "language": result.language_code,
                    "language_name": result.language_name,
                    "confidence": result.confidence
                })
            except Exception:
                results.append({
                    "text_preview": text[:100] + "..." if len(text) > 100 else text,
                    "language": "unknown",
                    "error": "Detection failed"
                })

        return {
            "total_processed": len(results),
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch detection failed: {str(e)}")


@router.post("/batch/translate")
async def batch_translate(
    texts: List[str] = Body(...),
    target_language: str = Query(...),
    source_language: Optional[str] = Query(None)
):
    """
    Translate multiple texts.

    Efficiently translates multiple texts to the target language.
    """
    try:
        detector = LanguageDetector()
        translator = IdiomTranslator()

        results = []
        for text in texts[:20]:  # Limit to 20 texts
            try:
                src_lang = source_language
                if not src_lang:
                    detection = detector.detect(text)
                    src_lang = detection.language_code

                translation = translator.translate(
                    text=text,
                    source_lang=src_lang,
                    target_lang=target_language
                )

                results.append({
                    "original": text[:200] + "..." if len(text) > 200 else text,
                    "translated": translation.text,
                    "source_language": src_lang,
                    "confidence": translation.confidence
                })
            except Exception as ex:
                results.append({
                    "original": text[:200] + "..." if len(text) > 200 else text,
                    "error": str(ex)
                })

        return {
            "target_language": target_language,
            "total_processed": len(results),
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch translation failed: {str(e)}")


# =============================================================================
# Helper Functions
# =============================================================================

def _language_to_culture(lang_code: str) -> str:
    """Map language code to cultural context."""
    mapping = {
        "tr": "turkish",
        "ku": "kurdish",
        "ckb": "kurdish",
        "de": "german",
        "ar": "arabic",
        "fa": "persian",
        "en": "western",
        "fr": "western",
        "ru": "eastern_european"
    }
    return mapping.get(lang_code, "unknown")


def _calculate_context_score(elements: List, flags: List) -> float:
    """Calculate cultural context complexity score."""
    base_score = len(elements) * 10
    flag_penalty = len(flags) * 5

    # Normalize to 0-1 range
    score = min(100, base_score) - flag_penalty
    return max(0, score) / 100
