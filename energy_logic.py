# energy_logic.py  (수정/보강)
from collections import Counter
from sexagenary import full_ganzhi_from_datetime

ELEMENTS = ['Tree','Fire','Earth','Metal','Water']

# 천간(간) -> element 매핑 (Korean/Chinese to English)
STEM_TO_ELEMENT = {
  '甲':'Tree','乙':'Tree',
  '丙':'Fire','丁':'Fire',
  '戊':'Earth','己':'Earth',
  '庚':'Metal','辛':'Metal',
  '壬':'Water','癸':'Water'
}

BRANCH_HIDDEN = {
  '子': ['壬','癸'],
  '丑': ['癸','辛','己'],
  '寅': ['戊','丙','甲'],
  '卯': ['甲','乙'],
  '辰': ['乙','癸','戊'],
  '巳': ['戊','庚','丙'],
  '午': ['丙','丁','己'],
  '未': ['丁','乙','己'],
  '申': ['戊','壬','庚'],
  '酉': ['庚','辛'],
  '戌': ['辛','丁','戊'],
  '亥': ['戊','甲','壬']
}

DEFAULT_WEIGHTS = {
    'year_branch': 0.10,
    'month_branch': 0.375,
    'day_branch': 0.375,
    'hour_branch': 0.15
}

def calculate_base_counts(parsed_chart):
    counts = {e:0.0 for e in ELEMENTS}
    # sky stems
    for pos in ['year_stem','month_stem','day_stem','hour_stem']:
        s = parsed_chart.get(pos)
        if s and s in STEM_TO_ELEMENT:
            counts[STEM_TO_ELEMENT[s]] += 1.0

    # branch hidden stems weighting
    for pos, weight in DEFAULT_WEIGHTS.items():
        branch = parsed_chart.get(pos)
        if not branch:
            continue
        hidden = parsed_chart.get('hidden_stems', {}).get(branch, BRANCH_HIDDEN.get(branch, []))
        if hidden:
            share = weight / len(hidden)
            for hs in hidden:
                e = STEM_TO_ELEMENT.get(hs)
                if e:
                    counts[e] += share
    return counts

def compute_percentages(counts):
    total = sum(counts.values()) or 1.0
    perc = {k: round((v/total)*100,1) for k,v in counts.items()}
    return perc

def determine_daymaster_strength(parsed_chart, perc):
    day_stem = parsed_chart.get('day_stem')
    day_elem = STEMPL = None
    if day_stem:
        day_elem = STEMPL = STEMP = STEMP = None
    # safer:
    day_elem = STEMPL = None
    if day_stem:
        day_elem = STEM_TO_ELEMENT.get(day_stem)
    dm_score = perc.get(day_elem, 0.0) if day_elem else 0.0
    status = 'Strong' if dm_score >= 40.0 else 'Weak'
    return day_elem, dm_score, status

GENERATE = {'Tree':'Fire','Fire':'Earth','Earth':'Metal','Metal':'Water','Water':'Tree'}
CONTROL = {'Tree':'Metal','Fire':'Water','Earth':'Tree','Metal':'Fire','Water':'Earth'}

def select_energies(perc, day_elem, status):
    useful=None; supporting=None
    if not day_elem:
        useful = max(perc.items(), key=lambda x:x[1])[0]
        supporting = useful
    else:
        if status=='Strong':
            ctrl = CONTROL.get(day_elem)
            drain = GENERATE.get(day_elem)
            if ctrl and perc.get(ctrl,0) >= perc.get(drain,0):
                useful = ctrl
            else:
                useful = drain or ctrl
            supporting = GENERATE.get(useful) if useful else None
        else:
            gen = GENERATE.get(day_elem)
            useful = gen or day_elem
            supporting = day_elem
    sorted_by_perc = sorted(perc.items(), key=lambda x:-x[1])
    critical=None; threat=None
    for el,p in sorted_by_perc:
        if el not in (useful, supporting) and critical is None:
            critical = el
        elif el not in (useful, supporting, critical) and threat is None:
            threat = el
    for el in ELEMENTS:
        if critical is None and el not in (useful, supporting):
            critical = el
        if threat is None and el not in (useful, supporting, critical):
            threat = el
    return {'UsefulEnergy': useful, 'SupportingEnergy': supporting, 'CriticalEnergy': critical, 'ThreatEnergy': threat}

def build_24h_timeline(useful_element=None):
    import math
    arr=[]
    base=45
    for h in range(24):
        val = base + 35 * math.cos(((h-12)/24.0)*2*math.pi) * 0.9
        arr.append(round(max(0,min(100,val)),1))
    return arr

def analyze_chart_with_datetime(dt):
    # dt: datetime instance or iso string
    if isinstance(dt, str):
        from datetime import datetime
        dt = datetime.fromisoformat(dt)
    parsed = full_ganzhi_from_datetime(dt)  # from sexagenary.py
    counts = calculate_base_counts(parsed)
    perc = compute_percentages(counts)
    day_elem, dm_score, status = determine_daymaster_strength(parsed, perc)
    energies = select_energies(perc, day_elem, status)
    timeline = build_24h_timeline(energies.get('UsefulEnergy'))
    return {
        'parsed': parsed,
        'counts': counts,
        'percent': perc,
        'day_element': day_elem,
        'day_score': dm_score,
        'day_status': status,
        **energies,
        'timeline24': timeline
    }
