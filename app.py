# app.py — Flask server with internal ganzhi (四柱) calculator (no external API)
import os, json, io, base64
from datetime import datetime, timedelta
from flask import Flask, request, render_template, send_file, url_for, redirect
import math
from i18n_texts import generate_texts
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image

app = Flask(__name__, template_folder='templates', static_folder='static')

# Env
PADDLE_VENDOR_ID = os.getenv("PADDLE_VENDOR_ID", "268309")
PADDLE_PRICE_ID = os.getenv("PADDLE_PRICE_ID", "pri_01kb6fk39mh0k5e6gnf69zaag5")
PADDLE_TEST_MODE = os.getenv("PADDLE_TEST_MODE", "1")  # keep '1' while testing locally

# --- Heavenly Stems & Earthly Branches ----
HEAVENLY = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
EARTHLY  = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

# User's English notation mapping from Model Set Context (kept exactly)
BRANCH_ENG = {
    "子":"w", "丑":"e", "寅":"T", "卯":"t", "辰":"E", "巳":"F", "午":"f",
    "未":"e", "申":"M", "酉":"m", "戌":"E", "亥":"W"
}
# Note: mapping contains duplicates per user's earlier rule — we preserve it.

# --- Utilities: sexagenary year (common formula) ---
# For year: stem_index = (year - 4) % 10, branch_index = (year - 4) %12
def year_ganzhi_from_gregorian(year, month, day):
    # If before lunar new year, many systems treat as previous Ganzhi year.
    # Simple conservative approach: treat solar year boundary at Feb 4 (approx. Lichun).
    # If date < Feb 4 -> use year-1 for Ganzhi year
    if month < 2 or (month == 2 and day < 4):
        y = year - 1
    else:
        y = year
    stem = HEAVENLY[(y - 4) % 10]
    branch = EARTHLY[(y - 4) % 12]
    return stem, branch

# For month ganzhi approximate (standard rule: month stem depends on year stem and lunar month).
# We'll use conventional mapping: month_branch starts from 丑 as month1 for lunar; but to keep simple: use solar month offset from Tiger (寅) at lunar new year.
def month_ganzhi_from_date(year, month, day):
    # Approximate: month_branch_index = (month + 1) % 12  (Jan -> 丑 etc)
    # Use mapping: lunar month 1 roughly starts at Feb (after Lichun), so shift by 1
    # We'll compute an index that gives a repeatable month branch
    # This is an approximation—accurate month Ganzhi ideally requires lunar calendar.
    m_idx = (month + 10) % 12  # heuristic shift to align Feb->寅-ish
    month_branch = EARTHLY[m_idx]
    # month stem: (year_stem_index*2 + m_idx) % 10 approximated
    year_stem_idx = (year - 4) % 10
    month_stem = HEAVENLY[(year_stem_idx*2 + m_idx) % 10]
    return month_stem, month_branch

# Day ganzhi approximate using known epoch (Jan 1, 1900 is 庚子 day index known?) — We'll compute via Julian Day Number
def julian_day(year, month, day):
    # Fliegel-Van Flandern algorithm (integer)
    a = (14 - month)//12
    y = year + 4800 - a
    m = month + 12*a - 3
    JDN = day + ((153*m + 2)//5) + 365*y + y//4 - y//100 + y//400 - 32045
    return JDN

def day_ganzhi_from_date(year, month, day):
    # The sexagenary day cycle: reference 1984-02-02 is a known 甲子? But robust reference:
    # Use known JDN offset: JDN 2444239 = 1980-01-01 (we can compute offset so day0 maps to a stem/branch)
    # Commonly, day 1984-02-02 corresponds to 甲子 (cycle start). We'll instead use 1984-02-04 (jiazi) — to be consistent, pick an epoch.
    # We'll pick epoch JDN0 for 1984-02-02 as JiaZi.
    # Compute JDN difference and map to 60-cycle.
    jdn = julian_day(year, month, day)
    epoch_jdn = julian_day(1984, 2, 2)  # chosen reference (甲子)
    diff = jdn - epoch_jdn
    idx = diff % 60
    stem = HEAVENLY[idx % 10]
    branch = EARTHLY[idx % 12]
    return stem, branch

# Hour ganzhi: hour branch mapping standard: 23-1=子, 1-3=丑? Actually: 23-1:子(23~0:59)
def hour_ganzhi_from_time(hour, minute):
    # Chinese double-hour index: 23:00-00:59 -> 子(0), 01:00-02:59->丑(1), 03-04:59->寅 ...
    # compute index:
    h = hour
    if h == 23:
        idx = 0
    else:
        idx = (h + 1) // 2
    branch = EARTHLY[idx % 12]
    # hour stem: relative to day stem — simplified: use (day_stem_index*2 + idx) % 10
    # But we don't have day stem here; will compute at caller.
    return branch, idx

# Hidden stems (지장간) basic lookup per user-specified mapping (from Model Set Context)
HIDDEN_STEMS = {
    "子": ["壬","癸"],
    "丑": ["癸","辛","己"],
    "寅": ["戊","丙","甲"],
    "卯": ["甲","乙"],
    "辰": ["乙","癸","戊"],
    "巳": ["戊","庚","丙"],
    "午": ["丙","丁","己"],
    "未": ["丁","乙","己"],
    "申": ["戊","壬","庚"],
    "酉": ["辛","庚"],
    "戌": ["辛","丁","戊"],
    "亥": ["戊","甲","壬"]
}

# basic five-element assignment for stems (rough)
STEM_ELEMENT = {
    "甲":"Tree","乙":"Tree","丙":"Fire","丁":"Fire","戊":"Earth","己":"Earth",
    "庚":"Metal","辛":"Metal","壬":"Water","癸":"Water"
}
BRANCH_ELEMENT = {
    "子":"Water","丑":"Earth","寅":"Tree","卯":"Tree","辰":"Earth","巳":"Fire",
    "午":"Fire","未":"Earth","申":"Metal","酉":"Metal","戌":"Earth","亥":"Water"
}

# Convert branch to user's English symbol
def branch_to_eng(b):
    return BRANCH_ENG.get(b, b)

# compute five-energy distribution by counting occurrences in four pillars + hidden stems
def compute_five_energy(pillars):
    counts = {"Tree":0,"Fire":0,"Earth":0,"Metal":0,"Water":0}
    # sky stems
    for k in ("year","month","day","hour"):
        s = pillars[k]["sky"]
        e = STEM_ELEMENT.get(s, None)
        if e: counts[e] += 1.0
    # earth branches
    for k in ("year","month","day","hour"):
        b = pillars[k]["earth"]
        e = BRANCH_ELEMENT.get(b, None)
        if e: counts[e] += 0.6
        # hidden stems
        hs = HIDDEN_STEMS.get(b, [])
        for h in hs:
            he = STEM_ELEMENT.get(h, None)
            if he: counts[he] += 0.3
    # normalize to percentages
    total = sum(counts.values())
    if total == 0:
        return {k:0.0 for k in counts}
    pct = {k: round((v/total)*100,1) for k,v in counts.items()}
    return pct

# timeline: produce a smooth bell-shaped curve centered around hour useful energy (based on dominant element)
def make_timeline(pillars):
    # pick a dominant hour from hour heavenly stem presence approximate
    # for simplicity, center at 12 (noon), scale by UsefulEnergy if present
    timeline = []
    for h in range(24):
        # simple bell curve centered at 12
        val = 10 + 70 * math.exp(-((h-12)**2)/(2*5.0))
        timeline.append(int(val))
    return timeline

# --- main route & analysis ---
@app.route('/', methods=['GET'])
def index():
    return render_template('index_lang.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    name = request.form.get('name') or "Anonymous"
    birth = request.form.get('birth') or request.form.get('birth_date') or "1976-09-04"
    hour = int(request.form.get('hour') or "1")
    minute = int(request.form.get('minute') or "0")
    # parse date
    try:
        y,m,d = map(int, birth.split('-'))
    except Exception:
        y,m,d = 1976,9,4
    # compute pillars
    y_stem, y_branch = year_ganzhi_from_gregorian(y,m,d)
    mo_stem, mo_branch = month_ganzhi_from_date(y,m,d)
    d_stem, d_branch = day_ganzhi_from_date(y,m,d)
    h_branch, h_idx = hour_ganzhi_from_time(hour, minute)
    # compute hour stem approx using day stem index
    day_stem_idx = HEAVENLY.index(d_stem)
    h_stem = HEAVENLY[(day_stem_idx*2 + h_idx) % 10]
    pillars = {
        "year":{"sky":y_stem,"earth":y_branch,"eng_year":branch_to_eng(y_branch)},
        "month":{"sky":mo_stem,"earth":mo_branch,"eng_month":branch_to_eng(mo_branch)},
        "day":{"sky":d_stem,"earth":d_branch,"eng_day":branch_to_eng(d_branch)},
        "hour":{"sky":h_stem,"earth":h_branch,"eng_hour":branch_to_eng(h_branch)}
    }
    energy = compute_five_energy(pillars)
    timeline = make_timeline(pillars)
    texts = generate_texts({"percent":energy,"timeline24":timeline,"day_element":pillars["day"]["sky"]}, locale=request.form.get('lang','en'))
    # render
    return render_template('result_lang.html',
                           name=name,
                           birth=f"{y:04d}-{m:02d}-{d:02d}",
                           time=f"{hour:02d}:{minute:02d}",
                           pillars=pillars,
                           energy=energy,
                           timeline=timeline,
                           texts=texts,
                           interpretation="Auto analysis (internal engine). For more accuracy, enable Metasoft integration.")

# premium page
@app.route('/premium/<name>', methods=['GET'])
def premium(name):
    return render_template('premium_pay.html', name=name, paddle_vendor=PADDLE_VENDOR_ID, price_id=PADDLE_PRICE_ID)

# sample PDF download
@app.route('/download/test_pdf', methods=['GET'])
def download_test_pdf():
    name='Sample'; birth='1976-09-04'; time_str='01:00'
    analysis = {"percent":{"Tree":60,"Fire":25,"Earth":5,"Metal":5,"Water":5},"timeline24":[10]*24}
    texts = generate_texts(analysis, locale='en')
    pdf = create_pdf_report_bytes(name, birth, time_str, texts, analysis['timeline24'])
    return send_file(io.BytesIO(pdf), download_name="sample_destiny.pdf", as_attachment=True, mimetype='application/pdf')

# minimal PDF generation (reused from i18n_texts pattern)
def create_pdf_report_bytes(name,birth,time_str,texts,timeline):
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=letter)
    w,h = letter; margin=50; y=h-50
    c.setFont("Helvetica-Bold",16); c.drawString(margin,y,f"Destiny Report — {name}"); y-=18
    c.setFont("Helvetica",10); c.drawString(margin,y,f"Birth: {birth} {time_str}"); y-=20
    c.setFont("Helvetica-Bold",12); c.drawString(margin,y, texts.get('cover',{}).get('title','Premium Report')); y-=14
    c.setFont("Helvetica",10)
    for line in (texts.get('cover',{}).get('lead','')).splitlines(): c.drawString(margin,y,line); y-=12
    c.showPage(); c.save(); buf.seek(0); return buf.read()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv("PORT","5000")))
