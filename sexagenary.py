# sexagenary.py
# Convert Gregorian date/time -> Heavenly Stem & Earthly Branch (approx. algorithm)
# Uses the standard sexagenary algorithms from references (Wikipedia style).
# NOTE: For production-grade month-stem/branch accuracy use solar terms or Metasoft API.
from math import floor
from datetime import datetime, timezone

HEAVENLY_STEMS = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
EARTHLY_BRANCHES = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']

def year_ganzhi(year):
    """
    Year stem/branch:
    Stem index = (year - 4) % 10
    Branch index = (year - 4) % 12
    (Because 4 AD is a甲子 base in common formula)
    """
    s = HEAVENLY_STEMS[(year - 4) % 10]
    b = EARTHLY_BRANCHES[(year - 4) % 12]
    return s, b

def julian_day_number(y, m, d):
    # Convert Gregorian date to Julian Day Number (integer)
    a = (14 - m)//12
    y2 = y + 4800 - a
    m2 = m + 12*a - 3
    jd = d + ((153*m2 + 2)//5) + 365*y2 + y2//4 - y2//100 + y2//400 - 32045
    return jd

def day_ganzhi(year, month, day):
    """
    Compute day Ganzhi (stem+branch) using algorithm:
    SB = (y + c + m + d) mod 60
    where y, c, m per standard formulas (see Wikipedia algorithm).
    Implementation follows the algorithm described on the Sexagenary cycle page.
    Returns (stem, branch) for the day.
    """
    Y = year
    # y calculation
    ym = Y % 400
    y_mod80 = ym % 80
    y_calc = ( (y_mod80 % 12) * 5 + (y_mod80 // 4) ) % 60

    # century term for Gregorian calendar
    c = (Y // 400) - (Y // 100) + 10

    # month term m (algorithm uses month index with adjustments)
    # Using the formula from references:
    M = month
    if M == 1 or M == 2:
        i = 5 if not ( (Y % 4 == 0 and Y % 100 != 0) or (Y % 400 == 0) ) else 6
    else:
        i = 0
    m_term = ( ( (M + 1) % 2 ) * 30 + int(0.6 * (M + 1) - 3) ) - i

    SB = (y_calc + c + m_term + day) % 60
    stem = HEAVENLY_STEMS[SB % 10]
    branch = EARTHLY_BRANCHES[SB % 12]
    return stem, branch

def hour_branch_from_hour(hour, minute=0):
    """
    Map clock hour (24h) to Earthly Branch for hour pillar.
    Note: Chinese hours are two-hour blocks starting at 23:00-01:00 as 子
    We'll map exact hour (0-23) to branch:
    23-0 -> 子 (23:00-00:59 and 00:00-00:59 considered in 子)
    However classical mapping: 23:00-00:59 is 子 hour, 01:00-02:59 丑, etc.
    We'll use ranges: 23-0 -> 子, 1-2->丑, 3-4->寅, ...
    """
    h = int(hour)
    # Normalize: hour 23 -> 23, hour 0 -> 0 => both should be in 子 or treat 0 as within 子 block
    if h == 23 or h == 0:
        return '子'
    # Blocks: 1-2: 丑, 3-4: 寅, 5-6: 卯, 7-8: 辰, 9-10: 巳, 11-12: 午, 13-14: 未, 15-16: 申, 17-18: 酉, 19-20: 戌, 21-22: 亥
    mapping = {
        1: '丑', 2: '丑',
        3: '寅', 4: '寅',
        5: '卯', 6: '卯',
        7: '辰', 8: '辰',
        9: '巳', 10: '巳',
        11: '午', 12: '午',
        13: '未', 14: '未',
        15: '申', 16: '申',
        17: '酉', 18: '酉',
        19: '戌', 20: '戌',
        21: '亥', 22: '亥'
    }
    return mapping.get(h, '子')

def month_ganzhi_approx(year, month):
    """
    Approximate month stem/branch.
    Accurate month stem needs solar terms; this is a pragmatic mapping:
    - Month branch: month 1 (Jan) -> 丑, 2 -> 寅 ... (depends on lunar/solar start)
    This is an approximation: users should use Metasoft for production.
    We'll map approximate branch index: (month + 1) % 12 -> use as placeholder.
    For stem we use rule: month_stem_index = (year_stem_index*2 + month_index) % 10
    """
    # month_index: Jan=1 -> we choose mapping where Feb->寅 etc; but keep simple:
    branch_index = (month + 10) % 12  # chosen to approximate typical mapping
    branch = EARTHLY_BRANCHES[branch_index]
    # year stem index
    ystem_idx = (year - 4) % 10
    month_idx = (month - 1)  # 0..11
    stem_idx = (ystem_idx * 2 + month_idx) % 10
    stem = HEAVENLY_STEMS[stem_idx]
    return stem, branch

def full_ganzhi_from_datetime(dt):
    """
    Given a datetime (aware or naive), return dict:
    {
      'year_stem','year_branch',
      'month_stem','month_branch',
      'day_stem','day_branch',
      'hour_stem','hour_branch'
    }
    """
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    y,m,d = dt.year, dt.month, dt.day
    hour = dt.hour

    ys, yb = year_ganzhi(y)
    ds, db = day_ganzhi(y, m, d)
    ms, mb = month_ganzhi_approx(y, m)
    hb = hour_branch_from_hour(hour)

    # Hour stem requires day-stem context: hour stem is related to day stem.
    # Simplified: compute hour stem by mapping day-stem index & hour-block:
    day_stem_idx = HEAVENLY_STEMS.index(ds)
    # Each day-stem has its own sequence; formula for hour stem index:
    # hourStemIndex = (dayStemIndex*2 + hourBlockIndex) % 10
    # hourBlockIndex: 0..11 for the 12 two-hour blocks, compute from branch->index
    hour_block_index = EARTHLY_BRANCHES.index(hb)
    hour_stem_idx = (day_stem_idx*2 + hour_block_index) % 10
    hs = HEAVENLY_STEMS[hour_stem_idx]

    return {
        'year_stem': ys, 'year_branch': yb,
        'month_stem': ms, 'month_branch': mb,
        'day_stem': ds, 'day_branch': db,
        'hour_stem': hs, 'hour_branch': hb
    }

# Quick test when run directly
if __name__ == '__main__':
    now = datetime.now()
    print(full_ganzhi_from_datetime(now))
