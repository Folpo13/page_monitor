#!/usr/bin/env python3
import requests, hashlib, time, os
from pathlib import Path

# ---- CONFIG ----
URLS = {
    "math_news": "https://www.math.unipd.it/news/tutte/",
    "math_bando": "https://www.math.unipd.it/news/bando-di-concorso-n-5-2025-per-lassegnazione-di-complessivi-10-premi-di-studio-per-liscrizione-alle-lauree-magistrali-del-dipartimento-di-matematica-a-a-2025-2026/"  
}
INTERVAL = 60 * 10  # controlla ogni 10 minuti

# Telegram config
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

# ---- fine config ----

try:
    from plyer import notification
    _HAVE_PLYER = True
except Exception:
    _HAVE_PLYER = False

def get_page_hash(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    norm = " ".join(r.text.split())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()

def notify_desktop(title, message):
    if _HAVE_PLYER:
        notification.notify(title=title, message=message, timeout=10)
    else:
        print(f"[NOTIFY] {title} - {message}")

def notify_telegram(message):
    api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(api, data={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=10)
    except Exception as e:
        print("Errore invio Telegram:", e)

def notify(message):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        notify_telegram(message)
    else:
        notify_desktop("Pagina aggiornata", message)

def get_hashfile(name):
    return Path.home() / f".page_monitor_hash_{name}"

def load_old_hash(name):
    path = get_hashfile(name)
    if path.exists():
        return path.read_text().strip()
    return None

def save_hash(name, h):
    path = get_hashfile(name)
    path.write_text(h)

def main():
    print("Monitor avviato per più URL.")
    old_hashes = {}

    # Carica hash salvati
    for name in URLS:
        old_hashes[name] = load_old_hash(name)

    while True:
        for name, url in URLS.items():
            try:
                current_hash = get_page_hash(url)
            except Exception as e:
                print(f"[{name}] Errore fetch:", e)
                continue

            if old_hashes[name] is None:
                print(f"[{name}] Primo hash salvato.")
                save_hash(name, current_hash)
                old_hashes[name] = current_hash
            elif current_hash != old_hashes[name]:
                msg = f"⚠️ Pagina '{name}' aggiornata: {url}"
                print(msg)
                notify(msg)
                save_hash(name, current_hash)
                old_hashes[name] = current_hash
            else:
                print(f"[{name}] Nessuna modifica. ({time.strftime('%H:%M:%S')})")

        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
