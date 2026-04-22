import re
import os
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
JACKPOT_THRESHOLD = 40_000_000

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
        
        content = page.content()
        print(f"Page loaded, length: {len(content)}")
        
        # 搵估計頭獎基金數字
        patterns = [
            r'估計頭獎基金[^$\d]*\$?([\d,]+)',
            r'Est(?:imated)?\s*Jackpot[^\d$]*\$?([\d,]+)',
            r'jackpot[^\d]*([\d,]{7,})',
        ]
        for pat in patterns:
            m = re.search(pat, content, re.IGNORECASE)
            if m:
                amount = int(m.group(1).replace(",", ""))
                if amount >= 5_000_000:
                    print(f"Found jackpot: ${amount:,}")
                    browser.close()
                    return amount
        
        # 嘗試用 page text 再搵
        text = page.inner_text("body")
        print(f"Body text preview: {text[:500]}")
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                amount = int(m.group(1).replace(",", ""))
                if amount >= 5_000_000:
                    print(f"Found jackpot (text): ${amount:,}")
                    browser.close()
                    return amount
        
        browser.close()
        print("Jackpot amount not found.")
        return None

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    print(f"Telegram: {resp.status_code}")

def main():
    print("=== Mark Six Jackpot Checker ===")
    amount = get_estimated_jackpot()
    if amount is None:
        print("Failed to retrieve jackpot amount.")
        send_telegram("⚠️ 未能取得六合彩頭獎基金資料，請手動查閱：https://bet.hkjc.com/marksix/")
        return
    print(f"Jackpot: ${amount:,} | Threshold: ${JACKPOT_THRESHOLD:,}")
    if amount >= JACKPOT_THRESHOLD:
        send_telegram(f"🎰 六合彩估計頭獎基金達 <b>${amount:,}</b>！\n已超過 $40,000,000 門檻！\nhttps://bet.hkjc.com/marksix/")
    else:
        print("Below threshold, no notification sent.")

main()
