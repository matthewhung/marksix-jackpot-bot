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
            locale="zh-HK"
        )
        page = context.new_page()
        print("Opening HKJC Mark Six page...")
        page.goto("https://bet.hkjc.com/marksix/", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=20000)

        text = page.inner_text("body")
        print(f"Body text preview: {text[:500]}")
        browser.close()

        patterns = [
            r'估計頭獎基金[^$\d]*\$?([\d,]+)',
            r'Est(?:imated)?\s*Jackpot[^\d$]*\$?([\d,]+)',
            r'jackpot[^\d]*([\d,]{7,})',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
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
        return  # 搵唔到就靜靜地失敗，唔發 warning

    last_notified = load_last_notified()
    print(f"Current: ${amount:,} | Last notified: ${last_notified:,} | Threshold: ${JACKPOT_THRESHOLD:,}")

    if amount >= JACKPOT_THRESHOLD and amount != last_notified:
        send_telegram(f"🎰 六合彩估計頭獎基金達 <b>${amount:,}</b>！\n已超過 $40,000,000 門檻！\nhttps://bet.hkjc.com/marksix/")
        save_last_notified(amount)
        print(f"Notified! Saved new amount: ${amount:,}")
    elif amount < JACKPOT_THRESHOLD:
        # 跌返落門檻以下，reset 狀態（下次超過再通知）
        save_last_notified(0)
        print("Below threshold, state reset.")
    else:
        print(f"Already notified for ${amount:,}, skipping.")

main()
