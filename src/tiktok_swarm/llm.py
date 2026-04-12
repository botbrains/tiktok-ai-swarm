"""Ollama LLM interface."""
import httpx
from .config import load_config


def ask(system: str, user: str, temperature: float = 0.7) -> str:
    cfg = load_config()
    url = f"{cfg['ollama_url']}/api/chat"
    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": temperature},
    }
    try:
        resp = httpx.post(url, json=payload, timeout=180.0)
        resp.raise_for_status()
        return resp.json()["message"]["content"]
    except httpx.ConnectError:
        return "[ERROR] Cannot connect to Ollama. Make sure it's running: ollama serve"
    except httpx.HTTPStatusError as e:
        return f"[ERROR] Ollama returned {e.response.status_code}. Is model '{cfg['model']}' pulled?"
    except Exception as e:
        return f"[ERROR] {e}"
