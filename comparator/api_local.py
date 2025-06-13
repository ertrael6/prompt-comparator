
import httpx

def ask_local(prompt, endpoint="http://localhost:8000/completions"):
    data = {
        "prompt": prompt,
        "max_tokens": 1024
    }
    resp = httpx.post(endpoint, json=data, timeout=30)
    resp.raise_for_status()
    return resp.json().get("completion", "").strip()
