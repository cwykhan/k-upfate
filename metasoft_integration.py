# metasoft_integration.py
import os, requests
METASOFT_ENDPOINT = os.getenv("METASOFT_ENDPOINT")  # e.g. https://api.metasoft.example/compute
METASOFT_API_KEY = os.getenv("METASOFT_API_KEY")

def call_metasoft(birth_iso):
    if not METASOFT_ENDPOINT or not METASOFT_API_KEY:
        return None
    headers = {"Authorization":f"Bearer {METASOFT_API_KEY}","Content-Type":"application/json"}
    payload = {"birth":birth_iso}
    try:
        r = requests.post(METASOFT_ENDPOINT, headers=headers, json=payload, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Metasoft call failed:", e)
        return None
