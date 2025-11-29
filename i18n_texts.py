# i18n_texts.py
import os, json, requests
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def generate_kr_helper():
    return "한국어 보조: 본 리포트는 오행 상호작용과 일간 강약을 기준으로 작성되었습니다."

def _generate_fallback(analysis, locale='en'):
    pct = analysis.get('percent', {})
    sorted_e = sorted(pct.items(), key=lambda x:-x[1]) if pct else []
    top = sorted_e[0][0] if sorted_e else 'Tree'
    cover = {"title":"Premium Destiny Report","lead":f"Dominant: {top}."}
    summary = {"title":"Four Pillars Summary","lead":f"Dominant energy: {top}.","recommendations":[{"action":"Stabilize routine","why":"Build reserves","timeframe":"30 days"}]}
    return {"cover":cover,"summary":summary,"career":summary,"hiring":summary,"study":summary,"romance":summary,"spouse":summary,"parents":summary,"decade_luck":[{"period":"2026-2035","theme":"Consolidation","advice":"Focus"}],"checklist":[{"action":"Plan","why":"Reason","priority":"high","timeframe":"30 days"}],"short_note":"Use structure.","kr_helper":generate_kr_helper()}

def generate_texts(analysis, locale='en', mode='A'):
    if OPENAI_API_KEY:
        try:
            headers = {"Authorization":f"Bearer {OPENAI_API_KEY}","Content-Type":"application/json"}
            user = f"Percent: {analysis.get('percent',{})}\nLocale:{locale}"
            payload = {"model":"gpt-4o-mini","messages":[{"role":"system","content":"You are an expert Japyeong Jinjeon analyst."},{"role":"user","content":user}],"temperature":0.2,"max_tokens":700}
            r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=12)
            r.raise_for_status()
            content = r.json()['choices'][0]['message']['content']
            data = json.loads(content) if content.strip().startswith("{") else {"cover":{"title":"AI Report","lead":content}}
            data.setdefault('kr_helper', generate_kr_helper())
            return data
        except Exception as e:
            print("OpenAI fallback:", e)
    return _generate_fallback(analysis, locale)
