from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)


class PDFReportService:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name='CustomTitle', fontSize=22, textColor=colors.HexColor("#1a1a2e"),
            spaceAfter=20, fontName='Helvetica-Bold',
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeading', fontSize=14, textColor=colors.HexColor("#4338ca"),
            spaceBefore=15, spaceAfter=8, fontName='Helvetica-Bold',
        ))
        self.styles.add(ParagraphStyle(
            name='BodyText2', fontSize=10, textColor=colors.HexColor("#333333"),
            spaceAfter=6, leading=14,
        ))

    def generate_report(self, opportunities, problems, gaps, trends, username="User"):
        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm,
            title="AI Opportunity Discovery Report",
        )
        elements = []

        # Header
        elements.append(Paragraph("AI Opportunity Discovery Report", self.styles['CustomTitle']))
        elements.append(Paragraph(
            f"Generated for: <b>{username}</b><br/>"
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            self.styles['BodyText2'],
        ))
        elements.append(Spacer(1, 0.5*cm))

        # Summary
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeading']))
        summary_data = [
            ["Metric", "Count"],
            ["Total Opportunities", str(len(opportunities))],
            ["Problem Clusters", str(len(problems))],
            ["Research Gaps", str(len(gaps))],
            ["Active Trends", str(len(trends))],
        ]
        t = Table(summary_data, colWidths=[8*cm, 4*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4338ca")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.5*cm))

        # Opportunities
        elements.append(Paragraph("Top Opportunities", self.styles['SectionHeading']))
        if opportunities:
            rows = [["#", "Title", "Score", "Demand", "Gap", "Trend"]]
            for i, o in enumerate(opportunities[:15], 1):
                rows.append([
                    str(i),
                    Paragraph(o.title[:60], self.styles['BodyText2']),
                    f"{o.opportunity_score:.2f}",
                    f"{o.demand_score:.2f}",
                    f"{o.research_gap_score:.2f}",
                    f"{o.trend_score:.2f}",
                ])
            t = Table(rows, colWidths=[1*cm, 8*cm, 2*cm, 2*cm, 2*cm, 2*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4338ca")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
            ]))
            elements.append(t)
        else:
            elements.append(Paragraph("No opportunities available.", self.styles['BodyText2']))

        elements.append(PageBreak())

        # Research Gaps
        elements.append(Paragraph("Research Gaps", self.styles['SectionHeading']))
        if gaps:
            for g in gaps[:12]:
                elements.append(Paragraph(
                    f"<b>{g.title}</b> — gap score: {g.gap_score:.2f}",
                    self.styles['BodyText2'],
                ))
                elements.append(Paragraph(g.description[:250], self.styles['BodyText2']))
                elements.append(Spacer(1, 0.2*cm))
        else:
            elements.append(Paragraph("No research gaps identified.", self.styles['BodyText2']))

        elements.append(Spacer(1, 0.5*cm))

        # Trends
        elements.append(Paragraph("Emerging Trends", self.styles['SectionHeading']))
        if trends:
            rows = [["Trend", "Category", "Score"]]
            for tr in trends[:15]:
                rows.append([tr.name[:40], tr.category, f"{tr.trend_score:.2f}"])
            t = Table(rows, colWidths=[10*cm, 4*cm, 2*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#059669")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#ecfdf5")]),
            ]))
            elements.append(t)

        doc.build(elements)
        buf.seek(0)
        return buf
