# pdf_report.py
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from datetime import datetime

def generate_pdf_report(analysis, out_path):
    c = canvas.Canvas(out_path, pagesize=A4)
    w, h = A4
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20*mm, h - 20*mm, "Destiny Analysis Report")
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, h - 26*mm, f"Generated: {datetime.utcnow().isoformat()} UTC")
    # Four Pillars
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20*mm, h - 40*mm, "Four Pillars")
    c.setFont("Helvetica", 11)
    parsed = analysis.get('parsed', {})
    c.drawString(25*mm, h - 48*mm, f"Year: {parsed.get('year_stem','-')} {parsed.get('year_branch','-')}")
    c.drawString(25*mm, h - 56*mm, f"Month: {parsed.get('month_stem','-')} {parsed.get('month_branch','-')}")
    c.drawString(25*mm, h - 64*mm, f"Day: {parsed.get('day_stem','-')} {parsed.get('day_branch','-')}")
    c.drawString(25*mm, h - 72*mm, f"Hour: {parsed.get('hour_stem','-')} {parsed.get('hour_branch','-')}")

    # Energies
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20*mm, h - 88*mm, "Element Distribution (%)")
    c.setFont("Helvetica", 11)
    y = h - 96*mm
    perc = analysis.get('percent', {})
    for k,v in perc.items():
        c.drawString(25*mm, y, f"{k}: {v}%")
        y -= 8*mm

    # Interpretation
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20*mm, y - 6*mm, "Interpretation")
    c.setFont("Helvetica", 10)
    y -= 14*mm
    texts = analysis.get('interpretations', {})
    for key in ('intro','career','wealth','relationship','study'):
        val = texts.get(key, '')
        # wrap text manually
        max_width = w - 40*mm
        lines = []
        words = val.split()
        line = ''
        for word in words:
            if c.stringWidth(line + ' ' + word, "Helvetica", 10) < max_width:
                line = (line + ' ' + word).strip()
            else:
                lines.append(line); line = word
        if line: lines.append(line)
        for ln in lines:
            c.drawString(25*mm, y, ln)
            y -= 6*mm
    c.showPage()
    c.save()
    return out_path
