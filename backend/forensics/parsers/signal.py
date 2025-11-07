"""
Signal Database Parser
Parses signal.db (Signal SQLite database)
"""

import sqlite3
from pathlib import Path
from typing import Dict, List

class SignalParser:
    """Parse Signal database"""
    
    async def parse_database(self, db_path: Path) -> Dict:
        """
        Parse Signal database and extract messages
        
        Args:
            db_path: Path to signal database
            
        Returns:
            Dict with messages and contacts
        """
        if not db_path.exists():
            return {
                "messages": [],
                "contacts": []
            }
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Parse messages
        messages = self._parse_messages(cursor)
        
        # Parse contacts
        contacts = self._parse_contacts(cursor)
        
        conn.close()
        
        return {
            "messages": messages,
            "contacts": contacts
        }
    
    def _parse_messages(self, cursor) -> List[Dict]:
        """Parse Signal messages"""
        
        queries = [
            # Signal schema
            """
            SELECT 
                _id,
                address,
                date_sent,
                date_received,
                body,
                read,
                thread_id,
                type
            FROM sms
            ORDER BY date_sent DESC
            LIMIT 1000
            """,
            # Alternative
            """
            SELECT 
                _id,
                recipient_id,
                date_sent,
                date_received,
                body,
                read,
                thread_id,
                type
            FROM message
            ORDER BY date_sent DESC
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
                        "address": row[1],
                        "date_sent": row[2],
                        "date_received": row[3],
                        "content": row[4] if row[4] else "[Media/No text]",
                        "read": bool(row[5]),
                        "thread_id": row[6],
                        "type": row[7]
                    })
                
                if messages:
                    break
                    
            except sqlite3.Error:
                continue
        
        return messages
    
    def _parse_contacts(self, cursor) -> List[Dict]:
        """Parse Signal contacts"""
        
        query = """
            SELECT 
                _id,
                phone,
                name,
                profile_name
            FROM recipient
            LIMIT 500
        """
        
        contacts = []
        
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                contacts.append({
                    "id": row[0],
                    "phone": row[1],
                    "name": row[2],
                    "profile_name": row[3]
                })
        except:
            pass
        
        return contacts
