"""
AI Chat API Router
Endpoints for user-friendly AI chat assistant.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from backend.ai.claude import ChatAssistant, ChatSession, ChatMessage
from backend.ai.claude import RiskAnalyzer, RiskAnalysisResult
from backend.ai.claude import PetitionGenerator, PetitionType, CourtJurisdiction
from backend.ai.claude import LegalTranslator, TranslationRequest, TranslationResult, TranslationType
from backend.ai.claude import AlienationDetector, AlienationAnalysisRequest, AlienationEvidence
from backend.ai.claude import EvidenceAnalyzer, EvidenceAnalysisRequest, EvidenceItem, EvidenceType
from backend.ai.claude import TimelineGenerator, TimelineGenerationRequest, TimelineEvent, EventType, EventSeverity
from backend.ai.claude import CaseSummaryGenerator, CaseSummaryRequest
from backend.auth import get_current_user

router = APIRouter(prefix="/ai", tags=["AI Assistant"])
logger = logging.getLogger(__name__)

# Initialize AI services
chat_assistant = ChatAssistant()
risk_analyzer = RiskAnalyzer()
petition_generator = PetitionGenerator()
legal_translator = LegalTranslator()
alienation_detector = AlienationDetector()
evidence_analyzer = EvidenceAnalyzer()
timeline_generator = TimelineGenerator()
case_summary_generator = CaseSummaryGenerator()

# In-memory session storage (replace with Redis/DB in production)
active_sessions: Dict[str, ChatSession] = {}


# Request/Response Models
class ChatRequest(BaseModel):
    """User chat message request."""
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    case_id: Optional[str] = None


class ChatResponse(BaseModel):
    """AI chat response."""
    session_id: str
    message: str
    quick_actions: Optional[List[Dict[str, str]]] = None
    timestamp: datetime


class RiskAnalysisRequest(BaseModel):
    """Risk analysis request."""
    case_id: str
    case_description: str
    additional_context: Optional[Dict[str, Any]] = None


class QuickActionRequest(BaseModel):
    """Quick action execution request."""
    action: str
    session_id: str
    context: Optional[Dict[str, Any]] = None


@router.post("/chat", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Send a message to AI chat assistant.

    **User-Friendly Features:**
    - Simple conversational interface
    - Automatic quick action suggestions
    - Context-aware responses
    - Empathetic tone for 40+ women

    **Example:**
    ```json
    {
      "message": "My ex-spouse is threatening my child, what should I do?"
    }
    ```
    """
    try:
        # Get or create session
        session_id = request.session_id or f"session_{current_user.id}_{datetime.now().timestamp()}"

        if session_id not in active_sessions:
            # Create new session
            session = ChatSession(
                session_id=session_id,
                user_id=current_user.id,
                case_id=request.case_id,
                messages=[],
                created_at=datetime.now(),
                last_activity=datetime.now()
            )

            # Add welcome message
            welcome_msg = await chat_assistant.create_welcome_message(
                user_name=current_user.username
            )
            session.messages.append(welcome_msg)

            active_sessions[session_id] = session
        else:
            session = active_sessions[session_id]

        # Send message and get response
        response_msg = await chat_assistant.send_message(
            session=session,
            user_message=request.message
        )

        logger.info(
            f"Chat message processed for user {current_user.id}, "
            f"session {session_id}"
        )

        return ChatResponse(
            session_id=session_id,
            message=response_msg.content,
            quick_actions=response_msg.quick_actions,
            timestamp=response_msg.timestamp
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process your message at the moment. Please try again."
        )


@router.post("/analyze-risk", response_model=Dict[str, Any])
async def analyze_case_risk(
    request: RiskAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    **One-Click Risk Analysis**

    Analyze situation with AI in one click!

    **What It Does:**
    - Determines risk level for your child
    - Lists major dangers
    - Provides immediate action items
    - Explains in simple terms

    **Results:**
    - Risk score (0-10)
    - Simple explanation
    - Action checklist

    **Example:**
    ```json
    {
      "case_id": "case_123",
      "case_description": "My ex-spouse came to watch the child while drinking alcohol..."
    }
    ```
    """
    try:
        logger.info(f"Risk analysis requested for case {request.case_id}")

        # Perform AI risk analysis
        analysis = await risk_analyzer.analyze_case(
            case_id=request.case_id,
            case_description=request.case_description,
            additional_context=request.additional_context
        )

        # Return user-friendly response
        return {
            "success": True,
            "risk_level": analysis.risk_level.value,
            "risk_score": analysis.overall_risk_score,
            "summary": analysis.parent_friendly_summary,
            "top_concerns": analysis.top_concerns[:3],  # Top 3
            "immediate_actions": analysis.immediate_actions[:5],  # Top 5
            "next_steps": analysis.next_steps[:3],  # Top 3
            "confidence": analysis.confidence,
            "timestamp": analysis.analysis_timestamp.isoformat()
        }

    except Exception as e:
        logger.error(f"Risk analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to perform risk analysis. Please try again later."
        )


@router.post("/quick-action")
async def execute_quick_action(
    request: QuickActionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    **Execute one-click action.**

    Available actions:
    - `analyze_risk`: Risk analizi yap
    - `collect_evidence`: Kanıt toplama başlat
    - `get_legal_help`: Hukuki yardım al
    - `write_document`: Belge hazırla
    - `emergency_help`: Acil yardım

    Returns next steps and UI to display.
    """
    try:
        logger.info(f"Quick action: {request.action} for user {current_user.id}")

        # Handle different quick actions
        if request.action == "analyze_risk":
            return {
                "action": "analyze_risk",
                "title": "Risk Analysis",
                "description": "Let's analyze your situation with AI",
                "next_step": "form",
                "form_fields": [
                    {
                        "name": "case_description",
                        "label": "What's happening? Tell me about it",
                        "type": "textarea",
                        "placeholder": "Example: My ex-spouse came to pick up the child while...",
                        "required": True
                    },
                    {
                        "name": "child_age",
                        "label": "Your child's age",
                        "type": "number",
                        "required": False
                    }
                ],
                "button_text": "Analyze 🛡️"
            }

        elif request.action == "collect_evidence":
            return {
                "action": "collect_evidence",
                "title": "Evidence Collection",
                "description": "What type of evidence should you collect?",
                "next_step": "guide",
                "guide_steps": [
                    "📸 Photos: Take photos of everything related to your child",
                    "💬 Messages: Save all messages (WhatsApp, SMS)",
                    "📝 Notes: Write down events with dates and times",
                    "👥 Witnesses: Who saw what? Make a list"
                ],
                "button_text": "Start Collecting Evidence"
            }

        elif request.action == "emergency_help":
            return {
                "action": "emergency_help",
                "title": "🚨 EMERGENCY HELP",
                "description": "If your child is in danger, call immediately:",
                "next_step": "emergency_contacts",
                "contacts": [
                    {
                        "name": "Police (Emergency)",
                        "phone": "155",
                        "description": "If there's violence or danger"
                    },
                    {
                        "name": "Women's Shelter",
                        "phone": "183",
                        "description": "Safe housing"
                    },
                    {
                        "name": "Child Protection Hotline",
                        "phone": "183",
                        "description": "Child protection services"
                    }
                ],
                "button_text": "Call Now"
            }

        elif request.action == "write_document":
            return {
                "action": "write_document",
                "title": "Prepare Document",
                "description": "Which document would you like to prepare?",
                "next_step": "document_type",
                "document_types": [
                    {
                        "type": "custody_petition",
                        "label": "Custody Petition",
                        "icon": "⚖️"
                    },
                    {
                        "type": "protection_order",
                        "label": "Protection Order Request",
                        "icon": "🛡️"
                    },
                    {
                        "type": "evidence_summary",
                        "label": "Evidence Summary",
                        "icon": "📋"
                    }
                ],
                "button_text": "Select and Prepare"
            }

        else:
            return {"error": "Unknown action"}

    except Exception as e:
        logger.error(f"Quick action error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to execute action."
        )


@router.get("/chat/history/{session_id}")
async def get_chat_history(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get chat history for a session."""
    if session_id not in active_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found."
        )

    session = active_sessions[session_id]

    # Verify user owns this session
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this chat."
        )

    return {
        "session_id": session.session_id,
        "messages": [
            {
                "type": msg.message_type.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "quick_actions": msg.quick_actions
            }
            for msg in session.messages
        ]
    }


@router.post("/explain-term")
async def explain_legal_term(
    term: str,
    current_user: dict = Depends(get_current_user)
):
    """
    **Explain Legal Term**

    Don't understand a word? Let's explain it in simple terms!

    **Examples:**
    - What does "custody" mean?
    - What is a "protection order"?
    - What does "alimony" mean?
    """
    try:
        explanation = await chat_assistant.explain_legal_term(term)
        return {
            "term": term,
            "explanation": explanation,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Term explanation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to explain term."
        )


@router.get("/health")
async def ai_health_check():
    """Check if AI services are working."""
    try:
        # Quick health check
        is_healthy = await chat_assistant.client.health_check()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# =============================================================================
# Court Document Generation Endpoints
# =============================================================================

class PetitionGenerationRequest(BaseModel):
    """Request to generate a court petition."""
    petition_type: str  # "custody", "protection_order", "visitation_modification", etc.
    case_description: str = Field(..., min_length=50, max_length=5000)

    # Personal information
    petitioner_name: str
    respondent_name: str
    child_name: str
    child_age: int = Field(..., ge=0, le=18)

    # What they're asking for
    relief_requested: List[str] = Field(..., min_items=1, max_items=10)

    # Optional details
    jurisdiction: str = "turkey"  # "turkey", "germany", "eu", "us"
    language: str = "en"  # "en", "tr", "de"
    court_name: Optional[str] = None
    case_number: Optional[str] = None
    attorney_name: Optional[str] = None
    key_incidents: Optional[List[str]] = None
    evidence_summary: Optional[str] = None
    urgency: str = "normal"  # "normal", "urgent", "emergency"


@router.post("/generate-petition", response_model=Dict[str, Any])
async def generate_court_petition(
    request: PetitionGenerationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    **One-Click Court Petition Generator**

    Generate professional court petitions automatically using AI.

    **Petition Types:**
    - `custody` - Child custody petition
    - `protection_order` - Protection/restraining order
    - `visitation_modification` - Modify visitation rights
    - `child_support` - Child support petition
    - `emergency_custody` - Emergency custody
    - `evidence_summary` - Evidence summary report

    **Example:**
    ```json
    {
      "petition_type": "custody",
      "case_description": "Ex-spouse has been exposing child to unsafe conditions...",
      "petitioner_name": "Jane Doe",
      "respondent_name": "John Doe",
      "child_name": "Emily Doe",
      "child_age": 7,
      "relief_requested": [
        "Grant primary custody to petitioner",
        "Restrict respondent's visitation rights",
        "Order supervised visitation"
      ],
      "jurisdiction": "turkey",
      "language": "en"
    }
    ```

    **Returns:**
    - Complete court-ready petition
    - Word count and page estimate
    - Key legal points
    - Evidence references
    """
    try:
        logger.info(
            f"Petition generation requested: {request.petition_type} for user {current_user.id}"
        )

        # Validate petition type
        try:
            petition_type_enum = PetitionType(request.petition_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid petition type: {request.petition_type}"
            )

        # Validate jurisdiction
        try:
            jurisdiction_enum = CourtJurisdiction(request.jurisdiction)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid jurisdiction: {request.jurisdiction}"
            )

        # Generate petition using AI
        petition = await petition_generator.generate_quick_petition(
            petition_type=petition_type_enum,
            case_description=request.case_description,
            petitioner_name=request.petitioner_name,
            respondent_name=request.respondent_name,
            child_name=request.child_name,
            child_age=request.child_age,
            relief_requested=request.relief_requested,
            jurisdiction=jurisdiction_enum,
            language=request.language
        )

        logger.info(
            f"Petition generated: {petition.word_count} words, "
            f"{petition.estimated_pages} pages"
        )

        return {
            "success": True,
            "petition_id": petition.petition_id,
            "petition_type": petition.petition_type.value,
            "jurisdiction": petition.jurisdiction.value,
            "language": petition.language,
            "title": petition.title,
            "full_document": petition.full_document,
            "sections": {
                "introduction": petition.introduction,
                "statement_of_facts": petition.statement_of_facts,
                "legal_arguments": petition.legal_arguments,
                "relief_requested": petition.relief_requested_section,
                "conclusion": petition.conclusion
            },
            "metadata": {
                "word_count": petition.word_count,
                "estimated_pages": petition.estimated_pages,
                "key_legal_points": petition.key_legal_points,
                "supporting_evidence_refs": petition.supporting_evidence_refs,
                "confidence": petition.confidence
            },
            "generated_at": petition.generated_at.isoformat(),
            "model_used": petition.model_used
        }

    except Exception as e:
        logger.error(f"Petition generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate petition. Please try again later."
        )


@router.get("/petition-types")
async def get_petition_types(current_user: dict = Depends(get_current_user)):
    """
    Get available petition types with descriptions.

    Returns list of all supported petition types.
    """
    return {
        "petition_types": [
            {
                "type": "custody",
                "label": "Child Custody Petition",
                "description": "Request primary or sole custody of your child",
                "icon": "⚖️"
            },
            {
                "type": "protection_order",
                "label": "Protection Order",
                "description": "Request a protection/restraining order",
                "icon": "🛡️"
            },
            {
                "type": "visitation_modification",
                "label": "Modify Visitation Rights",
                "description": "Change existing visitation arrangements",
                "icon": "📅"
            },
            {
                "type": "child_support",
                "label": "Child Support Petition",
                "description": "Request child support or modify amount",
                "icon": "💰"
            },
            {
                "type": "emergency_custody",
                "label": "Emergency Custody",
                "description": "Urgent custody request due to immediate danger",
                "icon": "🚨"
            },
            {
                "type": "evidence_summary",
                "label": "Evidence Summary Report",
                "description": "Organized summary of all evidence",
                "icon": "📋"
            }
        ],
        "jurisdictions": [
            {"code": "turkey", "name": "Turkey (Türkiye)"},
            {"code": "germany", "name": "Germany (Deutschland)"},
            {"code": "eu", "name": "European Union (EU)"},
            {"code": "us", "name": "United States"},
            {"code": "uk", "name": "United Kingdom"}
        ],
        "languages": [
            {"code": "en", "name": "English"},
            {"code": "tr", "name": "Türkçe (Turkish)"},
            {"code": "de", "name": "Deutsch (German)"},
            {"code": "fr", "name": "Français (French)"},
            {"code": "es", "name": "Español (Spanish)"}
        ]
    }


# Translation Request/Response Models
class TranslationRequestModel(BaseModel):
    """Legal document translation request."""
    source_text: str = Field(..., min_length=1, max_length=50000)
    source_language: str = Field(..., pattern="^[a-z]{2}$")
    target_language: str = Field(..., pattern="^[a-z]{2}$")
    translation_type: str = "document"  # document, terminology, evidence, petition, correspondence
    source_jurisdiction: Optional[str] = None
    target_jurisdiction: Optional[str] = None
    legal_domain: Optional[str] = None
    preserve_legal_force: bool = True
    include_annotations: bool = True
    cultural_adaptation: bool = True


class QuickTranslationRequest(BaseModel):
    """Quick translation without annotations."""
    text: str = Field(..., min_length=1, max_length=10000)
    source_language: str = Field(..., pattern="^[a-z]{2}$")
    target_language: str = Field(..., pattern="^[a-z]{2}$")


class BatchTranslationRequest(BaseModel):
    """Batch translation request."""
    texts: List[str] = Field(..., min_items=1, max_items=50)
    source_language: str = Field(..., pattern="^[a-z]{2}$")
    target_language: str = Field(..., pattern="^[a-z]{2}$")
    translation_type: str = "document"


@router.post("/translate", response_model=Dict[str, Any])
async def translate_legal_document(
    request: TranslationRequestModel,
    current_user: dict = Depends(get_current_user)
):
    """
    Translate legal document with cultural and jurisdictional awareness.

    **Features:**
    - AI-powered legal translation
    - Preserves legal precision
    - Cultural context adaptation
    - Terminology notes
    - False friends warnings

    **Example:**
    ```json
    {
      "source_text": "Velayet davası açmak istiyorum.",
      "source_language": "tr",
      "target_language": "en",
      "translation_type": "document",
      "source_jurisdiction": "turkey"
    }
    ```

    **Returns:**
    ```json
    {
      "translated_text": "I want to file a custody petition.",
      "confidence": 0.95,
      "terminology_notes": [...],
      "cultural_notes": [...],
      "warnings": [...]
    }
    ```
    """
    try:
        # Validate translation type
        try:
            translation_type_enum = TranslationType(request.translation_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid translation type: {request.translation_type}"
            )

        # Build translation request
        translation_request = TranslationRequest(
            source_text=request.source_text,
            source_language=request.source_language,
            target_language=request.target_language,
            translation_type=translation_type_enum,
            source_jurisdiction=request.source_jurisdiction,
            target_jurisdiction=request.target_jurisdiction,
            legal_domain=request.legal_domain,
            preserve_legal_force=request.preserve_legal_force,
            include_annotations=request.include_annotations,
            cultural_adaptation=request.cultural_adaptation
        )

        # Translate
        result = await legal_translator.translate(translation_request)

        logger.info(
            f"Translation completed: {request.source_language} -> {request.target_language}, "
            f"confidence {result.confidence:.2f}"
        )

        return {
            "success": True,
            "translation_id": result.translation_id,
            "translated_text": result.translated_text,
            "source_language": result.source_language,
            "target_language": result.target_language,
            "confidence": result.confidence,
            "legal_accuracy": result.legal_accuracy,
            "cultural_appropriateness": result.cultural_appropriateness,
            "terminology_notes": result.terminology_notes,
            "cultural_notes": result.cultural_notes,
            "warnings": result.warnings,
            "false_friends": result.false_friends,
            "translated_at": result.translated_at.isoformat(),
            "model_used": result.model_used,
            "tokens_used": result.tokens_used
        }

    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to translate document. Please try again later."
        )


@router.post("/translate-quick", response_model=Dict[str, Any])
async def quick_translate(
    request: QuickTranslationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Quick translation without detailed annotations.

    Perfect for simple queries and short texts.

    **Example:**
    ```json
    {
      "text": "Merhaba",
      "source_language": "tr",
      "target_language": "en"
    }
    ```

    **Returns:**
    ```json
    {
      "translated_text": "Hello"
    }
    ```
    """
    try:
        translated_text = await legal_translator.quick_translate(
            text=request.text,
            source_lang=request.source_language,
            target_lang=request.target_language
        )

        return {
            "success": True,
            "translated_text": translated_text,
            "source_language": request.source_language,
            "target_language": request.target_language
        }

    except Exception as e:
        logger.error(f"Quick translation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to translate text. Please try again later."
        )


@router.post("/translate-batch", response_model=Dict[str, Any])
async def batch_translate(
    request: BatchTranslationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Translate multiple texts in batch.

    **Example:**
    ```json
    {
      "texts": ["Velayet", "Nafaka", "Görüşme hakkı"],
      "source_language": "tr",
      "target_language": "en",
      "translation_type": "terminology"
    }
    ```

    **Returns:**
    ```json
    {
      "translations": [
        {"original": "Velayet", "translated": "Custody"},
        {"original": "Nafaka", "translated": "Child support"},
        {"original": "Görüşme hakkı", "translated": "Visitation rights"}
      ]
    }
    ```
    """
    try:
        # Validate translation type
        try:
            translation_type_enum = TranslationType(request.translation_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid translation type: {request.translation_type}"
            )

        # Batch translate
        results = await legal_translator.translate_batch(
            texts=request.texts,
            source_language=request.source_language,
            target_language=request.target_language,
            translation_type=translation_type_enum
        )

        translations = []
        for i, result in enumerate(results):
            translations.append({
                "original": request.texts[i],
                "translated": result.translated_text,
                "confidence": result.confidence
            })

        logger.info(
            f"Batch translation completed: {len(translations)} items, "
            f"{request.source_language} -> {request.target_language}"
        )

        return {
            "success": True,
            "count": len(translations),
            "translations": translations,
            "source_language": request.source_language,
            "target_language": request.target_language
        }

    except Exception as e:
        logger.error(f"Batch translation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to translate batch. Please try again later."
        )


@router.get("/translation-languages")
async def get_translation_languages(current_user: dict = Depends(get_current_user)):
    """
    Get supported translation language pairs with descriptions.

    Returns all available language pairs for legal translation.
    """
    return {
        "language_pairs": [
            {
                "source": "tr",
                "target": "en",
                "source_name": "Turkish",
                "target_name": "English",
                "description": "Turkish to English legal translation",
                "jurisdictions": ["turkey", "eu"]
            },
            {
                "source": "en",
                "target": "tr",
                "source_name": "English",
                "target_name": "Turkish",
                "description": "English to Turkish legal translation",
                "jurisdictions": ["turkey", "eu"]
            },
            {
                "source": "de",
                "target": "en",
                "source_name": "German",
                "target_name": "English",
                "description": "German to English legal translation",
                "jurisdictions": ["germany", "eu"]
            },
            {
                "source": "en",
                "target": "de",
                "source_name": "English",
                "target_name": "German",
                "description": "English to German legal translation",
                "jurisdictions": ["germany", "eu"]
            },
            {
                "source": "tr",
                "target": "de",
                "source_name": "Turkish",
                "target_name": "German",
                "description": "Turkish to German legal translation",
                "jurisdictions": ["turkey", "germany", "eu"]
            },
            {
                "source": "de",
                "target": "tr",
                "source_name": "German",
                "target_name": "Turkish",
                "description": "German to Turkish legal translation",
                "jurisdictions": ["turkey", "germany", "eu"]
            }
        ],
        "translation_types": [
            {
                "type": "document",
                "label": "Full Document",
                "description": "Complete legal document translation",
                "icon": "📄"
            },
            {
                "type": "terminology",
                "label": "Legal Terms",
                "description": "Legal terminology translation",
                "icon": "📖"
            },
            {
                "type": "evidence",
                "label": "Evidence Description",
                "description": "Evidence documentation translation",
                "icon": "🔍"
            },
            {
                "type": "petition",
                "label": "Court Petition",
                "description": "Court petition translation",
                "icon": "⚖️"
            },
            {
                "type": "correspondence",
                "label": "Legal Correspondence",
                "description": "Legal letter/email translation",
                "icon": "✉️"
            }
        ]
    }


# Parental Alienation Detection
class AlienationAnalysisRequestModel(BaseModel):
    """Parental alienation analysis request."""
    case_id: str
    child_name: str = Field(..., min_length=1)
    child_age: int = Field(..., ge=0, le=18)
    alienating_parent: str = Field(..., min_length=1)
    targeted_parent: str = Field(..., min_length=1)
    case_description: str = Field(..., min_length=10)

    # Optional detailed information
    custody_arrangement: Optional[str] = None
    relationship_history: Optional[str] = None
    child_statements: Optional[List[str]] = None
    behavioral_changes: Optional[List[str]] = None
    evidence_items: Optional[List[Dict[str, Any]]] = None


@router.post("/analyze-alienation", response_model=Dict[str, Any])
async def analyze_parental_alienation(
    request: AlienationAnalysisRequestModel,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze case for parental alienation patterns.

    **Critical Feature for Custody Cases:**
    - Detects 10 common alienation tactics
    - Provides severity assessment (none/mild/moderate/severe/critical)
    - Generates court-ready documentation
    - Suggests evidence collection strategies

    **Example:**
    ```json
    {
      "case_id": "case_001",
      "child_name": "Emma",
      "child_age": 8,
      "alienating_parent": "John Doe",
      "targeted_parent": "Jane Doe",
      "case_description": "Father constantly tells child that mother doesn't love her...",
      "child_statements": [
        "Daddy says mommy doesn't want me",
        "I don't want to see mommy anymore"
      ],
      "behavioral_changes": [
        "Child refuses video calls with mother",
        "Child becomes anxious before visits"
      ]
    }
    ```

    **Returns:**
    ```json
    {
      "severity": "moderate",
      "severity_score": 6.5,
      "detected_tactics": [
        {
          "tactic": "badmouthing",
          "description": "...",
          "court_relevance": "..."
        }
      ],
      "immediate_actions": ["Document all incidents", "Request therapy", ...],
      "executive_summary": "Court-ready summary..."
    }
    ```
    """
    try:
        # Convert evidence items if provided
        evidence_items = []
        if request.evidence_items:
            for item in request.evidence_items:
                evidence_items.append(AlienationEvidence(
                    evidence_type=item.get("evidence_type", "incident"),
                    description=item.get("description", ""),
                    date=item.get("date"),
                    source=item.get("source"),
                    severity_contribution=item.get("severity_contribution", 0.5)
                ))

        # Build analysis request
        analysis_request = AlienationAnalysisRequest(
            case_id=request.case_id,
            child_name=request.child_name,
            child_age=request.child_age,
            alienating_parent=request.alienating_parent,
            targeted_parent=request.targeted_parent,
            case_description=request.case_description,
            evidence_items=evidence_items,
            custody_arrangement=request.custody_arrangement,
            relationship_history=request.relationship_history,
            child_statements=request.child_statements,
            behavioral_changes=request.behavioral_changes
        )

        # Analyze
        result = await alienation_detector.analyze_case(analysis_request)

        logger.info(
            f"Alienation analysis completed for case {request.case_id}: "
            f"{result.severity.value} (score {result.severity_score:.1f}/10)"
        )

        return {
            "success": True,
            "analysis_id": result.analysis_id,
            "case_id": result.case_id,
            "severity": result.severity.value,
            "severity_score": result.severity_score,
            "confidence": result.confidence,
            "detected_tactics": [
                {
                    "tactic": tactic.tactic.value,
                    "description": tactic.description,
                    "evidence_references": tactic.evidence_references,
                    "severity": tactic.severity,
                    "court_relevance": tactic.court_relevance
                }
                for tactic in result.detected_tactics
            ],
            "primary_concerns": result.primary_concerns,
            "behavioral_indicators": result.behavioral_indicators,
            "child_impact_assessment": result.child_impact_assessment,
            "long_term_risks": result.long_term_risks,
            "immediate_actions": result.immediate_actions,
            "documentation_suggestions": result.documentation_suggestions,
            "court_presentation_tips": result.court_presentation_tips,
            "executive_summary": result.executive_summary,
            "evidence_summary": result.evidence_summary,
            "expert_opinion": result.expert_opinion,
            "analyzed_at": result.analyzed_at.isoformat(),
            "model_used": result.model_used,
            "tokens_used": result.tokens_used
        }

    except Exception as e:
        logger.error(f"Alienation analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to analyze case for parental alienation. Please try again later."
        )


@router.post("/analyze-alienation-quick", response_model=Dict[str, Any])
async def quick_alienation_analysis(
    case_description: str = Body(..., min_length=10),
    child_name: str = Body(..., min_length=1),
    child_age: int = Body(..., ge=0, le=18),
    alienating_parent: str = Body(..., min_length=1),
    targeted_parent: str = Body(..., min_length=1),
    current_user: dict = Depends(get_current_user)
):
    """
    Quick parental alienation screening.

    Perfect for initial assessment with minimal information.

    **Example:**
    ```
    POST /api/ai/analyze-alienation-quick
    {
      "case_description": "Ex-husband tells our 7-year-old that I abandoned the family...",
      "child_name": "Sophie",
      "child_age": 7,
      "alienating_parent": "Michael Smith",
      "targeted_parent": "Lisa Smith"
    }
    ```
    """
    try:
        result = await alienation_detector.quick_analysis(
            case_description=case_description,
            child_name=child_name,
            child_age=child_age,
            alienating_parent=alienating_parent,
            targeted_parent=targeted_parent
        )

        return {
            "success": True,
            "severity": result.severity.value,
            "severity_score": result.severity_score,
            "confidence": result.confidence,
            "primary_concerns": result.primary_concerns[:5],  # Top 5
            "immediate_actions": result.immediate_actions[:3],  # Top 3
            "detected_tactics": [
                {"tactic": t.tactic.value, "description": t.description}
                for t in result.detected_tactics[:5]  # Top 5 tactics
            ]
        }

    except Exception as e:
        logger.error(f"Quick alienation analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to analyze case. Please try again later."
        )


@router.get("/alienation-info")
async def get_alienation_info(current_user: dict = Depends(get_current_user)):
    """
    Get information about parental alienation detection.

    Returns explanations of tactics, severity levels, and what to document.
    """
    return {
        "alienation_tactics": [
            {
                "tactic": "badmouthing",
                "label": "Badmouthing",
                "description": "Repeatedly criticizing or demeaning the other parent to the child",
                "examples": [
                    "Telling child 'Your mother doesn't love you'",
                    "Calling other parent insulting names in front of child"
                ],
                "icon": "🗣️"
            },
            {
                "tactic": "limiting_contact",
                "label": "Limiting Contact",
                "description": "Restricting phone calls, visits, or communication with other parent",
                "examples": [
                    "Not answering phone during scheduled call times",
                    "Claiming child is 'too busy' to talk"
                ],
                "icon": "📵"
            },
            {
                "tactic": "creating_conflict",
                "label": "Creating Conflict",
                "description": "Forcing child to choose sides or demonstrate loyalty",
                "examples": [
                    "Asking 'Who do you love more?'",
                    "Making child feel guilty for enjoying time with other parent"
                ],
                "icon": "⚔️"
            },
            {
                "tactic": "false_allegations",
                "label": "False Allegations",
                "description": "Making untrue accusations of abuse or neglect",
                "examples": [
                    "Falsely claiming abuse to authorities",
                    "Exaggerating minor incidents"
                ],
                "icon": "⚠️"
            },
            {
                "tactic": "interfering_visitation",
                "label": "Interfering with Visitation",
                "description": "Finding excuses to cancel or shorten visits",
                "examples": [
                    "Last-minute cancellations",
                    "Scheduling conflicting activities during visitation"
                ],
                "icon": "🚫"
            },
            {
                "tactic": "emotional_manipulation",
                "label": "Emotional Manipulation",
                "description": "Using guilt, fear, or emotional blackmail on child",
                "examples": [
                    "Saying 'If you love me, you won't see your father'",
                    "Acting sad or upset when child returns from visit"
                ],
                "icon": "😢"
            },
            {
                "tactic": "erasing_parent",
                "label": "Erasing the Parent",
                "description": "Removing photos, gifts, or mentions of other parent from child's life",
                "examples": [
                    "Removing all photos of other parent",
                    "Throwing away gifts from other parent"
                ],
                "icon": "🗑️"
            },
            {
                "tactic": "withholding_info",
                "label": "Withholding Information",
                "description": "Not sharing school, medical, or important updates",
                "examples": [
                    "Not informing about school events",
                    "Hiding medical information"
                ],
                "icon": "🤐"
            },
            {
                "tactic": "rewarding_rejection",
                "label": "Rewarding Rejection",
                "description": "Praising child for refusing to see other parent",
                "examples": [
                    "Giving treats when child refuses visit",
                    "Expressing pride when child rejects other parent"
                ],
                "icon": "🎁"
            },
            {
                "tactic": "undermining_authority",
                "label": "Undermining Authority",
                "description": "Disrespecting or invalidating other parent's rules and decisions",
                "examples": [
                    "Telling child to ignore other parent's rules",
                    "Contradicting other parent's discipline"
                ],
                "icon": "👎"
            }
        ],
        "severity_levels": [
            {
                "level": "none",
                "label": "No Alienation",
                "score_range": "0-1",
                "description": "No signs of parental alienation detected",
                "color": "green"
            },
            {
                "level": "mild",
                "label": "Mild",
                "score_range": "2-4",
                "description": "Early warning signs present, preventable with intervention",
                "color": "yellow",
                "action": "Monitor situation, document incidents"
            },
            {
                "level": "moderate",
                "label": "Moderate",
                "score_range": "5-6",
                "description": "Clear alienation pattern established, intervention needed",
                "color": "orange",
                "action": "Seek therapy, consider legal action"
            },
            {
                "level": "severe",
                "label": "Severe",
                "score_range": "7-8",
                "description": "Advanced alienation, therapeutic intervention required",
                "color": "red",
                "action": "Emergency therapy, custody modification needed"
            },
            {
                "level": "critical",
                "label": "Critical",
                "score_range": "9-10",
                "description": "Complete rejection, emergency intervention required",
                "color": "darkred",
                "action": "Immediate court action, emergency custody change"
            }
        ],
        "what_to_document": [
            "Date, time, and description of each incident",
            "Exact words said by alienating parent (if known)",
            "Child's statements and reactions",
            "Behavioral changes in child",
            "Cancelled or interfered visits",
            "Withheld information about child",
            "Messages, emails, or texts showing alienation",
            "Witness accounts",
            "Photos or videos (if appropriate)",
            "School or therapy reports"
        ]
    }


# Evidence Analysis
class EvidenceItemModel(BaseModel):
    """Evidence item for analysis."""
    evidence_id: str
    evidence_type: str  # text_message, email, photo, video, audio, document, etc.
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    date_occurred: Optional[str] = None
    date_collected: Optional[str] = None
    source: Optional[str] = None


class EvidenceAnalysisRequestModel(BaseModel):
    """Evidence analysis request."""
    case_id: str
    evidence_items: List[EvidenceItemModel] = Field(..., min_items=1, max_items=100)
    case_context: Optional[str] = None
    analysis_purpose: str = "custody"


@router.post("/analyze-evidence", response_model=Dict[str, Any])
async def analyze_case_evidence(
    request: EvidenceAnalysisRequestModel,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze evidence items for court case.

    **One-Click Evidence Organization** ("Baş Yolla"):
    - Upload all evidence (messages, photos, documents)
    - AI analyzes relevance and legal significance
    - Gets organized timeline and presentation order
    - Court-ready evidence summary generated

    **Example:**
    ```json
    {
      "case_id": "case_001",
      "evidence_items": [
        {
          "evidence_id": "1",
          "evidence_type": "text_message",
          "title": "Threatening message from ex-spouse",
          "description": "Text saying 'You'll never see the kids again'",
          "date_occurred": "2024-12-01"
        },
        {
          "evidence_id": "2",
          "evidence_type": "photo",
          "title": "Bruises on child's arm",
          "description": "Photo showing bruising after visit with father",
          "date_occurred": "2024-12-05"
        }
      ],
      "case_context": "Custody case, seeking primary custody due to abuse"
    }
    ```

    **Returns:**
    ```json
    {
      "evidence_strength": 8.5,
      "critical_items": 2,
      "analyzed_items": [...],
      "evidence_timeline": [...],
      "presentation_order": ["2", "1", "3"],
      "executive_summary": "...",
      "gaps_identified": ["Need medical records", ...],
      "recommendations": [...]
    }
    ```
    """
    try:
        # Convert evidence items
        evidence_items = []
        for item in request.evidence_items:
            try:
                evidence_type = EvidenceType(item.evidence_type)
            except ValueError:
                # Default to document if type unknown
                evidence_type = EvidenceType.DOCUMENT

            evidence_items.append(EvidenceItem(
                evidence_id=item.evidence_id,
                evidence_type=evidence_type,
                title=item.title,
                description=item.description,
                date_occurred=item.date_occurred,
                date_collected=item.date_collected,
                source=item.source
            ))

        # Build analysis request
        analysis_request = EvidenceAnalysisRequest(
            case_id=request.case_id,
            evidence_items=evidence_items,
            case_context=request.case_context,
            analysis_purpose=request.analysis_purpose
        )

        # Analyze
        result = await evidence_analyzer.analyze_evidence(analysis_request)

        logger.info(
            f"Evidence analysis completed for case {request.case_id}: "
            f"{result.total_items} items, {result.critical_items} critical, "
            f"strength {result.evidence_strength:.1f}/10"
        )

        return {
            "success": True,
            "analysis_id": result.analysis_id,
            "case_id": result.case_id,
            "total_items": result.total_items,
            "critical_items": result.critical_items,
            "evidence_strength": result.evidence_strength,
            "confidence": result.confidence,
            "analyzed_items": [
                {
                    "evidence_id": item.evidence_id,
                    "relevance": item.relevance.value,
                    "relevance_score": item.relevance_score,
                    "categories": [cat.value for cat in item.categories],
                    "key_findings": item.key_findings,
                    "legal_significance": item.legal_significance,
                    "court_presentation": item.court_presentation,
                    "potential_challenges": item.potential_challenges,
                    "corroboration_needed": item.corroboration_needed,
                    "related_evidence": item.related_evidence,
                    "timeline_position": item.timeline_position
                }
                for item in result.analyzed_items
            ],
            "executive_summary": result.executive_summary,
            "evidence_timeline": result.evidence_timeline,
            "strength_analysis": result.strength_analysis,
            "gaps_identified": result.gaps_identified,
            "recommendations": result.recommendations,
            "presentation_order": result.presentation_order,
            "opening_statement_points": result.opening_statement_points,
            "analyzed_at": result.analyzed_at.isoformat(),
            "model_used": result.model_used,
            "tokens_used": result.tokens_used
        }

    except Exception as e:
        logger.error(f"Evidence analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to analyze evidence. Please try again later."
        )


@router.get("/evidence-types")
async def get_evidence_types(current_user: dict = Depends(get_current_user)):
    """
    Get all supported evidence types with descriptions.
    """
    return {
        "evidence_types": [
            {
                "type": "text_message",
                "label": "Text Messages",
                "description": "SMS, WhatsApp, iMessage, etc.",
                "icon": "💬",
                "examples": ["Threatening messages", "Parental alienation texts"]
            },
            {
                "type": "email",
                "label": "Emails",
                "description": "Email correspondence",
                "icon": "📧",
                "examples": ["Custody arrangement emails", "Threats via email"]
            },
            {
                "type": "photo",
                "label": "Photos",
                "description": "Visual evidence (bruises, living conditions, etc.)",
                "icon": "📷",
                "examples": ["Bruises on child", "Unsafe living conditions"]
            },
            {
                "type": "video",
                "label": "Videos",
                "description": "Video recordings",
                "icon": "🎥",
                "examples": ["Recorded incidents", "Child's statements"]
            },
            {
                "type": "audio",
                "label": "Audio Recordings",
                "description": "Voice recordings, phone calls",
                "icon": "🎤",
                "examples": ["Threatening voicemails", "Recorded conversations"]
            },
            {
                "type": "document",
                "label": "Documents",
                "description": "Legal documents, records",
                "icon": "📄",
                "examples": ["Court orders", "Custody agreements"]
            },
            {
                "type": "social_media",
                "label": "Social Media",
                "description": "Facebook, Instagram, Twitter posts",
                "icon": "📱",
                "examples": ["Posts showing substance abuse", "Location check-ins"]
            },
            {
                "type": "witness_statement",
                "label": "Witness Statements",
                "description": "Written or recorded witness accounts",
                "icon": "👥",
                "examples": ["Neighbor statements", "Teacher observations"]
            },
            {
                "type": "medical_record",
                "label": "Medical Records",
                "description": "Medical documentation",
                "icon": "🏥",
                "examples": ["Injury reports", "Therapy notes"]
            },
            {
                "type": "police_report",
                "label": "Police Reports",
                "description": "Law enforcement documentation",
                "icon": "🚔",
                "examples": ["Domestic violence reports", "Incident reports"]
            },
            {
                "type": "school_record",
                "label": "School Records",
                "description": "Academic and behavioral records",
                "icon": "🏫",
                "examples": ["Attendance records", "Behavioral changes"]
            }
        ],
        "relevance_levels": [
            {"level": "critical", "label": "Critical", "description": "Essential to proving the case", "color": "red"},
            {"level": "high", "label": "High", "description": "Very important, strongly supports case", "color": "orange"},
            {"level": "moderate", "label": "Moderate", "description": "Supportive, adds to overall picture", "color": "yellow"},
            {"level": "low", "label": "Low", "description": "Background context", "color": "blue"},
            {"level": "minimal", "label": "Minimal", "description": "Not very relevant", "color": "gray"}
        ]
    }


# Timeline Generation - Week 4
class TimelineEventModel(BaseModel):
    """Timeline event for generation."""
    event_id: str
    date: str  # YYYY-MM-DD format
    event_type: str  # incident, visitation, communication, legal_action, etc.
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    severity: Optional[str] = None  # critical, high, moderate, low, info
    evidence_ids: Optional[List[str]] = None
    participants: Optional[List[str]] = None


class TimelineGenerationRequestModel(BaseModel):
    """Timeline generation request."""
    case_id: str
    events: List[TimelineEventModel] = Field(..., min_items=1, max_items=200)
    case_context: Optional[str] = None


@router.post("/generate-timeline", response_model=Dict[str, Any])
async def generate_case_timeline(
    request: TimelineGenerationRequestModel,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate chronological timeline for court case.

    **One-Click Timeline** ("Baş Yolla"):
    - Input all events (incidents, visits, messages, etc.)
    - AI organizes chronologically
    - Identifies patterns and escalation
    - Groups into meaningful periods
    - Court-ready narrative generated

    **Example:**
    ```json
    {
      "case_id": "case_001",
      "events": [
        {
          "event_id": "1",
          "date": "2024-01-15",
          "event_type": "incident",
          "title": "First threatening message",
          "description": "Ex-spouse sent threatening text",
          "severity": "high"
        },
        {
          "event_id": "2",
          "date": "2024-02-10",
          "event_type": "incident",
          "title": "Bruises discovered",
          "description": "Child returned with bruises after visit",
          "severity": "critical"
        }
      ],
      "case_context": "Custody case, pattern of escalating abuse"
    }
    ```

    **Returns:**
    - Organized chronological timeline
    - Period analysis (escalation phases)
    - Pattern identification
    - Court narrative
    - Key dates highlighted
    """
    try:
        # Convert events
        timeline_events = []
        for event_model in request.events:
            try:
                event_type = EventType(event_model.event_type)
            except ValueError:
                event_type = EventType.INCIDENT

            severity = None
            if event_model.severity:
                try:
                    severity = EventSeverity(event_model.severity)
                except ValueError:
                    pass

            timeline_events.append(TimelineEvent(
                event_id=event_model.event_id,
                date=event_model.date,
                event_type=event_type,
                title=event_model.title,
                description=event_model.description,
                severity=severity,
                evidence_ids=event_model.evidence_ids or [],
                participants=event_model.participants or []
            ))

        # Build timeline request
        timeline_request = TimelineGenerationRequest(
            case_id=request.case_id,
            events=timeline_events,
            case_context=request.case_context
        )

        # Generate timeline
        result = await timeline_generator.generate_timeline(timeline_request)

        logger.info(
            f"Timeline generated for case {request.case_id}: "
            f"{result.total_events} events, {len(result.periods)} periods"
        )

        return {
            "success": True,
            "timeline_id": result.timeline_id,
            "case_id": result.case_id,
            "total_events": result.total_events,
            "date_range": result.date_range,
            "organized_events": result.organized_events,
            "periods": [
                {
                    "period_name": period.period_name,
                    "start_date": period.start_date,
                    "end_date": period.end_date,
                    "summary": period.summary,
                    "key_events": period.key_events,
                    "pattern_analysis": period.pattern_analysis
                }
                for period in result.periods
            ],
            "pattern_summary": result.pattern_summary,
            "escalation_analysis": result.escalation_analysis,
            "key_dates": result.key_dates,
            "frequency_analysis": result.frequency_analysis,
            "visual_timeline_description": result.visual_timeline_description,
            "narrative_summary": result.narrative_summary,
            "opening_statement_timeline": result.opening_statement_timeline,
            "critical_events_highlighted": result.critical_events_highlighted,
            "generated_at": result.generated_at.isoformat(),
            "model_used": result.model_used,
            "tokens_used": result.tokens_used
        }

    except Exception as e:
        logger.error(f"Timeline generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate timeline. Please try again later."
        )


# Case Summary Generation - Week 4
class CaseSummaryRequestModel(BaseModel):
    """Comprehensive case summary request."""
    case_id: str
    petitioner_name: str = Field(..., min_length=1)
    respondent_name: str = Field(..., min_length=1)
    child_name: str = Field(..., min_length=1)
    child_age: int = Field(..., ge=0, le=18)
    case_type: str = "custody"
    case_description: str = Field(..., min_length=10)
    relief_requested: List[str] = Field(..., min_items=1)

    # Optional summaries from other analyses
    timeline_summary: Optional[str] = None
    evidence_summary: Optional[str] = None
    risk_analysis_summary: Optional[str] = None
    alienation_analysis_summary: Optional[str] = None

    # Additional context
    jurisdiction: Optional[str] = None
    previous_orders: Optional[List[str]] = None
    medical_concerns: Optional[List[str]] = None
    safety_concerns: Optional[List[str]] = None


@router.post("/generate-case-summary", response_model=Dict[str, Any])
async def generate_comprehensive_case_summary(
    request: CaseSummaryRequestModel,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate comprehensive case summary for court.

    **Complete "Baş Yolla" Package**:
    - Pulls together ALL case information
    - Creates 1-page executive summary
    - Detailed multi-page summary
    - Talking points for court
    - Proposed findings and conclusions
    - Settlement position

    **Perfect For:**
    - Court filing packages
    - Attorney consultations
    - Mediation preparation
    - Settlement negotiations

    **Example:**
    ```json
    {
      "case_id": "case_001",
      "petitioner_name": "Jane Doe",
      "respondent_name": "John Doe",
      "child_name": "Emma Doe",
      "child_age": 7,
      "case_type": "custody",
      "case_description": "Seeking primary custody due to abuse and neglect...",
      "relief_requested": [
        "Primary physical custody",
        "Supervised visitation only",
        "Child support"
      ],
      "evidence_summary": "5 incidents documented with photos...",
      "risk_analysis_summary": "High risk (8.5/10) for child safety...",
      "safety_concerns": ["Physical abuse", "Substance abuse"]
    }
    ```

    **Returns:**
    - One-page summary (for judges/clerks)
    - Detailed summary (full case)
    - Elevator pitch (2-3 sentences)
    - Legal arguments
    - Talking points
    - Settlement position
    """
    try:
        # Build case summary request
        summary_request = CaseSummaryRequest(
            case_id=request.case_id,
            petitioner_name=request.petitioner_name,
            respondent_name=request.respondent_name,
            child_name=request.child_name,
            child_age=request.child_age,
            case_type=request.case_type,
            case_description=request.case_description,
            relief_requested=request.relief_requested,
            timeline_summary=request.timeline_summary,
            evidence_summary=request.evidence_summary,
            risk_analysis_summary=request.risk_analysis_summary,
            alienation_analysis_summary=request.alienation_analysis_summary,
            jurisdiction=request.jurisdiction,
            previous_orders=request.previous_orders,
            medical_concerns=request.medical_concerns,
            safety_concerns=request.safety_concerns
        )

        # Generate summary
        result = await case_summary_generator.generate_summary(summary_request)

        logger.info(
            f"Case summary generated for {request.case_id}: "
            f"{len(result.key_facts)} facts, {len(result.legal_issues)} issues"
        )

        return {
            "success": True,
            "summary_id": result.summary_id,
            "case_id": result.case_id,
            "one_page_summary": result.one_page_summary,
            "detailed_summary": result.detailed_summary,
            "elevator_pitch": result.elevator_pitch,
            "background": result.background,
            "key_facts": result.key_facts,
            "legal_issues": result.legal_issues,
            "evidence_highlights": result.evidence_highlights,
            "child_impact": result.child_impact,
            "safety_concerns_summary": result.safety_concerns_summary,
            "legal_basis": result.legal_basis,
            "supporting_precedents": result.supporting_precedents,
            "relief_justification": result.relief_justification,
            "proposed_findings_of_fact": result.proposed_findings_of_fact,
            "proposed_conclusions_of_law": result.proposed_conclusions_of_law,
            "urgency_statement": result.urgency_statement,
            "talking_points": result.talking_points,
            "questions_for_opposing_counsel": result.questions_for_opposing_counsel,
            "settlement_position": result.settlement_position,
            "generated_at": result.generated_at.isoformat(),
            "model_used": result.model_used,
            "tokens_used": result.tokens_used
        }

    except Exception as e:
        logger.error(f"Case summary generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate case summary. Please try again later."
        )


@router.get("/ai-features")
async def get_all_ai_features(current_user: dict = Depends(get_current_user)):
    """
    Get complete list of all AI features available.

    Returns overview of all AI-powered tools for SafeChild platform.
    """
    return {
        "week_1_2": {
            "chat_assistant": {
                "endpoint": "/api/ai/chat",
                "description": "User-friendly chat for 40+ women",
                "features": ["Simple language", "Quick actions", "Empathetic responses"]
            },
            "risk_analyzer": {
                "endpoint": "/api/ai/analyze-risk",
                "description": "Child safety risk assessment",
                "features": ["Risk scoring (0-10)", "Immediate actions", "Parent-friendly summaries"]
            },
            "petition_generator": {
                "endpoint": "/api/ai/generate-petition",
                "description": "Court petition generation",
                "features": ["6 petition types", "Multi-jurisdiction", "Court-ready documents"]
            }
        },
        "week_3": {
            "legal_translator": {
                "endpoint": "/api/ai/translate",
                "description": "Legal document translation",
                "features": ["TR↔EN, DE↔EN", "Cultural context", "Terminology notes"]
            },
            "alienation_detector": {
                "endpoint": "/api/ai/analyze-alienation",
                "description": "Parental alienation detection",
                "features": ["10 tactics", "5 severity levels", "Court documentation"]
            }
        },
        "week_4": {
            "evidence_analyzer": {
                "endpoint": "/api/ai/analyze-evidence",
                "description": "Evidence organization & analysis",
                "features": ["11 evidence types", "Relevance scoring", "Court presentation order"]
            },
            "timeline_generator": {
                "endpoint": "/api/ai/generate-timeline",
                "description": "Chronological timeline creation",
                "features": ["Pattern detection", "Escalation analysis", "Period grouping"]
            },
            "case_summary_generator": {
                "endpoint": "/api/ai/generate-case-summary",
                "description": "Comprehensive case summary",
                "features": ["1-page summary", "Talking points", "Settlement position"]
            }
        },
        "total_endpoints": 13,
        "philosophy": "Baş Yolla - One-click simplicity for 40+ women with minimal tech experience"
    }


# ========================================================================
# DOCUMENT ANALYSIS (Admin Feature)
# ========================================================================

class DocumentAnalysisRequest(BaseModel):
    """Request for AI document analysis."""
    documentContent: str = Field(..., description="Document content to analyze")
    fileName: str = Field(..., description="Original file name")
    question: str = Field(..., description="Question to ask about the document")
    documentNumber: Optional[str] = None


@router.post("/analyze-document")
async def analyze_document(
    request: DocumentAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    **Analyze Document with AI**
    
    Admin can upload a document and ask AI questions about it.
    The AI will analyze the content and provide insights.
    
    **Use Cases:**
    - Summarize legal documents
    - Extract key information from evidence
    - Identify potential legal issues
    - Translate and explain complex text
    """
    try:
        logger.info(f"Document analysis requested by {current_user.get('email')} for file: {request.fileName}")
        
        # Build prompt for Claude
        analysis_prompt = f"""You are a legal assistant helping analyze a document.

Document Name: {request.fileName}
Document Content:
{request.documentContent[:10000]}  # Limit to first 10k chars

User Question: {request.question}

Please provide a detailed, professional analysis answering the user's question. Focus on:
1. Direct answer to the question
2. Key facts and findings
3. Legal relevance (if applicable)
4. Recommendations or action items

Be concise but thorough."""

        # Use ChatAssistant to analyze
        response = await chat_assistant.send_message(analysis_prompt, session_id=None)
        
        return {
            "analysis": response.content,
            "fileName": request.fileName,
            "question": request.question,
            "timestamp": datetime.now().isoformat(),
            "documentNumber": request.documentNumber
        }
        
    except Exception as e:
        logger.error(f"Document analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document analysis failed: {str(e)}"
        )
