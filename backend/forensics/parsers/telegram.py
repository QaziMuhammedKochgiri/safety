"""
Telegram Database Parser
Parses cache4.db (Telegram SQLite database)
"""

import sqlite3
from pathlib import Path
from typing import Dict, List
from datetime import datetime

class TelegramParser:
    """Parse Telegram cache4.db database"""
    
    async def parse_database(self, db_path: Path) -> Dict:
        """
        Parse Telegram database and extract all messages
        
        Args:
            db_path: Path to cache4.db
            
        Returns:
            Dict with messages, contacts, media
        """
        if not db_path.exists():
            return {
                "messages": [],
                "contacts": [],
                "chats": [],
                "media": []
            }
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Parse messages
        messages = self._parse_messages(cursor)
        
        # Parse contacts
        contacts = self._parse_contacts(cursor)
        
        # Parse chats
        chats = self._parse_chats(cursor)
        
        # Parse media
        media = self._parse_media(cursor)
        
        conn.close()
        
        return {
            "messages": messages,
            "contacts": contacts,
            "chats": chats,
            "media": media
        }
    
    def _parse_messages(self, cursor) -> List[Dict]:
        """Parse messages from Telegram database"""
        
        queries = [
            # Try messages table
            """
            SELECT 
                mid as id,
                uid as user_id,
                read_state,
                send_state,
                date,
                data as content,
                out as outgoing,
                media
            FROM messages
            ORDER BY date DESC
            LIMIT 1000
            """,
            # Alternative schema
            """
            SELECT 
                _id as id,
                peer_id as user_id,
                0 as read_state,
                0 as send_state,
                date,
                message as content,
                is_outgoing as outgoing,
                NULL as media
            FROM message
            ORDER BY date DESC
            LIMIT 1000
            """
        ]
        
        messages = []
        
        for query in queries:
            try:
                cursor.execute(query)
                rows = cursor.fetchall()
                
                for row in rows:
                    messages.append({
                        "id": row[0],
                        "user_id": row[1],
                        "read": bool(row[2]) if row[2] is not None else None,
                        "sent": bool(row[3]) if row[3] is not None else None,
                        "timestamp": row[4],
                        "content": row[5] if row[5] else "[Media/No text]",
                        "outgoing": bool(row[6]),
                        "media": row[7]
                    })
                
                if messages:
                    break
                    
            except sqlite3.Error as e:
                continue
        
        return messages
    
    def _parse_contacts(self, cursor) -> List[Dict]:
        """Parse contacts from Telegram"""
        
        queries = [
            """
            SELECT 
                uid,
                name,
                data
            FROM users
            LIMIT 500
            """,
            """
            SELECT 
                id,
                first_name || ' ' || last_name as name,
                username
            FROM contacts
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
                        "id": row[0],
                        "name": row[1],
                        "username": row[2] if len(row) > 2 else None
                    })
                
                if contacts:
                    break
                    
            except sqlite3.Error:
                continue
        
        return contacts
    
    def _parse_chats(self, cursor) -> List[Dict]:
        """Parse chat groups"""
        
        query = """
            SELECT 
                uid,
                name,
                data
            FROM chats
            LIMIT 200
        """
        
        chats = []
        
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                chats.append({
                    "id": row[0],
                    "name": row[1],
                    "data": row[2]
                })
        except:
            pass
        
        return chats
    
    def _parse_media(self, cursor) -> List[Dict]:
        """Parse media files"""
        
        query = """
            SELECT 
                mid,
                type,
                data
            FROM media_v2
            LIMIT 500
        """
        
        media = []
        
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                media.append({
                    "message_id": row[0],
                    "type": row[1],
                    "data": row[2]
                })
        except:
            pass
        
        return media
