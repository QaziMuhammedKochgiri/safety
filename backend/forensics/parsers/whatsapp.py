"""
WhatsApp Database Parser
Parses msgstore.db (WhatsApp SQLite database)
"""

import sqlite3
from pathlib import Path
from typing import Dict, List
from datetime import datetime

class WhatsAppParser:
    """Parse WhatsApp msgstore.db database"""
    
    async def parse_database(self, db_path: Path) -> Dict:
        """
        Parse WhatsApp database and extract all messages
        
        Args:
            db_path: Path to msgstore.db
            
        Returns:
            Dict with messages, deleted, contacts, media
        """
        if not db_path.exists():
            return {
                "messages": [],
                "deleted": [],
                "contacts": [],
                "media": []
            }
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Parse messages
        messages = self._parse_messages(cursor)
        
        # Parse deleted messages (simplified)
        deleted = self._parse_deleted_messages(cursor, db_path)
        
        # Parse contacts
        contacts = self._parse_contacts(cursor)
        
        # Parse media
        media = self._parse_media(cursor)
        
        conn.close()
        
        return {
            "messages": messages,
            "deleted": deleted,
            "contacts": contacts,
            "media": media
        }
    
    def _parse_messages(self, cursor) -> List[Dict]:
        """Parse regular messages from WhatsApp database"""
        
        # Try different WhatsApp database schemas
        # Older versions use 'messages' table
        # Newer versions might use 'message' table
        
        queries = [
            # Schema 1: Older WhatsApp
            """
            SELECT 
                _id,
                key_remote_jid as contact,
                key_from_me,
                data as content,
                timestamp,
                media_url,
                media_mime_type,
                media_size,
                latitude,
                longitude
            FROM messages
            ORDER BY timestamp DESC
            LIMIT 1000
            """,
            # Schema 2: Alternative
            """
            SELECT 
                _id,
                remote_resource as contact,
                from_me,
                text_data as content,
                timestamp,
                NULL as media_url,
                NULL as media_mime_type,
                NULL as media_size,
                NULL as latitude,
                NULL as longitude
            FROM message
            ORDER BY timestamp DESC
            LIMIT 1000
            """
        ]
        
        messages = []
        
        for query in queries:
            try:
                cursor.execute(query)
                rows = cursor.fetchall()
                
                for row in rows:
                    # Convert timestamp (WhatsApp uses milliseconds)
                    timestamp = row[4]
                    if timestamp and timestamp > 1000000000000:
                        # Milliseconds
                        timestamp = timestamp // 1000
                    
                    messages.append({
                        "id": row[0],
                        "contact": row[1] if row[1] else "Unknown",
                        "from_me": bool(row[2]),
                        "content": row[3] if row[3] else "[Media/No text]",
                        "timestamp": timestamp,
                        "media_url": row[5],
                        "media_type": row[6],
                        "media_size": row[7],
                        "latitude": row[8],
                        "longitude": row[9]
                    })
                
                if messages:
                    break  # Found messages, stop trying other queries
                    
            except sqlite3.Error as e:
                # Try next query
                continue
        
        return messages
    
    def _parse_deleted_messages(self, cursor, db_path: Path) -> List[Dict]:
        """
        Parse deleted messages (simplified version)
        Real implementation would do deep SQLite forensics
        """
        deleted = []
        
        # Check for WAL file (Write-Ahead Log)
        wal_path = Path(str(db_path) + "-wal")
        
        if wal_path.exists():
            deleted.append({
                "info": f"WAL file found ({wal_path.stat().st_size} bytes)",
                "recovery_possible": True,
                "note": "Deleted message recovery is possible through WAL analysis"
            })
        
        # Check for freelist pages
        try:
            cursor.execute("PRAGMA freelist_count")
            freelist_count = cursor.fetchone()[0]
            
            if freelist_count > 0:
                deleted.append({
                    "info": f"{freelist_count} freelist pages found",
                    "recovery_possible": True,
                    "note": "Potential deleted messages in SQLite freelists"
                })
        except:
            pass
        
        return deleted
    
    def _parse_contacts(self, cursor) -> List[Dict]:
        """Parse contacts from WhatsApp"""
        
        queries = [
            # Try wa_contacts table
            """
            SELECT DISTINCT
                jid,
                display_name,
                number
            FROM wa_contacts
            LIMIT 500
            """,
            # Alternative: Extract from messages
            """
            SELECT DISTINCT
                key_remote_jid as jid,
                NULL as display_name,
                NULL as number
            FROM messages
            WHERE key_remote_jid IS NOT NULL
            LIMIT 500
            """
        ]
        
        contacts = []
        
        for query in queries:
            try:
                cursor.execute(query)
                rows = cursor.fetchall()
                
                for row in rows:
                    contacts.append({
                        "jid": row[0],
                        "name": row[1] if len(row) > 1 else None,
                        "number": row[2] if len(row) > 2 else None
                    })
                
                if contacts:
                    break
                    
            except sqlite3.Error:
                continue
        
        return contacts
    
    def _parse_media(self, cursor) -> List[Dict]:
        """Parse media files metadata"""
        
        query = """
            SELECT 
                _id,
                media_url,
                media_mime_type,
                media_size
            FROM messages
            WHERE media_url IS NOT NULL
            LIMIT 500
        """
        
        media = []
        
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                media.append({
                    "id": row[0],
                    "url": row[1],
                    "type": row[2],
                    "size": row[3]
                })
        except:
            pass
        
        return media
