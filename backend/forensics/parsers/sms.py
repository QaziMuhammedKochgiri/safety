"""
SMS and Call Logs Parser
Parses mmssms.db (Android telephony database)
"""

import sqlite3
from pathlib import Path
from typing import Dict, List
from datetime import datetime

class SMSParser:
    """Parse Android SMS and Call Logs database"""
    
    async def parse_database(self, db_path: Path) -> Dict:
        """
        Parse SMS/MMS database and call logs
        
        Args:
            db_path: Path to mmssms.db or similar
            
        Returns:
            Dict with messages and calls
        """
        if not db_path.exists():
            return {
                "messages": [],
                "calls": []
            }
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Parse SMS messages
        messages = self._parse_sms(cursor)
        
        # Parse call logs
        calls = self._parse_calls(cursor)
        
        conn.close()
        
        return {
            "messages": messages,
            "calls": calls
        }
    
    def _parse_sms(self, cursor) -> List[Dict]:
        """Parse SMS messages"""
        
        query = """
            SELECT 
                _id,
                thread_id,
                address,
                person,
                date,
                date_sent,
                protocol,
                read,
                status,
                type,
                body,
                service_center
            FROM sms
            ORDER BY date DESC
            LIMIT 2000
        """
        
        messages = []
        
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                # Type: 1=received, 2=sent
                msg_type = "received" if row[9] == 1 else "sent" if row[9] == 2 else "unknown"
                
                messages.append({
                    "id": row[0],
                    "thread_id": row[1],
                    "address": row[2],  # Phone number
                    "person": row[3],
                    "timestamp": row[4] // 1000 if row[4] else None,  # Convert ms to seconds
                    "date_sent": row[5] // 1000 if row[5] else None,
                    "read": bool(row[7]),
                    "type": msg_type,
                    "content": row[10],
                    "service_center": row[11]
                })
        
        except sqlite3.Error as e:
            print(f"Error parsing SMS: {e}")
        
        return messages
    
    def _parse_calls(self, cursor) -> List[Dict]:
        """Parse call logs from separate database or table"""
        
        # Try to find call logs
        queries = [
            # Standard Android call log
            """
            SELECT 
                _id,
                number,
                date,
                duration,
                type,
                name,
                numbertype,
                numberlabel
            FROM calls
            ORDER BY date DESC
            LIMIT 1000
            """,
            # Alternative schema
            """
            SELECT 
                _id,
                number,
                date,
                duration,
                type,
                name,
                NULL as numbertype,
                NULL as numberlabel
            FROM call_log
            ORDER BY date DESC
            LIMIT 1000
            """
        ]
        
        calls = []
        
        for query in queries:
            try:
                cursor.execute(query)
                rows = cursor.fetchall()
                
                for row in rows:
                    # Type: 1=incoming, 2=outgoing, 3=missed
                    call_type = "incoming" if row[4] == 1 else "outgoing" if row[4] == 2 else "missed" if row[4] == 3 else "unknown"
                    
                    calls.append({
                        "id": row[0],
                        "number": row[1],
                        "timestamp": row[2] // 1000 if row[2] else None,
                        "duration": row[3],  # seconds
                        "type": call_type,
                        "name": row[5],
                        "number_type": row[6],
                        "number_label": row[7]
                    })
                
                if calls:
                    break
                    
            except sqlite3.Error:
                continue
        
        return calls
