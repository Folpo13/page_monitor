#!/usr/bin/env python3
import os
import requests
import hashlib
import time
from pathlib import Path

# === CONFIG ===

# URL delle pagine da monitorare (nome logico : URL)
URLS = {
    "math_news": "https://www.math.unipd.it/news/tutte/",
    "math_bando": "https://www.math.unipd.it/news/bando-di-concorso-n-5-2025-per-lassegnazione-di-complessivi-10-premi-di-studio-per-liscrizione-alle-lauree-magistrali-del-dipartimento-di-matematica-a-a-2025-2026/"  
}

# Cartella dove salvare gli hash
HASH_DIR = Path("hash")
HASH_DIR.mkdir(exist_ok=True)

# Leggi le variabili di ambiente (se usate in GitHub Actions)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

# === FUNZIONI ===

def get_page_hash(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    norm = " ".join(r.text.split())  # normalizza whitespace
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()

def get_hash_path(name):
    return HASH_DIR / f"{name}.hash"

def load_old_hash(name):
    path = get_hash_path(name)
    if path.exists():
        return path.read_text().strip()
    return None

def save_hash(name, h):
    get_hash_path(name).write_text(h)

def notify_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ TELEGRAM_TOKEN o TELEGRAM_CHAT_ID non definiti.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"Errore invio notifica Telegram: {e}")

def notify(message):
    print(f"[NOTIFICA] {message}")
    notify_telegram(message)

# === MAIN ===

def main():
    for name, url in URLS.items():
        try:
            current_hash = get_page_hash(url)
        except Exception as e:
            print(f"[{name}] Errore durante fetch: {e}")
            continue

        old_hash = load_old_hash(name)

        if old_hash is None:
            print(f"[{name}] Primo salvataggio hash.")
            save_hash(name, current_hash)
            continue

        if current_hash != old_hash:
            msg = f"⚠️ La pagina '{name}' è cambiata:\n{url}"
            notify(msg)
            save_hash(name, current_hash)
        else:
            print(f"[{name}] Nessuna modifica. ({time.strftime('%H:%M:%S')})")

if __name__ == "__main__":
    main()
