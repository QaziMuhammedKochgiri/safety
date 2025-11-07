"""
Media File Analyzer
Analyzes media files (images, videos, audio)
"""

from pathlib import Path
from typing import Dict, List
import mimetypes

class MediaAnalyzer:
    """Analyze media files from communications"""
    
    async def analyze_media(
        self,
        whatsapp_data: Dict,
        telegram_data: Dict,
        case_dir: Path
    ) -> Dict:
        """
        Analyze media files from all sources
        
        Returns:
            Media analysis with counts, types, sizes
        """
        media_files = []
        
        # Collect WhatsApp media
        for media in whatsapp_data.get("media", []):
            media_files.append({
                "source": "WhatsApp",
                "type": media.get("type"),
                "size": media.get("size"),
                "url": media.get("url"),
                "message_id": media.get("id")
            })
        
        # Collect Telegram media
        for media in telegram_data.get("media", []):
            media_files.append({
                "source": "Telegram",
                "type": media.get("type"),
                "data": media.get("data"),
                "message_id": media.get("message_id")
            })
        
        # Analyze by type
        by_type = {}
        total_size = 0
        
        for media in media_files:
            media_type = self._categorize_media_type(media.get("type"))
            by_type[media_type] = by_type.get(media_type, 0) + 1
            
            if media.get("size"):
                total_size += media.get("size")
        
        return {
            "total_files": len(media_files),
            "by_type": by_type,
            "total_size": total_size,
            "total_size_formatted": self._format_size(total_size),
            "files": media_files[:100]  # First 100 files
        }
    
    def _categorize_media_type(self, mime_type: str) -> str:
        """Categorize media type"""
        if not mime_type:
            return "unknown"
        
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type.startswith("video/"):
            return "video"
        elif mime_type.startswith("audio/"):
            return "audio"
        elif mime_type.startswith("application/pdf"):
            return "document"
        else:
            return "other"
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
