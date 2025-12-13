"""
Report Generation Module for SafeChild

Provides court-ready report generation capabilities:
- PDF generation with WeasyPrint
- DOCX export with python-docx
- Digital signatures with cryptography
- Multi-language support (DE/EN/TR)
- Legal compliance templates
"""

from .report_engine import (
    ReportEngine,
    PDFGenerator,
    DOCXGenerator,
    DigitalSigner,
    ReportTemplate,
    ReportType,
    ReportFormat,
    ReportLanguage,
    GeneratedReport,
    SignatureInfo,
    ChainOfCustody,
    EvidenceItem
)

from .legal_templates import (
    LegalTemplateEngine,
    GDPRChecklist,
    ExpertWitnessTemplate,
    EvidenceAuthenticationPage,
    CourtFilingFormat,
    Jurisdiction,
    generate_gdpr_checklist,
    generate_expert_statement,
    generate_authentication_page
)

from .export_formats import (
    ExportEngine,
    E001Exporter,
    CellebriteExporter,
    ExportFormat,
    export_to_format
)

__all__ = [
    # Report Engine
    'ReportEngine',
    'PDFGenerator',
    'DOCXGenerator',
    'DigitalSigner',
    'ReportTemplate',
    'ReportType',
    'ReportFormat',
    'ReportLanguage',
    'GeneratedReport',
    'SignatureInfo',
    'ChainOfCustody',
    'EvidenceItem',
    # Legal Templates
    'LegalTemplateEngine',
    'GDPRChecklist',
    'ExpertWitnessTemplate',
    'EvidenceAuthenticationPage',
    'CourtFilingFormat',
    'Jurisdiction',
    'generate_gdpr_checklist',
    'generate_expert_statement',
    'generate_authentication_page',
    # Export Formats
    'ExportEngine',
    'E001Exporter',
    'CellebriteExporter',
    'ExportFormat',
    'export_to_format'
]
