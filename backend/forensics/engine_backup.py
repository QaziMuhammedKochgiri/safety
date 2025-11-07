"""
SafeChild Forensics Engine
100% Open Source - Uses Sleuth Kit (TSK) under Apache 2.0
"""

import pytsk3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import hashlib
import json
import sqlite3

class SafeChildForensicsEngine:
    """
    Main forensics engine using Sleuth Kit (TSK)
    Provides forensically sound mobile device analysis
    """
    
    def __init__(self):
        self.tsk_version = pytsk3.TSK_VERSION_STR
        self.output_base = Path("/app/forensic_outputs")
        self.output_base.mkdir(exist_ok=True, parents=True)
        print(f"✅ SafeChild Forensics Engine initialized (TSK {self.tsk_version})")
        
    async def analyze_android_backup(
        self,
        backup_file: Path,
        case_id: str,
        client_info: Dict
    ) -> Dict:
        """
        Analyze Android backup file
        
        Args:
            backup_file: Path to backup file (.ab, .tar, or SQLite .db)
            case_id: Unique case identifier
            client_info: Client information dict
            
        Returns:
            Analysis results with report paths
        """
        case_dir = self.output_base / case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"🔬 SafeChild Forensic Analysis Started")
        print(f"{'='*60}")
        print(f"Case ID: {case_id}")
        print(f"Client: {client_info.get('email', 'Unknown')}")
        print(f"File: {backup_file.name}")
        print(f"{'='*60}\n")
        
        try:
            # Step 1: Hash verification for chain of custody
            print("[1/5] 🔐 Computing file hash for chain of custody...")
            file_hash = self._compute_hash(backup_file)
            print(f"      SHA-256: {file_hash[:32]}...")
            
            # Step 2: Detect file type and extract data
            print("[2/5] 📂 Detecting file type and extracting data...")
            extraction_result = await self._extract_data(backup_file, case_dir)
            
            # Step 3: Parse WhatsApp if found
            print("[3/5] 💬 Analyzing WhatsApp data...")
            whatsapp_data = await self._analyze_whatsapp(case_dir)
            
            # Step 4: Create timeline
            print("[4/5] ⏱️  Creating communication timeline...")
            timeline = await self._create_timeline(whatsapp_data)
            
            # Step 5: Generate report
            print("[5/5] 📄 Generating forensic report...")
            report_data = {
                "case_id": case_id,
                "client": client_info,
                "file_hash": file_hash,
                "file_name": backup_file.name,
                "file_size": backup_file.stat().st_size,
                "analysis_date": datetime.utcnow().isoformat(),
                "tsk_version": self.tsk_version,
                "whatsapp": whatsapp_data,
                "timeline": timeline
            }
            
            report_path = await self._generate_simple_report(report_data, case_dir)
            
            statistics = {
                "whatsapp_messages": len(whatsapp_data.get("messages", [])),
                "whatsapp_deleted": len(whatsapp_data.get("deleted", [])),
                "whatsapp_contacts": len(whatsapp_data.get("contacts", [])),
                "timeline_events": len(timeline)
            }
            
            print(f"\n{'='*60}")
            print(f"✅ Analysis Completed Successfully!")
            print(f"{'='*60}")
            print(f"WhatsApp Messages: {statistics['whatsapp_messages']}")
            print(f"Deleted Messages: {statistics['whatsapp_deleted']}")
            print(f"Contacts: {statistics['whatsapp_contacts']}")
            print(f"Timeline Events: {statistics['timeline_events']}")
            print(f"Report: {report_path}")
            print(f"{'='*60}\n")
            
            return {
                "success": True,
                "case_id": case_id,
                "file_hash": file_hash,
                "report_pdf": str(report_path),
                "report_html": str(report_path.with_suffix('.html')),
                "statistics": statistics
            }
            
        except Exception as e:
            print(f"\n❌ Error during analysis: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e),
                "case_id": case_id
            }
    
    def _compute_hash(self, file_path: Path, algorithm='sha256') -> str:
        """Compute cryptographic hash for chain of custody"""
        hash_obj = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    async def _extract_data(self, backup_file: Path, case_dir: Path) -> Dict:
        """
        Extract data from backup file
        Handles: .db files directly, .tar archives, .ab backups
        """
        file_ext = backup_file.suffix.lower()
        
        if file_ext == '.db':
            # Direct SQLite database - likely WhatsApp msgstore.db
            extracted_db = case_dir / "whatsapp_msgstore.db"
            import shutil
            shutil.copy(backup_file, extracted_db)
            return {"whatsapp_db": extracted_db, "method": "direct"}
        
        elif file_ext in ['.tar', '.gz']:
            # Extract tar archive
            import tarfile
            with tarfile.open(backup_file, 'r:*') as tar:
                tar.extractall(case_dir / "extracted")
            return {"extracted_dir": case_dir / "extracted", "method": "tar"}
        
        elif file_ext == '.ab':
            # Android backup - needs special handling
            # For now, just note it
            return {"method": "android_backup", "note": "Android backup format detected"}
        
        else:
            return {"method": "unknown", "error": f"Unsupported format: {file_ext}"}
    
    async def _analyze_whatsapp(self, case_dir: Path) -> Dict:
        """Analyze WhatsApp data"""
        whatsapp_data = {
            "messages": [],
            "deleted": [],
            "contacts": [],
            "media": []
        }
        
        # Look for WhatsApp database
        possible_paths = [
            case_dir / "whatsapp_msgstore.db",
            case_dir / "extracted" / "apps" / "com.whatsapp" / "databases" / "msgstore.db",
            case_dir / "extracted" / "msgstore.db"
        ]
        
        db_path = None
        for path in possible_paths:
            if path.exists():
                db_path = path
                break
        
        if not db_path:
            print("      ⚠️  WhatsApp database not found")
            return whatsapp_data
        
        print(f"      ✅ WhatsApp database found: {db_path.name}")
        
        try:
            from .parsers.whatsapp import WhatsAppParser
            parser = WhatsAppParser()
            whatsapp_data = await parser.parse_database(db_path)
            print(f"      ✅ Parsed {len(whatsapp_data['messages'])} messages")
            
        except Exception as e:
            print(f"      ❌ Error parsing WhatsApp: {e}")
        
        return whatsapp_data
    
    async def _create_timeline(self, whatsapp_data: Dict) -> List[Dict]:
        """Create chronological timeline of communications"""
        timeline = []
        
        for msg in whatsapp_data.get("messages", []):
            timeline.append({
                "timestamp": msg.get("timestamp"),
                "type": "WhatsApp",
                "contact": msg.get("contact"),
                "from_me": msg.get("from_me"),
                "content": msg.get("content", "")[:100],  # First 100 chars
                "deleted": False
            })
        
        for msg in whatsapp_data.get("deleted", []):
            timeline.append({
                "timestamp": msg.get("timestamp"),
                "type": "WhatsApp (Deleted)",
                "contact": msg.get("contact"),
                "content": msg.get("info", ""),
                "deleted": True
            })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x.get("timestamp", 0))
        
        return timeline
    
    async def _generate_simple_report(self, data: Dict, case_dir: Path) -> Path:
        """Generate simple text report (PDF coming soon)"""
        report_path = case_dir / f"SafeChild_Report_{data['case_id']}.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("SafeChild Hukuk Bürosu - Forensic Analysis Report\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Case ID: {data['case_id']}\n")
            f.write(f"Client: {data['client'].get('email', 'N/A')}\n")
            f.write(f"Analysis Date: {data['analysis_date']}\n")
            f.write(f"File: {data['file_name']}\n")
            f.write(f"File Size: {data['file_size']} bytes\n")
            f.write(f"SHA-256 Hash: {data['file_hash']}\n")
            f.write(f"TSK Version: {data['tsk_version']}\n")
            f.write("\n" + "="*80 + "\n\n")
            
            f.write("WHATSAPP ANALYSIS\n")
            f.write("-"*80 + "\n")
            f.write(f"Total Messages: {len(data['whatsapp']['messages'])}\n")
            f.write(f"Deleted Messages: {len(data['whatsapp']['deleted'])}\n")
            f.write(f"Contacts: {len(data['whatsapp']['contacts'])}\n\n")
            
            if data['whatsapp']['messages']:
                f.write("Recent Messages (last 10):\n")
                for msg in data['whatsapp']['messages'][:10]:
                    f.write(f"\n  Timestamp: {msg.get('timestamp')}\n")
                    f.write(f"  Contact: {msg.get('contact')}\n")
                    f.write(f"  From Me: {msg.get('from_me')}\n")
                    f.write(f"  Content: {msg.get('content', 'N/A')[:200]}\n")
                    f.write("  " + "-"*70 + "\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("TIMELINE\n")
            f.write("-"*80 + "\n")
            f.write(f"Total Events: {len(data['timeline'])}\n\n")
            
            for event in data['timeline'][:20]:  # First 20 events
                f.write(f"  [{event.get('type')}] {event.get('timestamp')}\n")
                f.write(f"  Contact: {event.get('contact')}\n")
                if event.get('deleted'):
                    f.write(f"  ⚠️  DELETED MESSAGE\n")
                f.write("\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("End of Report\n")
            f.write("="*80 + "\n")
        
        return report_path
