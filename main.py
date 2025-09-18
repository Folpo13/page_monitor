#!/usr/bin/env python3
import os
import requests
import hashlib
import subprocess
from pathlib import Path
import time

# === CONFIG ===

# Pagine da monitorare
URLS = {
    "math_news": "https://www.math.unipd.it/news/tutte/",
    "math_bando": "https://www.math.unipd.it/news/bando-di-concorso-n-5-2025-per-lassegnazione-di-complessivi-10-premi-di-studio-per-liscrizione-alle-lauree-magistrali-del-dipartimento-di-matematica-a-a-2025-2026/"  
}

# Cartella dove salvare gli hash
HASH_DIR = Path("hash")
HASH_DIR.mkdir(exist_ok=True)

# Variabili Telegram (da GitHub Secrets)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

# Autore commit automatico
GIT_USER_NAME = "github-actions[bot]"
GIT_USER_EMAIL = "github-actions[bot]@users.noreply.github.com"

# === FUNZIONI ===

def get_page_hash(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    norm = " ".join(r.text.split())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()

def get_hash_path(name):
    return HASH_DIR / f"{name}.hash"

def load_old_hash(name):
    path = get_hash_path(name)
    if path.exists():
        return path.read_text().strip()
    return None

def save_hash(name, h):
    path = get_hash_path(name)
    path.write_text(h)

def notify_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ TELEGRAM_TOKEN o TELEGRAM_CHAT_ID non definiti")
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

def git_commit_push():
    # Configura Git
    subprocess.run(["git", "config", "user.name", GIT_USER_NAME], check=True)
    subprocess.run(["git", "config", "user.email", GIT_USER_EMAIL], check=True)
    
    # Aggiungi i file hash
    subprocess.run(["git", "add", str(HASH_DIR)], check=True)
    
    # Commit e push solo se ci sono cambiamenti
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode != 0:
        subprocess.run(["git", "commit", "-m", "Aggiornamento hash pagine monitorate"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("[GIT] Commit e push effettuati")
    else:
        print("[GIT] Nessun cambiamento da pushare")

# === MAIN ===

def main():
    changes = False
    for name, url in URLS.items():
        try:
            current_hash = get_page_hash(url)
        except Exception as e:
            print(f"[{name}] Errore fetch: {e}")
            continue

        old_hash = load_old_hash(name)
        if old_hash is None:
            print(f"[{name}] Primo salvataggio hash")
            save_hash(name, current_hash)
            changes = True
            continue

        if current_hash != old_hash:
            msg = f"⚠️ La pagina '{name}' è cambiata:\n{url}"
            notify(msg)
            save_hash(name, current_hash)
            changes = True
        else:
            print(f"[{name}] Nessuna modifica.")

    if changes:
        git_commit_push()
    else:
        print("Nessun cambiamento da salvare.")

if __name__ == "__main__":
    main()
