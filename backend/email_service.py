import resend
from typing import List, Optional, Dict
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize Resend with API key
resend.api_key = os.environ.get('RESEND_API_KEY')

# Type mapping for display
TYPE_DISPLAY_NAMES = {
    "whatsapp": "WhatsApp Messages",
    "telegram": "Telegram Messages",
    "photos": "Photos & Media",
    "sms": "SMS Messages",
    "calls": "Call Logs",
    "any": "Any Evidence Files"
}

class EmailService:
    """Service for sending transactional emails through Resend."""
    
    @staticmethod
    def send_email(
        to: List[str],
        subject: str,
        html: str,
        text: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> Dict:
        """
        Send an email through Resend.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject line
            html: HTML content of the email
            text: Plain text content (optional)
            reply_to: Reply-to email address (optional)
            
        Returns:
            Dictionary containing success status and email ID or error
        """
        
        from_address = f"{os.environ.get('EMAIL_FROM_NAME', 'SafeChild Law')} <{os.environ.get('EMAIL_FROM_ADDRESS', 'info@safechild.mom')}>"
        
        try:
            params = {
                "from": from_address,
                "to": to if isinstance(to, list) else [to],
                "subject": subject,
                "html": html,
            }
            
            if text:
                params["text"] = text
            
            if reply_to:
                params["reply_to"] = reply_to
            
            # Send email through Resend
            response = resend.Emails.send(params)
            
            logger.info(f"Email sent successfully: {response.get('id')}")
            
            return {
                "success": True,
                "email_id": response.get("id"),
                "message": "Email sent successfully"
            }
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to send email"
            }
    
    @staticmethod
    def send_meeting_confirmation(
        recipient_email: str,
        recipient_name: str,
        meeting_title: str,
        meeting_date: str,
        meeting_time: str,
        meeting_url: Optional[str] = None,
        meeting_id: Optional[str] = None
    ) -> Dict:
        """Send a meeting confirmation email."""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">SafeChild Law</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0;">Rechtsanwaltskanzlei</p>
            </div>
            
            <div style="background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #1e40af; margin-top: 0;">Video-Konsultation Bestätigt</h2>
                
                <p style="font-size: 16px;">Hallo {recipient_name},</p>
                
                <p style="font-size: 16px;">Ihre Video-Konsultation wurde erfolgreich bestätigt:</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2563eb;">
                    <p style="margin: 5px 0;"><strong>Beratung:</strong> {meeting_title}</p>
                    <p style="margin: 5px 0;"><strong>Datum:</strong> {meeting_date}</p>
                    <p style="margin: 5px 0;"><strong>Uhrzeit:</strong> {meeting_time}</p>
                    {f'<p style="margin: 5px 0;"><strong>Meeting ID:</strong> {meeting_id}</p>' if meeting_id else ''}
                </div>
                
                {f'''
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{meeting_url}" style="background: #2563eb; color: white; padding: 15px 40px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                        Zum Video-Meeting
                    </a>
                </div>
                ''' if meeting_url else ''}
                
                <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <p style="margin: 0; font-size: 14px;"><strong>Wichtig:</strong> Bitte stellen Sie sicher, dass Sie eine stabile Internetverbindung haben und Ihre Kamera und Ihr Mikrofon funktionieren.</p>
                </div>
                
                <p style="font-size: 16px;">Bei Fragen stehen wir Ihnen jederzeit zur Verfügung.</p>
                
                <p style="font-size: 16px; margin-top: 30px;">
                    Mit freundlichen Grüßen,<br>
                    <strong>Ihr SafeChild Law Team</strong>
                </p>
            </div>
            
            <div style="text-align: center; padding: 20px; color: #64748b; font-size: 12px;">
                <p>SafeChild Rechtsanwaltskanzlei</p>
                <p>Spezialisiert auf internationales Kindschaftsrecht</p>
                <p style="margin-top: 15px;">
                    <a href="mailto:info@safechild.mom" style="color: #2563eb; text-decoration: none;">info@safechild.mom</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
SafeChild Law - Video-Konsultation Bestätigt

Hallo {recipient_name},

Ihre Video-Konsultation wurde erfolgreich bestätigt:

Beratung: {meeting_title}
Datum: {meeting_date}
Uhrzeit: {meeting_time}
{f'Meeting ID: {meeting_id}' if meeting_id else ''}
{f'Meeting-Link: {meeting_url}' if meeting_url else ''}

Bei Fragen stehen wir Ihnen jederzeit zur Verfügung.

Mit freundlichen Grüßen,
Ihr SafeChild Law Team

---
SafeChild Rechtsanwaltskanzlei
info@safechild.mom
        """
        
        return EmailService.send_email(
            to=[recipient_email],
            subject=f"Video-Konsultation bestätigt - {meeting_date}",
            html=html_content,
            text=text_content
        )
    
    @staticmethod
    def send_forensic_analysis_complete(
        recipient_email: str,
        recipient_name: str,
        case_id: str,
        file_name: str,
        statistics: Optional[Dict] = None
    ) -> Dict:
        """Send forensic analysis completion notification."""
        
        stats_html = ""
        if statistics:
            stats_html = f"""
            <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e40af; margin-top: 0;">Analyse-Ergebnisse:</h3>
                <ul style="list-style: none; padding: 0;">
                    {f'<li style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">📱 WhatsApp Nachrichten: <strong>{statistics.get("whatsapp_messages", 0)}</strong></li>' if statistics.get("whatsapp_messages") else ''}
                    {f'<li style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">💬 Telegram Nachrichten: <strong>{statistics.get("telegram_messages", 0)}</strong></li>' if statistics.get("telegram_messages") else ''}
                    {f'<li style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">📧 SMS Nachrichten: <strong>{statistics.get("sms_messages", 0)}</strong></li>' if statistics.get("sms_messages") else ''}
                    {f'<li style="padding: 8px 0;">📞 Anrufliste: <strong>{statistics.get("call_logs", 0)}</strong></li>' if statistics.get("call_logs") else ''}
                </ul>
            </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">🔍 Forensische Analyse</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0;">Abgeschlossen</p>
            </div>
            
            <div style="background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #4f46e5; margin-top: 0;">Analyse Abgeschlossen</h2>
                
                <p style="font-size: 16px;">Hallo {recipient_name},</p>
                
                <p style="font-size: 16px;">Die forensische Analyse Ihres Geräts wurde erfolgreich abgeschlossen.</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #6366f1;">
                    <p style="margin: 5px 0;"><strong>Fall-ID:</strong> {case_id}</p>
                    <p style="margin: 5px 0;"><strong>Datei:</strong> {file_name}</p>
                    <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: #16a34a;">✓ Abgeschlossen</span></p>
                </div>
                
                {stats_html}
                
                <div style="background: #dbeafe; border-left: 4px solid #3b82f6; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <p style="margin: 0; font-size: 14px;"><strong>Nächste Schritte:</strong></p>
                    <p style="margin: 10px 0 0 0; font-size: 14px;">Melden Sie sich in Ihrem SafeChild Portal an, um den vollständigen Bericht herunterzuladen.</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/forensic-analysis" style="background: #6366f1; color: white; padding: 15px 40px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                        Bericht Herunterladen
                    </a>
                </div>
                
                <p style="font-size: 16px; margin-top: 30px;">
                    Mit freundlichen Grüßen,<br>
                    <strong>Ihr SafeChild Forensik-Team</strong>
                </p>
            </div>
            
            <div style="text-align: center; padding: 20px; color: #64748b; font-size: 12px;">
                <p>SafeChild Rechtsanwaltskanzlei</p>
                <p>Forensische Analyse • Gerichtsverwertbar • Datenschutzkonform</p>
                <p style="margin-top: 15px;">
                    <a href="mailto:info@safechild.mom" style="color: #6366f1; text-decoration: none;">info@safechild.mom</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
SafeChild Law - Forensische Analyse Abgeschlossen

Hallo {recipient_name},

Die forensische Analyse Ihres Geräts wurde erfolgreich abgeschlossen.

Fall-ID: {case_id}
Datei: {file_name}
Status: Abgeschlossen

Melden Sie sich in Ihrem SafeChild Portal an, um den vollständigen Bericht herunterzuladen.

Mit freundlichen Grüßen,
Ihr SafeChild Forensik-Team

---
SafeChild Rechtsanwaltskanzlei
info@safechild.mom
        """
        
        return EmailService.send_email(
            to=[recipient_email],
            subject=f"Forensische Analyse abgeschlossen - {case_id}",
            html=html_content,
            text=text_content
        )
    
    @staticmethod
    def send_document_uploaded(
        recipient_email: str,
        recipient_name: str,
        document_name: str,
        document_number: str,
        uploaded_at: str
    ) -> Dict:
        """Send document upload confirmation."""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #16a34a 0%, #15803d 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">📄 Dokument Hochgeladen</h1>
            </div>
            
            <div style="background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #15803d; margin-top: 0;">Erfolgreich Hochgeladen</h2>
                
                <p style="font-size: 16px;">Hallo {recipient_name},</p>
                
                <p style="font-size: 16px;">Ihr Dokument wurde erfolgreich hochgeladen und sicher gespeichert.</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #16a34a;">
                    <p style="margin: 5px 0;"><strong>Dokument:</strong> {document_name}</p>
                    <p style="margin: 5px 0;"><strong>Dokumentnummer:</strong> {document_number}</p>
                    <p style="margin: 5px 0;"><strong>Hochgeladen am:</strong> {uploaded_at}</p>
                </div>
                
                <div style="background: #dcfce7; border-left: 4px solid #16a34a; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <p style="margin: 0; font-size: 14px;"><strong>✓ Sicher gespeichert:</strong> Ihr Dokument ist verschlüsselt und wird gemäß DSGVO gespeichert.</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/portal" style="background: #16a34a; color: white; padding: 15px 40px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                        Zum Portal
                    </a>
                </div>
                
                <p style="font-size: 16px; margin-top: 30px;">
                    Mit freundlichen Grüßen,<br>
                    <strong>Ihr SafeChild Law Team</strong>
                </p>
            </div>
            
            <div style="text-align: center; padding: 20px; color: #64748b; font-size: 12px;">
                <p>SafeChild Rechtsanwaltskanzlei</p>
                <p style="margin-top: 15px;">
                    <a href="mailto:info@safechild.mom" style="color: #16a34a; text-decoration: none;">info@safechild.mom</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
SafeChild Law - Dokument Hochgeladen

Hallo {recipient_name},

Ihr Dokument wurde erfolgreich hochgeladen und sicher gespeichert.

Dokument: {document_name}
Dokumentnummer: {document_number}
Hochgeladen am: {uploaded_at}

Ihr Dokument ist verschlüsselt und wird gemäß DSGVO gespeichert.

Mit freundlichen Grüßen,
Ihr SafeChild Law Team

---
SafeChild Rechtsanwaltskanzlei
info@safechild.mom
        """
        
        return EmailService.send_email(
            to=[recipient_email],
            subject=f"Dokument hochgeladen - {document_name}",
            html=html_content,
            text=text_content
        )
    
    @staticmethod
    def send_welcome_email(
        recipient_email: str,
        recipient_name: str,
        client_number: str
    ) -> Dict:
        """Send welcome email to new clients."""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%); padding: 40px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 32px;">Willkommen bei SafeChild Law</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 15px 0 0 0; font-size: 18px;">Ihr Partner für internationales Kindschaftsrecht</p>
            </div>
            
            <div style="background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #1e40af; margin-top: 0;">Willkommen, {recipient_name}!</h2>
                
                <p style="font-size: 16px;">Vielen Dank, dass Sie sich für SafeChild Law entschieden haben. Wir freuen uns, Sie auf Ihrem Weg zu unterstützen.</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2563eb;">
                    <p style="margin: 5px 0;"><strong>Ihre Mandantennummer:</strong> {client_number}</p>
                    <p style="margin: 10px 0 5px 0; font-size: 14px; color: #64748b;">Bitte notieren Sie diese Nummer für zukünftige Korrespondenz.</p>
                </div>
                
                <h3 style="color: #1e40af; margin-top: 30px;">Unsere Services:</h3>
                
                <div style="background: white; padding: 15px; border-radius: 8px; margin: 10px 0;">
                    <p style="margin: 0;"><strong>📞 Video-Konsultationen</strong></p>
                    <p style="margin: 5px 0 0 0; font-size: 14px; color: #64748b;">Persönliche Beratung per Videochat</p>
                </div>
                
                <div style="background: white; padding: 15px; border-radius: 8px; margin: 10px 0;">
                    <p style="margin: 0;"><strong>🔍 Forensische Analyse</strong></p>
                    <p style="margin: 5px 0 0 0; font-size: 14px; color: #64748b;">Professionelle Geräte-Analyse für Sorgerechtsfälle</p>
                </div>
                
                <div style="background: white; padding: 15px; border-radius: 8px; margin: 10px 0;">
                    <p style="margin: 0;"><strong>📄 Dokumentenverwaltung</strong></p>
                    <p style="margin: 5px 0 0 0; font-size: 14px; color: #64748b;">Sichere Speicherung aller wichtigen Unterlagen</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/portal" style="background: #2563eb; color: white; padding: 15px 40px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                        Zum Kunden-Portal
                    </a>
                </div>
                
                <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <p style="margin: 0; font-size: 14px;"><strong>Brauchen Sie Hilfe?</strong></p>
                    <p style="margin: 10px 0 0 0; font-size: 14px;">Unser Team steht Ihnen jederzeit zur Verfügung. Antworten Sie einfach auf diese E-Mail.</p>
                </div>
                
                <p style="font-size: 16px; margin-top: 30px;">
                    Mit freundlichen Grüßen,<br>
                    <strong>Ihr SafeChild Law Team</strong>
                </p>
            </div>
            
            <div style="text-align: center; padding: 20px; color: #64748b; font-size: 12px;">
                <p>SafeChild Rechtsanwaltskanzlei</p>
                <p>Ihr Recht, Ihr Kind zu sehen</p>
                <p style="margin-top: 15px;">
                    <a href="mailto:info@safechild.mom" style="color: #2563eb; text-decoration: none;">info@safechild.mom</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Willkommen bei SafeChild Law

Hallo {recipient_name},

Vielen Dank, dass Sie sich für SafeChild Law entschieden haben. Wir freuen uns, Sie auf Ihrem Weg zu unterstützen.

Ihre Mandantennummer: {client_number}
Bitte notieren Sie diese Nummer für zukünftige Korrespondenz.

Unsere Services:
- Video-Konsultationen: Persönliche Beratung per Videochat
- Forensische Analyse: Professionelle Geräte-Analyse für Sorgerechtsfälle
- Dokumentenverwaltung: Sichere Speicherung aller wichtigen Unterlagen

Portal: {os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/portal

Brauchen Sie Hilfe? Unser Team steht Ihnen jederzeit zur Verfügung.

Mit freundlichen Grüßen,
Ihr SafeChild Law Team

---
SafeChild Rechtsanwaltskanzlei
info@safechild.mom
        """
        
        return EmailService.send_email(
            to=[recipient_email],
            subject="Willkommen bei SafeChild Law",
            html=html_content,
            text=text_content
        )

    @staticmethod
    def send_magic_link_email(
        recipient_email: str,
        recipient_name: str,
        magic_link: str,
        requested_types: List[str],
        expires_at: datetime
    ) -> Dict:
        """Send magic link email for evidence upload."""

        # Format requested types for display
        types_display = ", ".join([TYPE_DISPLAY_NAMES.get(t, t) for t in requested_types])
        expires_formatted = expires_at.strftime("%d.%m.%Y um %H:%M Uhr")

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">SafeChild Law</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0;">Sichere Beweisübermittlung</p>
            </div>

            <div style="background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #4f46e5; margin-top: 0;">Anfrage zur Beweisübermittlung</h2>

                <p style="font-size: 16px;">Hallo {recipient_name},</p>

                <p style="font-size: 16px;">Ihr Rechtsanwalt hat Sie gebeten, folgende Beweise sicher hochzuladen:</p>

                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #6366f1;">
                    <p style="margin: 5px 0;"><strong>Angeforderte Daten:</strong></p>
                    <p style="margin: 5px 0; color: #4f46e5;">{types_display}</p>
                    <p style="margin: 15px 0 5px 0;"><strong>Link gültig bis:</strong></p>
                    <p style="margin: 5px 0; color: #dc2626;">{expires_formatted}</p>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{magic_link}" style="background: #6366f1; color: white; padding: 15px 40px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block; font-size: 16px;">
                        Beweise Hochladen
                    </a>
                </div>

                <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <p style="margin: 0; font-size: 14px;"><strong>Wichtige Hinweise:</strong></p>
                    <ul style="margin: 10px 0 0 0; padding-left: 20px; font-size: 14px;">
                        <li>Dieser Link ist nur für Sie bestimmt</li>
                        <li>Teilen Sie diesen Link nicht mit Dritten</li>
                        <li>Alle hochgeladenen Daten werden verschlüsselt</li>
                        <li>Der Link ist nach dem Ablaufdatum nicht mehr gültig</li>
                    </ul>
                </div>

                <div style="background: #dbeafe; border-left: 4px solid #3b82f6; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <p style="margin: 0; font-size: 14px;"><strong>So funktioniert es:</strong></p>
                    <ol style="margin: 10px 0 0 0; padding-left: 20px; font-size: 14px;">
                        <li>Klicken Sie auf "Beweise Hochladen"</li>
                        <li>Wählen Sie die gewünschten Dateien aus</li>
                        <li>Bestätigen Sie den Upload</li>
                        <li>Sie erhalten eine Bestätigung per E-Mail</li>
                    </ol>
                </div>

                <p style="font-size: 16px; margin-top: 30px;">
                    Bei Fragen stehen wir Ihnen jederzeit zur Verfügung.
                </p>

                <p style="font-size: 16px; margin-top: 30px;">
                    Mit freundlichen Grüßen,<br>
                    <strong>Ihr SafeChild Law Team</strong>
                </p>
            </div>

            <div style="text-align: center; padding: 20px; color: #64748b; font-size: 12px;">
                <p>SafeChild Rechtsanwaltskanzlei</p>
                <p>Sichere Beweisübermittlung • DSGVO-konform • Ende-zu-Ende verschlüsselt</p>
                <p style="margin-top: 15px;">
                    <a href="mailto:info@safechild.mom" style="color: #6366f1; text-decoration: none;">info@safechild.mom</a>
                </p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
SafeChild Law - Anfrage zur Beweisübermittlung

Hallo {recipient_name},

Ihr Rechtsanwalt hat Sie gebeten, folgende Beweise sicher hochzuladen:

Angeforderte Daten: {types_display}
Link gültig bis: {expires_formatted}

Klicken Sie auf folgenden Link, um Ihre Beweise hochzuladen:
{magic_link}

Wichtige Hinweise:
- Dieser Link ist nur für Sie bestimmt
- Teilen Sie diesen Link nicht mit Dritten
- Alle hochgeladenen Daten werden verschlüsselt
- Der Link ist nach dem Ablaufdatum nicht mehr gültig

Bei Fragen stehen wir Ihnen jederzeit zur Verfügung.

Mit freundlichen Grüßen,
Ihr SafeChild Law Team

---
SafeChild Rechtsanwaltskanzlei
info@safechild.mom
        """

        return EmailService.send_email(
            to=[recipient_email],
            subject="SafeChild: Anfrage zur Beweisübermittlung",
            html=html_content,
            text=text_content
        )
