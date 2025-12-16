"""
AI Chat API Router
Endpoints for user-friendly AI chat assistant.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from backend.ai.claude import ChatAssistant, ChatSession, ChatMessage, MessageType
from backend.ai.claude import RiskAnalyzer, RiskAnalysisResult
from backend.ai.claude import PetitionGenerator, PetitionType, CourtJurisdiction
from backend.auth import get_current_user
from backend.models import User

router = APIRouter(prefix="/ai", tags=["AI Assistant"])
logger = logging.getLogger(__name__)

# Initialize AI services
chat_assistant = ChatAssistant()
risk_analyzer = RiskAnalyzer()
petition_generator = PetitionGenerator()

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
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
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
async def get_petition_types(current_user: User = Depends(get_current_user)):
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
