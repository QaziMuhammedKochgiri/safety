"""
Timeline Analyzer
Creates comprehensive timeline of all communications
"""

from typing import Dict, List
from datetime import datetime

class TimelineAnalyzer:
    """Create and analyze communication timeline"""
    
    async def create_timeline(
        self,
        whatsapp_data: Dict,
        telegram_data: Dict,
        sms_data: Dict,
        signal_data: Dict
    ) -> List[Dict]:
        """
        Create comprehensive timeline from all sources
        
        Args:
            whatsapp_data: WhatsApp messages
            telegram_data: Telegram messages
            sms_data: SMS messages and calls
            signal_data: Signal messages
            
        Returns:
            Sorted timeline of all events
        """
        timeline = []
        
        # Add WhatsApp messages
        for msg in whatsapp_data.get("messages", []):
            timeline.append({
                "timestamp": msg.get("timestamp"),
                "source": "WhatsApp",
                "type": "message",
                "contact": msg.get("contact"),
                "from_me": msg.get("from_me"),
                "content_preview": self._truncate(msg.get("content", ""), 100),
                "has_media": bool(msg.get("media_url")),
                "location": self._format_location(msg.get("latitude"), msg.get("longitude")),
                "deleted": False
            })
        
        # Add deleted WhatsApp messages
        for msg in whatsapp_data.get("deleted", []):
            timeline.append({
                "timestamp": msg.get("timestamp"),
                "source": "WhatsApp",
                "type": "message",
                "content_preview": "[DELETED MESSAGE DETECTED]",
                "deleted": True,
                "recovery_info": msg.get("info")
            })
        
        # Add Telegram messages
        for msg in telegram_data.get("messages", []):
            timeline.append({
                "timestamp": msg.get("timestamp"),
                "source": "Telegram",
                "type": "message",
                "user_id": msg.get("user_id"),
                "outgoing": msg.get("outgoing"),
                "content_preview": self._truncate(msg.get("content", ""), 100),
                "read": msg.get("read"),
                "deleted": False
            })
        
        # Add SMS messages
        for msg in sms_data.get("messages", []):
            timeline.append({
                "timestamp": msg.get("timestamp"),
                "source": "SMS",
                "type": "sms",
                "address": msg.get("address"),
                "message_type": msg.get("type"),
                "content_preview": self._truncate(msg.get("content", ""), 100),
                "read": msg.get("read"),
                "deleted": False
            })
        
        # Add Call logs
        for call in sms_data.get("calls", []):
            timeline.append({
                "timestamp": call.get("timestamp"),
                "source": "Phone",
                "type": "call",
                "number": call.get("number"),
                "name": call.get("name"),
                "call_type": call.get("type"),
                "duration": call.get("duration"),
                "duration_formatted": self._format_duration(call.get("duration")),
                "deleted": False
            })
        
        # Add Signal messages
        for msg in signal_data.get("messages", []):
            timeline.append({
                "timestamp": msg.get("date_sent"),
                "source": "Signal",
                "type": "message",
                "address": msg.get("address"),
                "content_preview": self._truncate(msg.get("content", ""), 100),
                "read": msg.get("read"),
                "deleted": False
            })
        
        # Sort by timestamp (descending - newest first)
        timeline.sort(key=lambda x: x.get("timestamp", 0) or 0, reverse=True)
        
        return timeline
    
    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length"""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    def _format_location(self, lat, lon) -> str:
        """Format GPS coordinates"""
        if lat and lon:
            return f"{lat:.6f}, {lon:.6f}"
        return None
    
    def _format_duration(self, seconds) -> str:
        """Format call duration"""
        if not seconds:
            return "0s"
        
        minutes = seconds // 60
        secs = seconds % 60
        
        if minutes > 0:
            return f"{minutes}m {secs}s"
        return f"{secs}s"
    
    async def analyze_patterns(self, timeline: List[Dict]) -> Dict:
        """
        Analyze communication patterns
        
        Returns:
            Pattern analysis including frequency, peak times, etc.
        """
        if not timeline:
            return {}
        
        # Count by source
        by_source = {}
        for event in timeline:
            source = event.get("source")
            by_source[source] = by_source.get(source, 0) + 1
        
        # Count by hour of day
        by_hour = {}
        for event in timeline:
            timestamp = event.get("timestamp")
            if timestamp:
                dt = datetime.fromtimestamp(timestamp)
                hour = dt.hour
                by_hour[hour] = by_hour.get(hour, 0) + 1
        
        # Find peak hour
        peak_hour = max(by_hour, key=by_hour.get) if by_hour else None
        
        return {
            "total_events": len(timeline),
            "by_source": by_source,
            "by_hour": by_hour,
            "peak_hour": peak_hour,
            "date_range": {
                "earliest": min((e.get("timestamp") for e in timeline if e.get("timestamp")), default=None),
                "latest": max((e.get("timestamp") for e in timeline if e.get("timestamp")), default=None)
            }
        }
