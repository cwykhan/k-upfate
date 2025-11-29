# sexagenary.py
HEAVENLY = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
EARTHLY  = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

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

STEM_ELEMENT = {
    "甲":"Tree","乙":"Tree","丙":"Fire","丁":"Fire","戊":"Earth","己":"Earth",
    "庚":"Metal","辛":"Metal","壬":"Water","癸":"Water"
}
BRANCH_ELEMENT = {
    "子":"Water","丑":"Earth","寅":"Tree","卯":"Tree","辰":"Earth","巳":"Fire",
    "午":"Fire","未":"Earth","申":"Metal","酉":"Metal","戌":"Earth","亥":"Water"
}

def year_ganzhi_from_gregorian(year, month, day):
    if month < 2 or (month == 2 and day < 4):
        y = year - 1
    else:
        y = year
    stem = HEAVENLY[(y - 4) % 10]
    branch = EARTHLY[(y - 4) % 12]
    return stem, branch

def month_ganzhi_from_date(year, month, day):
    m_idx = (month + 10) % 12
    month_branch = EARTHLY[m_idx]
    year_stem_idx = (year - 4) % 10
    month_stem = HEAVENLY[(year_stem_idx*2 + m_idx) % 10]
    return month_stem, month_branch

def julian_day(year, month, day):
    a = (14 - month)//12
    y = year + 4800 - a
    m = month + 12*a - 3
    JDN = day + ((153*m + 2)//5) + 365*y + y//4 - y//100 + y//400 - 32045
    return JDN

def day_ganzhi_from_date(year, month, day):
    jdn = julian_day(year, month, day)
    epoch_jdn = julian_day(1984, 2, 2)
    diff = jdn - epoch_jdn
    idx = diff % 60
    stem = HEAVENLY[idx % 10]
    branch = EARTHLY[idx % 12]
    return stem, branch

def hour_ganzhi_from_time(hour, minute, day_stem=None):
    h = hour
    if h == 23:
        idx = 0
    else:
        idx = (h + 1) // 2
    branch = EARTHLY[idx % 12]
    if day_stem:
        day_idx = HEAVENLY.index(day_stem)
        stem = HEAVENLY[(day_idx*2 + idx) % 10]
    else:
        stem = HEAVENLY[idx % 10]
    return stem, branch
