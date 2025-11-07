"""
SafeChild Forensics Engine V2
100% Open Source - Uses Sleuth Kit (TSK) under Apache 2.0
Phase 2: Complete implementation with all parsers and analyzers
"""

import pytsk3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import hashlib
import json

from .parsers import WhatsAppParser, TelegramParser, SMSParser, SignalParser
from .analyzers import TimelineAnalyzer, ContactNetworkAnalyzer, MediaAnalyzer
from .reporters import PDFReportGenerator

class SafeChildForensicsEngine:
    """
    Main forensics engine using Sleuth Kit (TSK)
    Provides comprehensive mobile device forensic analysis
    """
    
    def __init__(self):
        self.tsk_version = pytsk3.TSK_VERSION_STR
        self.output_base = Path("/app/forensic_outputs")
        self.output_base.mkdir(exist_ok=True, parents=True)
        
        # Initialize parsers
        self.whatsapp_parser = WhatsAppParser()
        self.telegram_parser = TelegramParser()
        self.sms_parser = SMSParser()
        self.signal_parser = SignalParser()
        
        # Initialize analyzers
        self.timeline_analyzer = TimelineAnalyzer()
        self.contact_analyzer = ContactNetworkAnalyzer()
        self.media_analyzer = MediaAnalyzer()
        
        # Initialize reporters
        self.pdf_reporter = PDFReportGenerator()
        
        print(f"✅ SafeChild Forensics Engine V2 initialized (TSK {self.tsk_version})")
        print(f"   📱 Parsers: WhatsApp, Telegram, SMS, Signal")
        print(f"   📊 Analyzers: Timeline, Contacts, Media")
        print(f"   📄 Reporters: PDF, TXT")
        
    async def analyze_android_backup(
        self,
        backup_file: Path,
        case_id: str,
        client_info: Dict
    ) -> Dict:
        """
        Comprehensive Android backup analysis
        
        Args:
            backup_file: Path to backup file (.ab, .tar, or SQLite .db)
            case_id: Unique case identifier
            client_info: Client information dict
            
        Returns:
            Complete analysis results with reports
        """
        case_dir = self.output_base / case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*70}")
        print(f"🔬 SafeChild Forensic Analysis V2 - Started")
        print(f"{'='*70}")
        print(f"Case ID: {case_id}")
        print(f"Client: {client_info.get('email', 'Unknown')}")
        print(f"File: {backup_file.name} ({self._format_size(backup_file.stat().st_size)})")
        print(f"{'='*70}\n")
        
        try:
            # Step 1: Hash verification
            print("[1/10] 🔐 Computing file hash...")
            file_hash = self._compute_hash(backup_file)
            print(f"       SHA-256: {file_hash[:32]}...")
            
            # Step 2: Extract data
            print("[2/10] 📂 Extracting backup data...")
            extraction_result = await self._extract_data(backup_file, case_dir)
            print(f"       Method: {extraction_result.get('method')}")
            
            # Step 3: Parse WhatsApp
            print("[3/10] 💬 Analyzing WhatsApp...")
            whatsapp_data = await self._analyze_whatsapp(case_dir)
            print(f"       Messages: {len(whatsapp_data['messages'])}")
            print(f"       Contacts: {len(whatsapp_data['contacts'])}")
            print(f"       Media: {len(whatsapp_data['media'])}")
            
            # Step 4: Parse Telegram
            print("[4/10] ✈️  Analyzing Telegram...")
            telegram_data = await self._analyze_telegram(case_dir)
            print(f"       Messages: {len(telegram_data['messages'])}")
            print(f"       Contacts: {len(telegram_data['contacts'])}")
            
            # Step 5: Parse SMS & Calls
            print("[5/10] 📞 Analyzing SMS & Call Logs...")
            sms_data = await self._analyze_sms(case_dir)
            print(f"       SMS: {len(sms_data['messages'])}")
            print(f"       Calls: {len(sms_data['calls'])}")
            
            # Step 6: Parse Signal
            print("[6/10] 🔒 Analyzing Signal...")
            signal_data = await self._analyze_signal(case_dir)
            print(f"       Messages: {len(signal_data['messages'])}")
            print(f"       Contacts: {len(signal_data['contacts'])}")
            
            # Step 7: Create timeline
            print("[7/10] ⏱️  Creating comprehensive timeline...")
            timeline = await self.timeline_analyzer.create_timeline(
                whatsapp_data, telegram_data, sms_data, signal_data
            )
            print(f"       Total events: {len(timeline)}")
            
            # Step 8: Analyze contact network
            print("[8/10] 👥 Analyzing contact network...")
            contact_network = await self.contact_analyzer.analyze_network(
                whatsapp_data, telegram_data, sms_data, signal_data
            )
            print(f"       Total contacts: {contact_network['total_contacts']}")
            
            # Step 9: Analyze media
            print("[9/10] 📷 Analyzing media files...")
            media_analysis = await self.media_analyzer.analyze_media(
                whatsapp_data, telegram_data, case_dir
            )
            print(f"       Total files: {media_analysis['total_files']}")
            print(f"       Total size: {media_analysis['total_size_formatted']}")
            
            # Step 10: Generate comprehensive report
            print("[10/10] 📄 Generating comprehensive report...")
            report_data = {
                "case_id": case_id,
                "client": client_info,
                "file_hash": file_hash,
                "file_name": backup_file.name,
                "file_size": backup_file.stat().st_size,
                "analysis_date": datetime.utcnow().isoformat(),
                "tsk_version": self.tsk_version,
                "whatsapp": whatsapp_data,
                "telegram": telegram_data,
                "sms": sms_data,
                "signal": signal_data,
                "timeline": timeline,
                "contact_network": contact_network,
                "media_analysis": media_analysis
            }
            
            report_path = await self._generate_comprehensive_report(report_data, case_dir)
            
            statistics = {
                "whatsapp_messages": len(whatsapp_data['messages']),
                "whatsapp_deleted": len(whatsapp_data['deleted']),
                "whatsapp_contacts": len(whatsapp_data['contacts']),
                "whatsapp_media": len(whatsapp_data['media']),
                "telegram_messages": len(telegram_data['messages']),
                "telegram_contacts": len(telegram_data['contacts']),
                "sms_messages": len(sms_data['messages']),
                "call_logs": len(sms_data['calls']),
                "signal_messages": len(signal_data['messages']),
                "signal_contacts": len(signal_data['contacts']),
                "timeline_events": len(timeline),
                "total_contacts": contact_network['total_contacts'],
                "media_files": media_analysis['total_files']
            }
            
            print(f"\n{'='*70}")
            print(f"✅ Analysis Completed Successfully!")
            print(f"{'='*70}")
            print(f"Total Messages: {statistics['whatsapp_messages'] + statistics['telegram_messages'] + statistics['sms_messages'] + statistics['signal_messages']}")
            print(f"Total Contacts: {statistics['total_contacts']}")
            print(f"Timeline Events: {statistics['timeline_events']}")
            print(f"Media Files: {statistics['media_files']}")
            print(f"Report: {report_path}")
            print(f"{'='*70}\n")
            
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
        """Extract data from backup file"""
        file_ext = backup_file.suffix.lower()
        
        if file_ext == '.db':
            # Direct SQLite database
            extracted_db = case_dir / backup_file.name
            import shutil
            shutil.copy(backup_file, extracted_db)
            return {"method": "direct_db"}
        
        elif file_ext in ['.tar', '.gz', '.tgz']:
            # Extract tar archive
            import tarfile
            extract_dir = case_dir / "extracted"
            extract_dir.mkdir(exist_ok=True)
            with tarfile.open(backup_file, 'r:*') as tar:
                tar.extractall(extract_dir)
            return {"method": "tar_extraction", "extracted_dir": extract_dir}
        
        elif file_ext == '.ab':
            return {"method": "android_backup"}
        
        else:
            return {"method": "unknown"}
    
    async def _analyze_whatsapp(self, case_dir: Path) -> Dict:
        """Analyze WhatsApp data"""
        possible_paths = [
            case_dir / "whatsapp_msgstore.db",
            case_dir / "msgstore.db",
            case_dir / "extracted" / "apps" / "com.whatsapp" / "databases" / "msgstore.db",
        ]
        
        for path in possible_paths:
            if path.exists():
                return await self.whatsapp_parser.parse_database(path)
        
        return {"messages": [], "deleted": [], "contacts": [], "media": []}
    
    async def _analyze_telegram(self, case_dir: Path) -> Dict:
        """Analyze Telegram data"""
        possible_paths = [
            case_dir / "telegram_cache4.db",
            case_dir / "cache4.db",
            case_dir / "extracted" / "apps" / "org.telegram.messenger" / "databases" / "cache4.db",
        ]
        
        for path in possible_paths:
            if path.exists():
                return await self.telegram_parser.parse_database(path)
        
        return {"messages": [], "contacts": [], "chats": [], "media": []}
    
    async def _analyze_sms(self, case_dir: Path) -> Dict:
        """Analyze SMS and call logs"""
        possible_paths = [
            case_dir / "mmssms.db",
            case_dir / "extracted" / "apps" / "com.android.providers.telephony" / "databases" / "mmssms.db",
        ]
        
        for path in possible_paths:
            if path.exists():
                return await self.sms_parser.parse_database(path)
        
        return {"messages": [], "calls": []}
    
    async def _analyze_signal(self, case_dir: Path) -> Dict:
        """Analyze Signal data"""
        possible_paths = [
            case_dir / "signal.db",
            case_dir / "extracted" / "apps" / "org.thoughtcrime.securesms" / "databases" / "signal.db",
        ]
        
        for path in possible_paths:
            if path.exists():
                return await self.signal_parser.parse_database(path)
        
        return {"messages": [], "contacts": []}
    
    async def _generate_comprehensive_report(self, data: Dict, case_dir: Path) -> Dict:
        """Generate comprehensive forensic reports (TXT + PDF)"""
        report_txt_path = case_dir / f"SafeChild_Comprehensive_Report_{data['case_id']}.txt"
        report_pdf_path = case_dir / f"SafeChild_Comprehensive_Report_{data['case_id']}.pdf"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            # Header
            f.write("="*80 + "\n")
            f.write("SafeChild Hukuk Bürosu - Comprehensive Forensic Analysis Report\n")
            f.write("="*80 + "\n\n")
            
            # Case Information
            f.write("CASE INFORMATION\n")
            f.write("-"*80 + "\n")
            f.write(f"Case ID: {data['case_id']}\n")
            f.write(f"Client: {data['client'].get('email', 'N/A')}\n")
            f.write(f"Analysis Date: {data['analysis_date']}\n")
            f.write(f"File: {data['file_name']}\n")
            f.write(f"File Size: {self._format_size(data['file_size'])}\n")
            f.write(f"SHA-256 Hash: {data['file_hash']}\n")
            f.write(f"TSK Version: {data['tsk_version']}\n\n")
            
            # Summary Statistics
            f.write("="*80 + "\n")
            f.write("SUMMARY STATISTICS\n")
            f.write("-"*80 + "\n")
            f.write(f"WhatsApp Messages: {len(data['whatsapp']['messages'])}\n")
            f.write(f"WhatsApp Deleted: {len(data['whatsapp']['deleted'])}\n")
            f.write(f"Telegram Messages: {len(data['telegram']['messages'])}\n")
            f.write(f"SMS Messages: {len(data['sms']['messages'])}\n")
            f.write(f"Call Logs: {len(data['sms']['calls'])}\n")
            f.write(f"Signal Messages: {len(data['signal']['messages'])}\n")
            f.write(f"Total Timeline Events: {len(data['timeline'])}\n")
            f.write(f"Total Contacts: {data['contact_network']['total_contacts']}\n")
            f.write(f"Total Media Files: {data['media_analysis']['total_files']}\n\n")
            
            # WhatsApp Details
            f.write("="*80 + "\n")
            f.write("WHATSAPP ANALYSIS\n")
            f.write("-"*80 + "\n")
            if data['whatsapp']['messages']:
                f.write("Recent Messages (last 10):\n\n")
                for msg in data['whatsapp']['messages'][:10]:
                    f.write(f"  [{datetime.fromtimestamp(msg.get('timestamp', 0))}]\n")
                    f.write(f"  Contact: {msg.get('contact')}\n")
                    f.write(f"  From Me: {msg.get('from_me')}\n")
                    f.write(f"  Content: {msg.get('content', 'N/A')[:200]}\n")
                    if msg.get('latitude') and msg.get('longitude'):
                        f.write(f"  Location: {msg['latitude']:.6f}, {msg['longitude']:.6f}\n")
                    f.write("  " + "-"*70 + "\n\n")
            
            # Timeline
            f.write("="*80 + "\n")
            f.write("COMMUNICATION TIMELINE\n")
            f.write("-"*80 + "\n")
            f.write(f"Total Events: {len(data['timeline'])}\n\n")
            for event in data['timeline'][:50]:
                ts = event.get('timestamp')
                dt_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') if ts else 'N/A'
                f.write(f"[{dt_str}] {event.get('source')} - {event.get('type')}\n")
                if event.get('deleted'):
                    f.write("  ⚠️  DELETED MESSAGE\n")
                f.write(f"  {event.get('content_preview', '')}\n\n")
            
            # Contact Network
            f.write("="*80 + "\n")
            f.write("CONTACT NETWORK ANALYSIS\n")
            f.write("-"*80 + "\n")
            f.write(f"Total Contacts: {data['contact_network']['total_contacts']}\n")
            f.write(f"Top 10 Contacts:\n\n")
            for contact_id in data['contact_network']['top_contacts']:
                contact = data['contact_network']['contacts'].get(contact_id, {})
                f.write(f"  {contact_id}: {contact.get('name', 'Unknown')}\n")
                f.write(f"    Platforms: {', '.join(contact.get('platforms', []))}\n")
                f.write(f"    Messages: {contact.get('message_count')}\n")
                f.write(f"    Calls: {contact.get('call_count')}\n")
                f.write(f"    Total Interactions: {contact.get('total_interactions')}\n\n")
            
            # Media Analysis
            f.write("="*80 + "\n")
            f.write("MEDIA FILE ANALYSIS\n")
            f.write("-"*80 + "\n")
            f.write(f"Total Files: {data['media_analysis']['total_files']}\n")
            f.write(f"Total Size: {data['media_analysis']['total_size_formatted']}\n")
            f.write(f"By Type:\n")
            for media_type, count in data['media_analysis']['by_type'].items():
                f.write(f"  {media_type}: {count}\n")
            f.write("\n")
            
            # Footer
            f.write("="*80 + "\n")
            f.write("End of Comprehensive Report\n")
            f.write("="*80 + "\n")
        
        return report_path
    
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
