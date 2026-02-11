import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os


class ExportService:
    """Service for exporting data to CSV and PDF with Hebrew support."""
    
    def __init__(self):
        self._register_hebrew_fonts()
    
    def _register_hebrew_fonts(self):
        """Register Hebrew fonts for PDF generation."""
        fonts_dir = os.path.join(os.path.dirname(__file__), '..', 'fonts')
        
        font_paths = {
            'Arial': 'arial.ttf',
            'ArialBold': 'arialbd.ttf',
        }
        
        for font_name, font_file in font_paths.items():
            font_path = os.path.join(fonts_dir, font_file)
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                except Exception:
                    pass
    
    def export_to_csv(
        self,
        data: List[Dict[str, Any]],
        filename: str = "export.csv"
    ) -> bytes:
        """
        Export data to CSV with UTF-8 encoding and Hebrew support.
        
        Args:
            data: List of dictionaries to export
            filename: Name of the file (for reference)
        
        Returns:
            CSV content as bytes
        """
        if not data:
            return b""
        
        output = io.StringIO()
        fieldnames = list(data[0].keys())
        
        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            extrasaction='ignore',
            lineterminator='\n'
        )
        
        writer.writeheader()
        writer.writerows(data)
        
        csv_content = output.getvalue()
        return csv_content.encode('utf-8-sig')
    
    def export_to_pdf(
        self,
        data: List[Dict[str, Any]],
        title: str = "דוח",
        columns: Optional[List[str]] = None,
        filename: str = "export.pdf"
    ) -> bytes:
        """
        Export data to PDF with Hebrew support and formatted table.
        
        Args:
            data: List of dictionaries to export
            title: Title of the report
            columns: List of column names to include (if None, uses all keys)
            filename: Name of the file (for reference)
        
        Returns:
            PDF content as bytes
        """
        if not data:
            return b""
        
        output = io.BytesIO()
        
        if columns is None:
            columns = list(data[0].keys())
        
        doc = SimpleDocTemplate(
            output,
            pagesize=landscape(A4),
            rightMargin=0.5*cm,
            leftMargin=0.5*cm,
            topMargin=1*cm,
            bottomMargin=0.5*cm,
        )
        
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=1,
        )
        
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.3*cm))
        
        table_data = [columns]
        for row in data:
            table_row = []
            for col in columns:
                value = row.get(col, '')
                if value is None:
                    value = ''
                if isinstance(value, (datetime, )):
                    value = value.strftime('%d.%m.%Y %H:%M')
                elif isinstance(value, bool):
                    value = 'כן' if value else 'לא'
                table_row.append(str(value))
            table_data.append(table_row)
        
        col_widths = [18*cm / len(columns)] * len(columns)
        table = Table(table_data, colWidths=col_widths)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        story.append(table)
        
        story.append(Spacer(1, 0.5*cm))
        timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=2,
        )
        story.append(Paragraph(f"נוצר: {timestamp}", footer_style))
        
        doc.build(story)
        
        pdf_content = output.getvalue()
        return pdf_content
    
    def prepare_export_data(
        self,
        records: List[Any],
        field_mapping: Optional[Dict[str, str]] = None,
        exclude_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Prepare ORM records for export by converting to dictionaries.
        
        Args:
            records: List of ORM model instances
            field_mapping: Dict mapping field names to display names
            exclude_fields: List of field names to exclude
        
        Returns:
            List of dictionaries ready for export
        """
        exclude_fields = exclude_fields or []
        field_mapping = field_mapping or {}
        
        data = []
        for record in records:
            row = {}
            
            if hasattr(record, '__dict__'):
                for key, value in record.__dict__.items():
                    if key.startswith('_') or key in exclude_fields:
                        continue
                    
                    display_name = field_mapping.get(key, key)
                    row[display_name] = value
            
            if row:
                data.append(row)
        
        return data


export_service = ExportService()
