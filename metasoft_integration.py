import os, requests
METASOFT_ENDPOINT = os.getenv("METASOFT_ENDPOINT")
METASOFT_API_KEY = os.getenv("METASOFT_API_KEY")

def call_metasoft(birth_date, birth_time, tz='Asia/Seoul'):
    if not METASOFT_ENDPOINT or not METASOFT_API_KEY:
        return None
    payload = {"date": birth_date, "time": birth_time, "tz": tz}
    headers = {"Authorization": f"Bearer {METASOFT_API_KEY}", "Content-Type":"application/json"}
    try:
        r = requests.post(METASOFT_ENDPOINT, json=payload, headers=headers, timeout=12)
        r.raise_for_status()
        ms = r.json()
        parsed = {
            'year_stem': ms.get('year',{}).get('heavenly') or ms.get('tg_year'),
            'year_branch': ms.get('year',{}).get('earthly') or ms.get('dz_year'),
            'month_stem': ms.get('month',{}).get('heavenly') or ms.get('tg_month'),
            'month_branch': ms.get('month',{}).get('earthly') or ms.get('dz_month'),
            'day_stem': ms.get('day',{}).get('heavenly') or ms.get('tg_day'),
            'day_branch': ms.get('day',{}).get('earthly') or ms.get('dz_day'),
            'hour_stem': ms.get('hour',{}).get('heavenly') or ms.get('tg_hour'),
            'hour_branch': ms.get('hour',{}).get('earthly') or ms.get('dz_hour'),
            'hidden_stems': ms.get('hidden_stems') or ms.get('zang_gan') or {}
        }
        return parsed
    except Exception as e:
        print("Metasoft error:", e)
        return None
