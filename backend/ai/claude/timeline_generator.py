"""
AI-Powered Timeline Generator
Creates chronological timelines for court cases from events and evidence.

Design: Visual timeline for "Baş Yolla" one-click court preparation.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging

from .client import ClaudeClient

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of timeline events."""
    INCIDENT = "incident"  # Abuse, neglect, etc.
    VISITATION = "visitation"  # Custody visit
    COMMUNICATION = "communication"  # Messages, calls
    LEGAL_ACTION = "legal_action"  # Court filings, orders
    BEHAVIORAL = "behavioral"  # Child behavioral changes
    MEDICAL = "medical"  # Medical appointments, injuries
    SCHOOL = "school"  # School events, reports
    WITNESS = "witness"  # Witness observations
    VIOLATION = "violation"  # Court order violations
    POSITIVE = "positive"  # Positive developments


class EventSeverity(str, Enum):
    """Severity of timeline events."""
    CRITICAL = "critical"  # Major incidents
    HIGH = "high"  # Serious events
    MODERATE = "moderate"  # Notable events
    LOW = "low"  # Minor events
    INFO = "info"  # Informational only


@dataclass
class TimelineEvent:
    """Single event on timeline."""
    event_id: str
    date: str  # YYYY-MM-DD format
    event_type: EventType
    title: str
    description: str
    severity: Optional[EventSeverity] = None
    evidence_ids: List[str] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)
    location: Optional[str] = None
    outcome: Optional[str] = None


@dataclass
class TimelineGenerationRequest:
    """Request to generate timeline."""
    case_id: str
    events: List[TimelineEvent]
    case_context: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@dataclass
class TimelinePeriod:
    """Period/phase in timeline."""
    period_name: str
    start_date: str
    end_date: str
    summary: str
    key_events: List[str]  # Event IDs
    pattern_analysis: str


@dataclass
class TimelineGenerationResult:
    """Generated timeline with analysis."""
    timeline_id: str
    case_id: str

    # Timeline data
    total_events: int
    date_range: Dict[str, str]  # start_date, end_date
    organized_events: List[Dict[str, Any]]  # Events in chronological order

    # Analysis
    periods: List[TimelinePeriod]
    pattern_summary: str
    escalation_analysis: str
    key_dates: List[Dict[str, str]]
    frequency_analysis: str

    # Court presentation
    visual_timeline_description: str
    narrative_summary: str
    opening_statement_timeline: str
    critical_events_highlighted: List[str]

    # Metadata
    generated_at: datetime
    model_used: str
    tokens_used: Dict[str, int]


class TimelineGenerator:
    """
    AI-powered timeline generator for court cases.
    Creates organized, visual timelines from events and evidence.
    """

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """Initialize timeline generator."""
        self.client = claude_client or ClaudeClient()
        logger.info("Timeline Generator initialized")

    async def generate_timeline(
        self,
        request: TimelineGenerationRequest
    ) -> TimelineGenerationResult:
        """
        Generate organized timeline from events.

        Args:
            request: Timeline generation request

        Returns:
            Organized timeline with analysis
        """
        logger.info(
            f"Generating timeline for case {request.case_id} "
            f"with {len(request.events)} events"
        )

        # Build generation prompt
        prompt = self._build_generation_prompt(request)
        system_prompt = self._get_system_prompt()

        try:
            # Get Claude analysis
            response = await self.client.send_message(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=4096
            )

            # Parse response
            timeline_data = json.loads(response["content"])

            # Parse periods
            periods = []
            for period_data in timeline_data.get("periods", []):
                periods.append(TimelinePeriod(
                    period_name=period_data["period_name"],
                    start_date=period_data["start_date"],
                    end_date=period_data["end_date"],
                    summary=period_data["summary"],
                    key_events=period_data.get("key_events", []),
                    pattern_analysis=period_data.get("pattern_analysis", "")
                ))

            # Create result
            result = TimelineGenerationResult(
                timeline_id=f"timeline_{request.case_id}_{datetime.now().timestamp()}",
                case_id=request.case_id,
                total_events=len(request.events),
                date_range=timeline_data.get("date_range", {}),
                organized_events=timeline_data.get("organized_events", []),
                periods=periods,
                pattern_summary=timeline_data.get("pattern_summary", ""),
                escalation_analysis=timeline_data.get("escalation_analysis", ""),
                key_dates=timeline_data.get("key_dates", []),
                frequency_analysis=timeline_data.get("frequency_analysis", ""),
                visual_timeline_description=timeline_data.get("visual_timeline_description", ""),
                narrative_summary=timeline_data.get("narrative_summary", ""),
                opening_statement_timeline=timeline_data.get("opening_statement_timeline", ""),
                critical_events_highlighted=timeline_data.get("critical_events_highlighted", []),
                generated_at=datetime.now(),
                model_used=response["model"],
                tokens_used=response["usage"]
            )

            logger.info(
                f"Timeline generated: {result.total_events} events, "
                f"{len(result.periods)} periods identified"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse timeline: {e}")
            raise ValueError("Invalid AI timeline format")
        except Exception as e:
            logger.error(f"Timeline generation failed: {e}")
            raise

    def _build_generation_prompt(self, request: TimelineGenerationRequest) -> str:
        """Build timeline generation prompt."""
        prompt_parts = [
            f"Create a chronological timeline for case {request.case_id}.",
            f"**TOTAL EVENTS:** {len(request.events)}"
        ]

        if request.case_context:
            prompt_parts.extend([
                f"\n**CASE CONTEXT:**",
                request.case_context
            ])

        # Sort events chronologically
        sorted_events = sorted(request.events, key=lambda e: e.date)

        prompt_parts.append(f"\n**EVENTS (chronological):**")

        for i, event in enumerate(sorted_events, 1):
            severity_str = f" [{event.severity.value.upper()}]" if event.severity else ""
            prompt_parts.append(
                f"\n{i}. {event.date}{severity_str} - {event.event_type.value.upper()}: {event.title}"
            )
            prompt_parts.append(f"   {event.description}")
            if event.participants:
                prompt_parts.append(f"   Participants: {', '.join(event.participants)}")
            if event.evidence_ids:
                prompt_parts.append(f"   Evidence: {', '.join(event.evidence_ids)}")

        prompt_parts.append(
            "\nGenerate organized timeline with period analysis in JSON format as specified."
        )

        return "\n".join(prompt_parts)

    def _get_system_prompt(self) -> str:
        """Get system prompt for timeline generation."""

        return """You are an expert legal timeline analyst specializing in family law cases.

CRITICAL REQUIREMENTS:
1. Organize events chronologically
2. Identify patterns and escalation
3. Group events into meaningful periods/phases
4. Highlight critical incidents
5. Analyze frequency and timing
6. Create court-ready narrative
7. Note any gaps in timeline
8. Assess credibility of sequence

TIMELINE PERIODS:
Divide timeline into meaningful phases such as:
- "Pre-separation" - Before custody dispute began
- "Early conflict" - Initial custody issues
- "Escalation" - Worsening situation
- "Crisis" - Critical incidents
- "Recent" - Last 3-6 months

OUTPUT FORMAT (JSON):
{
    "date_range": {
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD"
    },
    "organized_events": [
        {
            "event_id": "1",
            "date": "YYYY-MM-DD",
            "type": "incident",
            "title": "Event title",
            "description": "Full description",
            "severity": "critical|high|moderate|low|info",
            "importance_note": "Why this matters in the case"
        }
    ],
    "periods": [
        {
            "period_name": "Escalation Phase",
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD",
            "summary": "Summary of this period",
            "key_events": ["event_id_1", "event_id_3"],
            "pattern_analysis": "What pattern emerged in this period"
        }
    ],
    "pattern_summary": "Overall pattern analysis across timeline",
    "escalation_analysis": "How situation escalated over time",
    "key_dates": [
        {
            "date": "YYYY-MM-DD",
            "significance": "Why this date is critical"
        }
    ],
    "frequency_analysis": "Analysis of event frequency and clustering",
    "visual_timeline_description": "Description for creating visual timeline",
    "narrative_summary": "2-3 paragraph chronological narrative for court",
    "opening_statement_timeline": "Timeline summary for opening statement",
    "critical_events_highlighted": ["event_id_2", "event_id_5"]
}

IMPORTANT:
- Be objective and evidence-based
- Identify both positive and negative patterns
- Note correlations (e.g., visitation days vs incidents)
- Highlight escalation or improvement
- Consider child's developmental timeline
- Use clear, professional language
- Focus on what timeline reveals about child safety
"""

    async def quick_timeline(
        self,
        case_id: str,
        event_descriptions: List[Dict[str, str]],
        case_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Quick timeline from simple event descriptions.

        Args:
            case_id: Case identifier
            event_descriptions: List of {"date": "YYYY-MM-DD", "description": "..."}
            case_context: Brief case summary

        Returns:
            Simple timeline with narrative
        """
        # Convert to TimelineEvent objects
        events = []
        for i, event_desc in enumerate(event_descriptions, 1):
            events.append(TimelineEvent(
                event_id=str(i),
                date=event_desc.get("date", ""),
                event_type=EventType.INCIDENT,
                title=event_desc.get("description", "")[:50],
                description=event_desc.get("description", "")
            ))

        request = TimelineGenerationRequest(
            case_id=case_id,
            events=events,
            case_context=case_context
        )

        result = await self.generate_timeline(request)

        return {
            "total_events": result.total_events,
            "date_range": result.date_range,
            "periods": len(result.periods),
            "narrative_summary": result.narrative_summary,
            "pattern_summary": result.pattern_summary
        }
