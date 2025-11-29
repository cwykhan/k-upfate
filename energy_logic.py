# energy_logic.py
from sexagenary import STEM_ELEMENT, BRANCH_ELEMENT, HIDDEN_STEMS
import math

def compute_five_energy(pillars):
    counts = {"Tree":0.0,"Fire":0.0,"Earth":0.0,"Metal":0.0,"Water":0.0}
    for k in ("year","month","day","hour"):
        s = pillars[k]["sky"]
        e = STEM_ELEMENT.get(s, None)
        if e: counts[e] += 1.0
    for k in ("year","month","day","hour"):
        b = pillars[k]["earth"]
        e = BRANCH_ELEMENT.get(b, None)
        if e: counts[e] += 0.6
        hs = HIDDEN_STEMS.get(b, [])
        for h in hs:
            he = STEM_ELEMENT.get(h, None)
            if he: counts[he] += 0.3
    total = sum(counts.values())
    if total == 0:
        return {k:0.0 for k in counts}
    pct = {k: round((v/total)*100,1) for k,v in counts.items()}
    return pct

def dominant_element(energy_pct):
    items = sorted(energy_pct.items(), key=lambda x:-x[1])
    return items[0][0] if items else None

def make_timeline(center_hour=12, peak=75, base=10):
    timeline=[]
    for h in range(24):
        val = base + peak*math.exp(-((h-center_hour)**2)/(2*16))
        timeline.append(int(round(val)))
    return timeline

def compute_useful_support(energy_pct):
    # naive mapping: dominant is Useful; other mapping as Supporting/Critical/Threat
    dom = dominant_element(energy_pct)
    supporting = None
    critical = None
    threat = None
    order = sorted(energy_pct.items(), key=lambda x:-x[1])
    if len(order)>1:
        supporting = order[1][0]
    if len(order)>2:
        critical = order[2][0]
    if len(order)>3:
        threat = order[3][0]
    return {"useful":dom,"supporting":supporting,"critical":critical,"threat":threat}
