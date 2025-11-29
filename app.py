# app.py
import os, io
from datetime import datetime
from flask import Flask, request, render_template, send_file, redirect, url_for
from sexagenary import year_ganzhi_from_gregorian, month_ganzhi_from_date, day_ganzhi_from_date, hour_ganzhi_from_time
from energy_logic import compute_five_energy, make_timeline, compute_useful_support
from i18n_texts import generate_texts
from pdf_report import create_pdf_report_bytes
from metasoft_integration import call_metasoft

app = Flask(__name__, template_folder='templates', static_folder='static')

PADDLE_VENDOR_ID = os.getenv("PADDLE_VENDOR_ID", "268309")
PADDLE_PRICE_ID = os.getenv("PADDLE_PRICE_ID", "pri_01kb6fk39mh0k5e6gnf69zaag5")

BRANCH_ENG = {
    "子":"w", "丑":"e", "寅":"T", "卯":"t", "辰":"E", "巳":"F", "午":"f",
    "未":"e", "申":"M", "酉":"m", "戌":"E", "亥":"W"
}

def branch_to_eng(b):
    return BRANCH_ENG.get(b, b)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    name = request.form.get("name","Anonymous")
    birth_raw = request.form.get("birth") or request.form.get("birth_date") or "1976-09-04"
    hour = int(request.form.get("hour") or 1)
    minute = int(request.form.get("minute") or 0)
    lang = request.form.get("lang","en")
    try:
        y,m,d = map(int, birth_raw.split("-"))
    except:
        y,m,d = 1976,9,4
    # Try Metasoft if enabled
    meta = call_metasoft(f"{y:04d}-{m:02d}-{d:02d}T{hour:02d}:{minute:02d}:00Z")
    if meta and isinstance(meta, dict):
        # map Metasoft response to pillars if provided
        try:
            pillars = {
                "year":{"sky":meta['year']['sky'],"earth":meta['year']['earth'],"eng_year":branch_to_eng(meta['year']['earth'])},
                "month":{"sky":meta['month']['sky'],"earth":meta['month']['earth'],"eng_month":branch_to_eng(meta['month']['earth'])},
                "day":{"sky":meta['day']['sky'],"earth":meta['day']['earth'],"eng_day":branch_to_eng(meta['day']['earth'])},
                "hour":{"sky":meta['hour']['sky'],"earth":meta['hour']['earth'],"eng_hour":branch_to_eng(meta['hour']['earth'])}
            }
        except Exception:
            meta = None
    if not meta:
        y_stem, y_branch = year_ganzhi_from_gregorian(y,m,d)
        mo_stem, mo_branch = month_ganzhi_from_date(y,m,d)
        d_stem, d_branch = day_ganzhi_from_date(y,m,d)
        h_stem, h_branch = hour_ganzhi_from_time(hour, minute, day_stem=d_stem)
        pillars = {
            "year":{"sky":y_stem,"earth":y_branch,"eng_year":branch_to_eng(y_branch)},
            "month":{"sky":mo_stem,"earth":mo_branch,"eng_month":branch_to_eng(mo_branch)},
            "day":{"sky":d_stem,"earth":d_branch,"eng_day":branch_to_eng(d_branch)},
            "hour":{"sky":h_stem,"earth":h_branch,"eng_hour":branch_to_eng(h_branch)}
        }
    energy = compute_five_energy(pillars)
    timeline = make_timeline(center_hour=12)
    support = compute_useful_support(energy)
    texts = generate_texts({"percent":energy,"timeline24":timeline,"day_element":pillars["day"]["sky"]}, locale=lang)
    interpretation = texts.get("summary",{}).get("lead","Auto analysis")
    return render_template("result.html", name=name, birth=f"{y:04d}-{m:02d}-{d:02d}", time=f"{hour:02d}:{minute:02d}", pillars=pillars, energy=energy, timeline=timeline, texts=texts, interpretation=interpretation, paddle_vendor=PADDLE_VENDOR_ID, paddle_price=PADDLE_PRICE_ID)

@app.route("/download/pdf", methods=["POST"])
def download_pdf():
    name = request.form.get("name","Anonymous")
    birth = request.form.get("birth","1976-09-04")
    time_str = request.form.get("time","01:00")
    texts = generate_texts({"percent":{}}, locale='en')
    pdf = create_pdf_report_bytes(name, birth, time_str, texts, {}, [])
    return send_file(io.BytesIO(pdf), download_name=f"{name}_destiny.pdf", as_attachment=True, mimetype='application/pdf')

@app.route("/premium/<name>", methods=["GET"])
def premium(name):
    return render_template("premium.html", name=name, paddle_vendor=PADDLE_VENDOR_ID, paddle_price=PADDLE_PRICE_ID)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT",5000)))
