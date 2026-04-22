import requests
from bs4 import BeautifulSoup
import re
import os
import logging

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
JACKPOT_THRESHOLD = 40_000_000

logging.basicConfig(level=logging.INFO)

def get_estimated_jackpot():
    # 試多個 URL
    urls = [
        "https://bet.hkjc.com/marksix/index.aspx",
        "https://www.hkjc.com/marksix/index.aspx",
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-HK,zh;q=0.9,en;q=0.8",
    }
    for url in urls:
        try:
            print(f"Trying URL: {url}")
            resp = requests.get(url, headers=headers, timeout=20)
            print(f"Status code: {resp.status_code}")
            print(f"Page length: {len(resp.text)} chars")
            
            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text()
            
            # Debug: print first 500 chars
            print(f"Page text preview: {text[:500]}")
            
            patterns = [
                r'估計頭獎基金[^$\d]*\$?\s*([\d,]+)',
                r'Estimated.*?1st.*?Prize[^$\d]*\$?\s*([\d,]+)',
                r'Est.*?Jackpot[^$\d]*\$?\s*([\d,]+)',
            ]
            for p in patterns:
                match = re.search(p, text, re.IGNORECASE | re.DOTALL)
                if match:
                    amount = int(match.group(1).replace(",", ""))
                    print(f"Found jackpot via pattern: ${amount:,}")
                    return amount
            
            # Fallback: find all large dollar amounts
            amounts = re.findall(r'[\$＄]\s*([\d,]{7,})', text)
            print(f"All large amounts found: {amounts}")
            if amounts:
                parsed = [int(a.replace(",", "")) for a in amounts]
                return max(parsed)
                
        except Exception as e:
            print(f"Error with {url}: {e}")
            continue
    
    return None

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        print(f"Telegram response: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Telegram error: {e}")

def main():
    print("=== Mark Six Jackpot Checker ===")
    amount = get_estimated_jackpot()
    
    if amount is None:
        print("Failed to get jackpot amount, sending warning.")
        send_telegram("⚠️ 未能取得六合彩頭獎基金資料，請手動查閱：https://bet.hkjc.com/marksix/")
        return
    
    print(f"Final jackpot amount: ${amount:,}")
    
    if amount >= JACKPOT_THRESHOLD:
        msg = (f"🎰 <b>頭獎基金警報！</b>\n"
               f"💰 估計頭獎基金：<b>${amount:,}</b>\n"
               f"✅ 已超過 ${JACKPOT_THRESHOLD:,}！\n"
               f"🔗 https://bet.hkjc.com/marksix/")
        send_telegram(msg)
    else:
        print(f"${amount:,} below threshold ${JACKPOT_THRESHOLD:,}. No notification.")

if __name__ == "__main__":
    main()
