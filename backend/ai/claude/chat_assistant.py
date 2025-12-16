"""
Chat Assistant for SafeChild
User-friendly AI assistant designed for 40+ women with minimal tech experience.

Design Principles:
- Simple, conversational language
- Empathetic and supportive tone
- One-click actions ("Baş Yolla")
- Step-by-step guidance
- Visual feedback
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from .client import ClaudeClient

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Types of messages in chat."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ACTION = "action"  # One-click action prompt


class QuickAction(str, Enum):
    """One-click actions for users."""
    ANALYZE_RISK = "analyze_risk"
    COLLECT_EVIDENCE = "collect_evidence"
    GET_LEGAL_HELP = "get_legal_help"
    WRITE_DOCUMENT = "write_document"
    CALL_EXPERT = "call_expert"
    EMERGENCY_HELP = "emergency_help"


@dataclass
class ChatMessage:
    """Single chat message."""
    message_id: str
    message_type: MessageType
    content: str
    timestamp: datetime
    quick_actions: Optional[List[Dict[str, str]]] = None  # Suggested actions
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatSession:
    """Chat conversation session."""
    session_id: str
    user_id: str
    case_id: Optional[str]
    messages: List[ChatMessage]
    created_at: datetime
    last_activity: datetime
    context: Dict[str, Any] = field(default_factory=dict)


class ChatAssistant:
    """
    User-friendly AI chat assistant.
    Designed for 40+ women with minimal tech experience.
    """

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """Initialize chat assistant."""
        self.client = claude_client or ClaudeClient()
        logger.info("Chat Assistant initialized")

    async def send_message(
        self,
        session: ChatSession,
        user_message: str
    ) -> ChatMessage:
        """
        Send a message and get AI response.

        Args:
            session: Current chat session
            user_message: User's message

        Returns:
            Assistant's response message with quick actions
        """
        logger.info(f"Processing message in session {session.session_id}")

        # Add user message to session
        user_msg = ChatMessage(
            message_id=f"msg_{len(session.messages)}",
            message_type=MessageType.USER,
            content=user_message,
            timestamp=datetime.now()
        )
        session.messages.append(user_msg)

        # Build conversation history for Claude
        conversation = self._build_conversation_history(session)

        # System prompt for user-friendly assistant
        system_prompt = """You are SafeChild AI assistant. Your role is to help women (especially 40+ age) with child custody cases.

IMPORTANT PRINCIPLES:
1. Use simple, clear language (no legal jargon)
2. Be empathetic and supportive
3. Explain step-by-step
4. Give hope, be solution-focused
5. Say 2-3 things at a time (don't overload with information)
6. Ask questions, listen

USER PROFILE:
- Not tech-savvy
- Going through emotionally challenging process
- Needs clear, simple instructions
- Requires trust and reassurance

RESPONSE FORMAT:
- Short paragraphs (2-3 sentences)
- Use emojis sparingly 💚
- Steps in list format
- Clear, actionable suggestions

ALWAYS:
- Start with empathy ("I understand")
- Suggest concrete steps
- Clearly state next action
- Offer simple one-click buttons"""

        try:
            # Get Claude's response
            response = await self.client.send_message(
                messages=conversation,
                system_prompt=system_prompt,
                temperature=0.8  # More conversational
            )

            # Determine quick actions based on context
            quick_actions = self._suggest_quick_actions(
                user_message=user_message,
                ai_response=response["content"],
                session_context=session.context
            )

            # Create assistant message
            assistant_msg = ChatMessage(
                message_id=f"msg_{len(session.messages)}",
                message_type=MessageType.ASSISTANT,
                content=response["content"],
                timestamp=datetime.now(),
                quick_actions=quick_actions,
                metadata={"tokens_used": response["usage"]}
            )

            # Add to session
            session.messages.append(assistant_msg)
            session.last_activity = datetime.now()

            logger.info(
                f"Response generated with {len(quick_actions or [])} quick actions"
            )

            return assistant_msg

        except Exception as e:
            logger.error(f"Failed to generate chat response: {e}")
            # Return friendly error message
            return ChatMessage(
                message_id=f"msg_{len(session.messages)}",
                message_type=MessageType.SYSTEM,
                content="I'm sorry, I'm experiencing an issue right now. Please try again in a few moments. 🙏",
                timestamp=datetime.now()
            )

    def _build_conversation_history(
        self,
        session: ChatSession
    ) -> List[Dict[str, str]]:
        """
        Build conversation history for Claude.
        Keep last 10 messages to avoid token limits.
        """
        recent_messages = session.messages[-10:]  # Last 10 messages

        conversation = []
        for msg in recent_messages:
            if msg.message_type == MessageType.USER:
                conversation.append({
                    "role": "user",
                    "content": msg.content
                })
            elif msg.message_type == MessageType.ASSISTANT:
                conversation.append({
                    "role": "assistant",
                    "content": msg.content
                })

        return conversation

    def _suggest_quick_actions(
        self,
        user_message: str,
        ai_response: str,
        session_context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Suggest one-click actions based on conversation context.

        Returns:
            List of quick action buttons
        """
        actions = []

        # Risk-related keywords
        risk_keywords = ["danger", "risk", "fear", "worry", "concern", "harm", "unsafe"]
        if any(keyword in user_message.lower() for keyword in risk_keywords):
            actions.append({
                "action": "analyze_risk",
                "label": "🛡️ Analyze Risk",
                "description": "Get AI risk assessment"
            })

        # Evidence collection keywords
        evidence_keywords = ["evidence", "proof", "message", "photo", "record", "document"]
        if any(keyword in user_message.lower() for keyword in evidence_keywords):
            actions.append({
                "action": "collect_evidence",
                "label": "📸 Collect Evidence",
                "description": "Start evidence collection"
            })

        # Legal help keywords
        legal_keywords = ["lawyer", "attorney", "court", "legal", "petition", "custody"]
        if any(keyword in user_message.lower() for keyword in legal_keywords):
            actions.append({
                "action": "get_legal_help",
                "label": "⚖️ Legal Help",
                "description": "Find lawyer or prepare documents"
            })

        # Emergency keywords
        emergency_keywords = ["urgent", "emergency", "now", "immediately", "violence", "abuse"]
        if any(keyword in user_message.lower() for keyword in emergency_keywords):
            actions.insert(0, {  # Insert at beginning
                "action": "emergency_help",
                "label": "🚨 EMERGENCY HELP",
                "description": "Emergency protocol"
            })

        # Always offer to write document if discussing legal matters
        if "petition" in ai_response.lower() or "document" in ai_response.lower():
            actions.append({
                "action": "write_document",
                "label": "📝 Prepare Document",
                "description": "Auto-generate with AI"
            })

        # Limit to max 4 actions
        return actions[:4]

    async def quick_guidance(self, question: str) -> str:
        """
        Quick question answering for simple queries.
        No session required.

        Args:
            question: User's question

        Returns:
            Short, simple answer (2-3 sentences)
        """
        system_prompt = """Provide short and concise answer. Max 3 sentences.
Use simple language. Explain for 40+ year old women."""

        response = await self.client.simple_prompt(
            prompt=question,
            system_prompt=system_prompt,
            max_tokens=200
        )

        return response

    async def explain_legal_term(self, term: str) -> str:
        """
        Explain legal terms in simple language.

        Args:
            term: Legal term to explain

        Returns:
            Simple explanation
        """
        prompt = f"""What does "{term}" mean?

Explain this to a 40+ year old woman with no technical background.
Use simple examples. Max 4 sentences."""

        response = await self.client.simple_prompt(
            prompt=prompt,
            max_tokens=300
        )

        return response

    async def create_welcome_message(self, user_name: Optional[str] = None) -> ChatMessage:
        """
        Create friendly welcome message for new users.

        Args:
            user_name: Optional user name

        Returns:
            Welcome message
        """
        greeting = f"Hello {user_name}! 👋" if user_name else "Hello! 👋"

        content = f"""{greeting}

I'm your SafeChild AI assistant. I'm here to help you with your child's safety.

**How can I help you?**
- Analyze your situation
- Help you collect evidence
- Prepare court documents
- Answer legal questions

Tell me about your situation, I'm listening. 💚"""

        quick_actions = [
            {
                "action": "analyze_risk",
                "label": "🛡️ Analyze Situation",
                "description": "Is there risk to your child?"
            },
            {
                "action": "collect_evidence",
                "label": "📸 Collect Evidence",
                "description": "What evidence should I collect?"
            },
            {
                "action": "get_legal_help",
                "label": "⚖️ Legal Help",
                "description": "Lawyer or document preparation"
            }
        ]

        return ChatMessage(
            message_id="welcome",
            message_type=MessageType.ASSISTANT,
            content=content,
            timestamp=datetime.now(),
            quick_actions=quick_actions
        )
