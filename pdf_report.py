# pdf_report.py
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_pdf_report_bytes(name, birth, time_str, texts, energy_pct, timeline):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w,h = letter; margin=50; y=h-50
    c.setFont("Helvetica-Bold",18); c.drawString(margin,y,f"{name} — Destiny Report"); y-=24
    c.setFont("Helvetica",10); c.drawString(margin,y,f"Birth: {birth} {time_str}"); y-=18
    c.setFont("Helvetica-Bold",12); c.drawString(margin,y, texts.get('cover',{}).get('title','Premium Report')); y-=14
    c.setFont("Helvetica",10)
    for line in (texts.get('cover',{}).get('lead','')).splitlines():
        c.drawString(margin,y,line); y-=12
        if y < 80:
            c.showPage(); y = h-50
    c.showPage(); c.save(); buf.seek(0)
    return buf.read()
