"""
Timeline Export Module

Comprehensive export functionality for case timelines in multiple formats:
- CSV: Spreadsheet-compatible data export with all timeline details
- PDF: Professional court-ready reports with visual timeline
- PNG: Visual timeline diagram for presentations

For legal/forensic use in authorized custody investigations.
"""

import csv
import io
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ExportFormat(str, Enum):
    """Supported export formats."""
    CSV = "csv"
    PDF = "pdf"
    PNG = "png"


@dataclass
class ExportResult:
    """Result of an export operation."""
    success: bool
    format: ExportFormat
    filename: str
    file_path: Optional[str] = None
    content_bytes: Optional[bytes] = None
    content_type: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimelineEvent:
    """Represents a timeline event for export."""
    event_id: str
    timestamp: datetime
    event_type: str
    title: str
    description: str = ""
    importance: str = "medium"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_by: str = ""


@dataclass
class TimelineTask:
    """Represents a task for export."""
    task_id: str
    title: str
    description: str = ""
    status: str = "pending"
    priority: str = "medium"
    due_date: Optional[datetime] = None
    assigned_to: str = ""
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class TimelineMilestone:
    """Represents a milestone for export."""
    milestone_id: str
    title: str
    description: str = ""
    status: str = "pending"
    target_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    order: int = 0
    phase: str = ""


class TimelineExporter:
    """
    Export case timelines in multiple formats.

    Supports CSV, PDF, and PNG export formats with full timeline data.
    """

    def __init__(self, case_id: str, client_name: str = ""):
        """Initialize exporter for a specific case."""
        self.case_id = case_id
        self.client_name = client_name
        self.events: List[TimelineEvent] = []
        self.tasks: List[TimelineTask] = []
        self.milestones: List[TimelineMilestone] = []
        self._pdf_available = self._check_pdf_support()
        self._png_available = self._check_png_support()

    def _check_pdf_support(self) -> bool:
        """Check if PDF generation is available."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            return True
        except ImportError:
            logger.warning("reportlab not installed. PDF export unavailable.")
            return False

    def _check_png_support(self) -> bool:
        """Check if PNG generation is available."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            return True
        except ImportError:
            logger.warning("Pillow not installed. PNG export unavailable.")
            return False

    def add_event(self, event: TimelineEvent) -> None:
        """Add an event to the export."""
        self.events.append(event)

    def add_events_from_dict(self, events: List[Dict[str, Any]]) -> None:
        """Add events from dictionary format (from MongoDB)."""
        for e in events:
            timestamp = e.get("created_at") or e.get("timestamp")
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except ValueError:
                    timestamp = datetime.utcnow()

            event = TimelineEvent(
                event_id=e.get("event_id", ""),
                timestamp=timestamp or datetime.utcnow(),
                event_type=e.get("event_type", "custom"),
                title=e.get("title", ""),
                description=e.get("description", ""),
                importance=e.get("importance", "medium"),
                metadata=e.get("metadata", {}),
                created_by=e.get("created_by", "")
            )
            self.events.append(event)

    def add_task(self, task: TimelineTask) -> None:
        """Add a task to the export."""
        self.tasks.append(task)

    def add_tasks_from_dict(self, tasks: List[Dict[str, Any]]) -> None:
        """Add tasks from dictionary format."""
        for t in tasks:
            due_date = t.get("due_date")
            if isinstance(due_date, str):
                try:
                    due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
                except ValueError:
                    due_date = None

            created_at = t.get("created_at")
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except ValueError:
                    created_at = None

            task = TimelineTask(
                task_id=t.get("task_id", ""),
                title=t.get("title", ""),
                description=t.get("description", ""),
                status=t.get("status", "pending"),
                priority=t.get("priority", "medium"),
                due_date=due_date,
                assigned_to=t.get("assigned_to", ""),
                created_at=created_at
            )
            self.tasks.append(task)

    def add_milestone(self, milestone: TimelineMilestone) -> None:
        """Add a milestone to the export."""
        self.milestones.append(milestone)

    def add_milestones_from_dict(self, milestones: List[Dict[str, Any]]) -> None:
        """Add milestones from dictionary format."""
        for m in milestones:
            target_date = m.get("target_date")
            if isinstance(target_date, str):
                try:
                    target_date = datetime.fromisoformat(target_date.replace("Z", "+00:00"))
                except ValueError:
                    target_date = None

            milestone = TimelineMilestone(
                milestone_id=m.get("milestone_id", ""),
                title=m.get("title", ""),
                description=m.get("description", ""),
                status=m.get("status", "pending"),
                target_date=target_date,
                order=m.get("order", 0),
                phase=m.get("phase", "")
            )
            self.milestones.append(milestone)

    def export(self, format: ExportFormat, output_dir: Optional[str] = None) -> ExportResult:
        """
        Export timeline in specified format.

        Args:
            format: Export format (CSV, PDF, PNG)
            output_dir: Optional directory to save file

        Returns:
            ExportResult with file content or path
        """
        if format == ExportFormat.CSV:
            return self._export_csv(output_dir)
        elif format == ExportFormat.PDF:
            return self._export_pdf(output_dir)
        elif format == ExportFormat.PNG:
            return self._export_png(output_dir)
        else:
            return ExportResult(
                success=False,
                format=format,
                filename="",
                error=f"Unsupported format: {format}"
            )

    def _export_csv(self, output_dir: Optional[str] = None) -> ExportResult:
        """Export timeline as CSV."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"timeline_{self.case_id}_{timestamp}.csv"

        try:
            output = io.StringIO()

            # Write header info
            output.write(f"# SafeChild Case Timeline Export\n")
            output.write(f"# Case ID: {self.case_id}\n")
            output.write(f"# Client: {self.client_name}\n")
            output.write(f"# Generated: {datetime.utcnow().isoformat()}\n")
            output.write(f"#\n")

            # Events section
            output.write(f"\n### TIMELINE EVENTS ###\n")
            writer = csv.writer(output)
            writer.writerow([
                "Event ID", "Timestamp", "Type", "Title", "Description",
                "Importance", "Created By", "Metadata"
            ])

            # Sort events by timestamp
            sorted_events = sorted(self.events, key=lambda e: e.timestamp)
            for event in sorted_events:
                writer.writerow([
                    event.event_id,
                    event.timestamp.isoformat() if event.timestamp else "",
                    event.event_type,
                    event.title,
                    event.description,
                    event.importance,
                    event.created_by,
                    str(event.metadata) if event.metadata else ""
                ])

            # Tasks section
            output.write(f"\n### TASKS ###\n")
            writer.writerow([
                "Task ID", "Title", "Description", "Status", "Priority",
                "Due Date", "Assigned To", "Created At"
            ])

            for task in self.tasks:
                writer.writerow([
                    task.task_id,
                    task.title,
                    task.description,
                    task.status,
                    task.priority,
                    task.due_date.isoformat() if task.due_date else "",
                    task.assigned_to,
                    task.created_at.isoformat() if task.created_at else ""
                ])

            # Milestones section
            output.write(f"\n### MILESTONES ###\n")
            writer.writerow([
                "Milestone ID", "Order", "Title", "Description", "Phase",
                "Status", "Target Date"
            ])

            sorted_milestones = sorted(self.milestones, key=lambda m: m.order)
            for milestone in sorted_milestones:
                writer.writerow([
                    milestone.milestone_id,
                    milestone.order,
                    milestone.title,
                    milestone.description,
                    milestone.phase,
                    milestone.status,
                    milestone.target_date.isoformat() if milestone.target_date else ""
                ])

            content = output.getvalue().encode('utf-8')

            # Save to file if output_dir specified
            file_path = None
            if output_dir:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                file_path = str(Path(output_dir) / filename)
                with open(file_path, 'wb') as f:
                    f.write(content)

            return ExportResult(
                success=True,
                format=ExportFormat.CSV,
                filename=filename,
                file_path=file_path,
                content_bytes=content,
                content_type="text/csv",
                metadata={
                    "events_count": len(self.events),
                    "tasks_count": len(self.tasks),
                    "milestones_count": len(self.milestones)
                }
            )

        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            return ExportResult(
                success=False,
                format=ExportFormat.CSV,
                filename=filename,
                error=str(e)
            )

    def _export_pdf(self, output_dir: Optional[str] = None) -> ExportResult:
        """Export timeline as PDF report."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"timeline_{self.case_id}_{timestamp}.pdf"

        if not self._pdf_available:
            return ExportResult(
                success=False,
                format=ExportFormat.PDF,
                filename=filename,
                error="reportlab not installed. Install with: pip install reportlab"
            )

        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            )
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT

            # Create PDF in memory
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )

            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=20
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=15,
                spaceAfter=10
            )

            normal_style = styles['Normal']

            # Build document content
            elements = []

            # Title
            elements.append(Paragraph("SafeChild Case Timeline Report", title_style))
            elements.append(Spacer(1, 0.2*inch))

            # Case info
            elements.append(Paragraph(f"<b>Case ID:</b> {self.case_id}", normal_style))
            if self.client_name:
                elements.append(Paragraph(f"<b>Client:</b> {self.client_name}", normal_style))
            elements.append(Paragraph(
                f"<b>Generated:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
                normal_style
            ))
            elements.append(Spacer(1, 0.3*inch))

            # Summary stats
            elements.append(Paragraph("Summary", heading_style))
            summary_data = [
                ["Category", "Count"],
                ["Timeline Events", str(len(self.events))],
                ["Tasks", str(len(self.tasks))],
                ["Milestones", str(len(self.milestones))]
            ]

            completed_tasks = sum(1 for t in self.tasks if t.status == "completed")
            if self.tasks:
                summary_data.append(["Tasks Completed", f"{completed_tasks}/{len(self.tasks)}"])

            completed_milestones = sum(1 for m in self.milestones if m.status == "completed")
            if self.milestones:
                summary_data.append(["Milestones Completed", f"{completed_milestones}/{len(self.milestones)}"])

            summary_table = Table(summary_data, colWidths=[3*inch, 1.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 0.3*inch))

            # Milestones section
            if self.milestones:
                elements.append(Paragraph("Milestones Progress", heading_style))

                sorted_milestones = sorted(self.milestones, key=lambda m: m.order)
                milestone_data = [["#", "Title", "Phase", "Status", "Target Date"]]

                for m in sorted_milestones:
                    status_display = {
                        "completed": "Completed",
                        "in_progress": "In Progress",
                        "pending": "Pending"
                    }.get(m.status, m.status.capitalize())

                    target = m.target_date.strftime("%Y-%m-%d") if m.target_date else "-"
                    milestone_data.append([
                        str(m.order),
                        m.title[:40] + "..." if len(m.title) > 40 else m.title,
                        m.phase.capitalize(),
                        status_display,
                        target
                    ])

                milestone_table = Table(
                    milestone_data,
                    colWidths=[0.4*inch, 2.5*inch, 1.2*inch, 1*inch, 1*inch]
                )
                milestone_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                elements.append(milestone_table)
                elements.append(Spacer(1, 0.3*inch))

            # Timeline Events section
            if self.events:
                elements.append(Paragraph("Timeline Events", heading_style))

                sorted_events = sorted(self.events, key=lambda e: e.timestamp, reverse=True)[:20]
                event_data = [["Date", "Type", "Title", "Importance"]]

                for e in sorted_events:
                    event_data.append([
                        e.timestamp.strftime("%Y-%m-%d %H:%M") if e.timestamp else "-",
                        e.event_type.replace("_", " ").title(),
                        e.title[:35] + "..." if len(e.title) > 35 else e.title,
                        e.importance.capitalize()
                    ])

                event_table = Table(
                    event_data,
                    colWidths=[1.3*inch, 1.5*inch, 2.5*inch, 0.8*inch]
                )
                event_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                elements.append(event_table)

                if len(self.events) > 20:
                    elements.append(Paragraph(
                        f"<i>Showing 20 of {len(self.events)} events</i>",
                        normal_style
                    ))
                elements.append(Spacer(1, 0.3*inch))

            # Tasks section
            if self.tasks:
                elements.append(Paragraph("Tasks", heading_style))

                task_data = [["Title", "Status", "Priority", "Due Date", "Assigned To"]]

                for t in self.tasks:
                    status_display = {
                        "completed": "Done",
                        "in_progress": "In Progress",
                        "pending": "Pending"
                    }.get(t.status, t.status.capitalize())

                    due = t.due_date.strftime("%Y-%m-%d") if t.due_date else "-"
                    task_data.append([
                        t.title[:30] + "..." if len(t.title) > 30 else t.title,
                        status_display,
                        t.priority.capitalize(),
                        due,
                        t.assigned_to[:15] if t.assigned_to else "-"
                    ])

                task_table = Table(
                    task_data,
                    colWidths=[2*inch, 0.9*inch, 0.8*inch, 0.9*inch, 1.2*inch]
                )
                task_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkorange),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                elements.append(task_table)

            # Footer
            elements.append(Spacer(1, 0.5*inch))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            elements.append(Paragraph(
                "Generated by SafeChild Digital Forensics Platform | Confidential",
                footer_style
            ))

            # Build PDF
            doc.build(elements)
            content = buffer.getvalue()
            buffer.close()

            # Save to file if output_dir specified
            file_path = None
            if output_dir:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                file_path = str(Path(output_dir) / filename)
                with open(file_path, 'wb') as f:
                    f.write(content)

            return ExportResult(
                success=True,
                format=ExportFormat.PDF,
                filename=filename,
                file_path=file_path,
                content_bytes=content,
                content_type="application/pdf",
                metadata={
                    "events_count": len(self.events),
                    "tasks_count": len(self.tasks),
                    "milestones_count": len(self.milestones),
                    "pages": 1  # Approximate
                }
            )

        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            return ExportResult(
                success=False,
                format=ExportFormat.PDF,
                filename=filename,
                error=str(e)
            )

    def _export_png(self, output_dir: Optional[str] = None) -> ExportResult:
        """Export timeline as PNG image."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"timeline_{self.case_id}_{timestamp}.png"

        if not self._png_available:
            return ExportResult(
                success=False,
                format=ExportFormat.PNG,
                filename=filename,
                error="Pillow not installed. Install with: pip install Pillow"
            )

        try:
            from PIL import Image, ImageDraw, ImageFont

            # Calculate image dimensions
            num_items = max(len(self.events), len(self.milestones), 1)
            width = 1200
            height = max(600, 150 + num_items * 80)

            # Create image
            img = Image.new('RGB', (width, height), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)

            # Try to load a font, fall back to default
            try:
                font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
                font_heading = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
                font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
            except (IOError, OSError):
                font_title = ImageFont.load_default()
                font_heading = ImageFont.load_default()
                font_normal = ImageFont.load_default()
                font_small = ImageFont.load_default()

            # Colors
            color_blue = (59, 130, 246)
            color_green = (34, 197, 94)
            color_orange = (249, 115, 22)
            color_red = (239, 68, 68)
            color_gray = (107, 114, 128)
            color_dark = (31, 41, 55)

            # Draw header
            draw.rectangle([0, 0, width, 80], fill=(59, 130, 246))
            draw.text((40, 20), "SafeChild Case Timeline", fill=(255, 255, 255), font=font_title)
            draw.text((40, 50), f"Case: {self.case_id} | {datetime.utcnow().strftime('%Y-%m-%d')}",
                     fill=(200, 220, 255), font=font_normal)

            # Draw statistics bar
            y_stats = 100
            stats_text = f"Events: {len(self.events)} | Tasks: {len(self.tasks)} | Milestones: {len(self.milestones)}"
            draw.text((40, y_stats), stats_text, fill=color_gray, font=font_normal)

            # Draw timeline line
            y_line = 150
            line_x_start = 80
            line_x_end = width - 80
            draw.line([(line_x_start, y_line), (line_x_end, y_line)], fill=color_blue, width=3)

            # Draw milestones on timeline
            if self.milestones:
                sorted_milestones = sorted(self.milestones, key=lambda m: m.order)
                num_milestones = len(sorted_milestones)

                for i, milestone in enumerate(sorted_milestones):
                    # Calculate x position
                    if num_milestones > 1:
                        x = line_x_start + (i / (num_milestones - 1)) * (line_x_end - line_x_start)
                    else:
                        x = (line_x_start + line_x_end) / 2

                    # Choose color based on status
                    if milestone.status == "completed":
                        dot_color = color_green
                    elif milestone.status == "in_progress":
                        dot_color = color_orange
                    else:
                        dot_color = color_gray

                    # Draw milestone dot
                    dot_radius = 12
                    draw.ellipse(
                        [x - dot_radius, y_line - dot_radius, x + dot_radius, y_line + dot_radius],
                        fill=dot_color,
                        outline=(255, 255, 255),
                        width=2
                    )

                    # Draw milestone number
                    draw.text((x - 4, y_line - 6), str(milestone.order), fill=(255, 255, 255), font=font_small)

                    # Draw milestone title (alternate above/below)
                    title_text = milestone.title[:25] + "..." if len(milestone.title) > 25 else milestone.title
                    text_bbox = draw.textbbox((0, 0), title_text, font=font_small)
                    text_width = text_bbox[2] - text_bbox[0]

                    if i % 2 == 0:
                        text_y = y_line - 35
                    else:
                        text_y = y_line + 20

                    draw.text((x - text_width/2, text_y), title_text, fill=color_dark, font=font_small)

            # Draw events list
            y_events = y_line + 80
            draw.text((40, y_events), "Recent Events", fill=color_blue, font=font_heading)
            y_events += 30

            # Sort and show recent events
            sorted_events = sorted(self.events, key=lambda e: e.timestamp, reverse=True)[:10]
            for event in sorted_events:
                # Event indicator dot
                importance_colors = {
                    "high": color_red,
                    "medium": color_orange,
                    "low": color_green
                }
                dot_color = importance_colors.get(event.importance, color_gray)
                draw.ellipse([50, y_events + 3, 58, y_events + 11], fill=dot_color)

                # Event text
                date_str = event.timestamp.strftime("%m/%d %H:%M") if event.timestamp else ""
                event_text = f"{date_str} - {event.title[:60]}"
                draw.text((70, y_events), event_text, fill=color_dark, font=font_normal)

                y_events += 25
                if y_events > height - 80:
                    break

            # Draw footer
            draw.rectangle([0, height - 40, width, height], fill=(243, 244, 246))
            draw.text((40, height - 28),
                     "Generated by SafeChild Digital Forensics Platform | Confidential",
                     fill=color_gray, font=font_small)

            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            content = buffer.getvalue()
            buffer.close()

            # Save to file if output_dir specified
            file_path = None
            if output_dir:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                file_path = str(Path(output_dir) / filename)
                img.save(file_path, 'PNG', optimize=True)

            return ExportResult(
                success=True,
                format=ExportFormat.PNG,
                filename=filename,
                file_path=file_path,
                content_bytes=content,
                content_type="image/png",
                metadata={
                    "width": width,
                    "height": height,
                    "events_shown": min(len(self.events), 10),
                    "milestones_shown": len(self.milestones)
                }
            )

        except Exception as e:
            logger.error(f"PNG export failed: {e}")
            return ExportResult(
                success=False,
                format=ExportFormat.PNG,
                filename=filename,
                error=str(e)
            )


# =============================================================================
# Convenience Functions
# =============================================================================

def export_timeline_csv(
    case_id: str,
    events: List[Dict[str, Any]],
    tasks: List[Dict[str, Any]],
    milestones: List[Dict[str, Any]],
    client_name: str = "",
    output_dir: Optional[str] = None
) -> ExportResult:
    """
    Convenience function to export timeline as CSV.

    Args:
        case_id: Case identifier
        events: List of event dictionaries
        tasks: List of task dictionaries
        milestones: List of milestone dictionaries
        client_name: Optional client name
        output_dir: Optional output directory

    Returns:
        ExportResult with CSV content
    """
    exporter = TimelineExporter(case_id, client_name)
    exporter.add_events_from_dict(events)
    exporter.add_tasks_from_dict(tasks)
    exporter.add_milestones_from_dict(milestones)
    return exporter.export(ExportFormat.CSV, output_dir)


def export_timeline_pdf(
    case_id: str,
    events: List[Dict[str, Any]],
    tasks: List[Dict[str, Any]],
    milestones: List[Dict[str, Any]],
    client_name: str = "",
    output_dir: Optional[str] = None
) -> ExportResult:
    """
    Convenience function to export timeline as PDF.

    Args:
        case_id: Case identifier
        events: List of event dictionaries
        tasks: List of task dictionaries
        milestones: List of milestone dictionaries
        client_name: Optional client name
        output_dir: Optional output directory

    Returns:
        ExportResult with PDF content
    """
    exporter = TimelineExporter(case_id, client_name)
    exporter.add_events_from_dict(events)
    exporter.add_tasks_from_dict(tasks)
    exporter.add_milestones_from_dict(milestones)
    return exporter.export(ExportFormat.PDF, output_dir)


def export_timeline_png(
    case_id: str,
    events: List[Dict[str, Any]],
    tasks: List[Dict[str, Any]],
    milestones: List[Dict[str, Any]],
    client_name: str = "",
    output_dir: Optional[str] = None
) -> ExportResult:
    """
    Convenience function to export timeline as PNG.

    Args:
        case_id: Case identifier
        events: List of event dictionaries
        tasks: List of task dictionaries
        milestones: List of milestone dictionaries
        client_name: Optional client name
        output_dir: Optional output directory

    Returns:
        ExportResult with PNG content
    """
    exporter = TimelineExporter(case_id, client_name)
    exporter.add_events_from_dict(events)
    exporter.add_tasks_from_dict(tasks)
    exporter.add_milestones_from_dict(milestones)
    return exporter.export(ExportFormat.PNG, output_dir)


# CLI interface for testing
if __name__ == '__main__':
    # Test export with sample data
    sample_events = [
        {
            "event_id": "EVT-001",
            "created_at": "2024-01-15T10:30:00",
            "event_type": "case_created",
            "title": "Case opened",
            "description": "Initial case intake completed",
            "importance": "high"
        },
        {
            "event_id": "EVT-002",
            "created_at": "2024-01-20T14:00:00",
            "event_type": "document_uploaded",
            "title": "Evidence documents uploaded",
            "description": "Court documents and photos uploaded",
            "importance": "medium"
        }
    ]

    sample_tasks = [
        {
            "task_id": "TSK-001",
            "title": "Review initial documents",
            "status": "completed",
            "priority": "high",
            "due_date": "2024-01-18T00:00:00"
        },
        {
            "task_id": "TSK-002",
            "title": "Schedule forensic analysis",
            "status": "in_progress",
            "priority": "medium",
            "due_date": "2024-02-01T00:00:00"
        }
    ]

    sample_milestones = [
        {
            "milestone_id": "MS-001",
            "title": "Case Intake",
            "status": "completed",
            "order": 1,
            "phase": "intake"
        },
        {
            "milestone_id": "MS-002",
            "title": "Document Collection",
            "status": "in_progress",
            "order": 2,
            "phase": "preparation"
        },
        {
            "milestone_id": "MS-003",
            "title": "Forensic Analysis",
            "status": "pending",
            "order": 3,
            "phase": "investigation"
        }
    ]

    # Test CSV export
    result = export_timeline_csv("TEST-001", sample_events, sample_tasks, sample_milestones, "Test Client")
    if result.success:
        print(f"CSV export successful: {result.filename}")
        print(f"Size: {len(result.content_bytes)} bytes")
    else:
        print(f"CSV export failed: {result.error}")

    # Test PDF export
    result = export_timeline_pdf("TEST-001", sample_events, sample_tasks, sample_milestones, "Test Client")
    if result.success:
        print(f"PDF export successful: {result.filename}")
        print(f"Size: {len(result.content_bytes)} bytes")
    else:
        print(f"PDF export failed: {result.error}")

    # Test PNG export
    result = export_timeline_png("TEST-001", sample_events, sample_tasks, sample_milestones, "Test Client")
    if result.success:
        print(f"PNG export successful: {result.filename}")
        print(f"Size: {len(result.content_bytes)} bytes")
    else:
        print(f"PNG export failed: {result.error}")
