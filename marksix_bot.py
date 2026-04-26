import re
import os
import json
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
JACKPOT_THRESHOLD = 40_000_000
STATE_FILE = "last_notified.json"

def get_estimated_jackpot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
            locale="en-HK"
        )
        page = context.new_page()
        print("Opening HKJC Mark Six page (EN)...")
        page.goto("https://bet.hkjc.com/en/marksix", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=20000)

        text = page.inner_text("body")
        print(f"Body text preview: {text[:500]}")
        browser.close()

        # 按精確度排列，唔用 broad fallback
        patterns = [
            r'[Ee]stimated\s+1st\s+[Dd]ivision\s+[Pp]rize\s+[Ff]und\s*\$?([\d,]+)',
            r'1st\s+[Dd]ivision\s+[Pp]rize\s+[Ff]und\s*\$?([\d,]+)',
            r'[Ee]st(?:imated)?\s*[Jj]ackpot\s*[Ff]und\s*\$?([\d,]+)',
            r'[Ee]st(?:imated)?\s*[Jj]ackpot\s*\$?([\d,]+)',
        ]

        for pat in patterns:
            m = re.search(pat, text)
            if m:
                amount = int(m.group(1).replace(",", ""))
                if amount >= 5_000_000:
                    print(f"Found jackpot: ${amount:,}")
                    return amount

        print("Jackpot amount not found.")
        return None

def load_last_notified():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            return data.get("amount", 0)
    return 0

def save_last_notified(amount):
    with open(STATE_FILE, "w") as f:
        json.dump({"amount": amount}, f)

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    print(f"Telegram: {resp.status_code}")

def main():
    print("=== Mark Six Jackpot Checker ===")
    amount = get_estimated_jackpot()

    if amount is None:
        print("Failed to retrieve jackpot amount.")
        return

    last_notified = load_last_notified()
    print(f"Current: ${amount:,} | Last notified: ${last_notified:,} | Threshold: ${JACKPOT_THRESHOLD:,}")

    if amount >= JACKPOT_THRESHOLD and amount != last_notified:
        send_telegram(
            f"🎰 <b>Mark Six Jackpot Alert!</b>\n"
            f"Estimated Jackpot Fund: <b>${amount:,}</b>\n"
            f"Threshold exceeded: ${JACKPOT_THRESHOLD:,}\n"
            f"https://bet.hkjc.com/en/marksix"
        )
        save_last_notified(amount)
        print(f"Notified! Saved new amount: ${amount:,}")
    elif amount < JACKPOT_THRESHOLD:
        save_last_notified(0)
        print("Below threshold, state reset.")
    else:
        print(f"Already notified for ${amount:,}, skipping.")

main()
