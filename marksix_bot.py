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
    url = "https://bet.hkjc.com/marksix/index.aspx"
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text()
        
        # 搵估計頭獎金額
        patterns = [r'估計頭獎基金[^$]*\$\s*([\d,]+)', r'Estimated.*?Prize.*?\$\s*([\d,]+)']
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE | re.DOTALL)
            if match:
                amount = int(match.group(1).replace(",", ""))
                return amount
        
        # Fallback
        amounts = re.findall(r'\$([\d,]{8,})', text)
        if amounts:
            return max(int(a.replace(",", "")) for a in amounts)
        return None
    except:
        return None

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)

def main():
    amount = get_estimated_jackpot()
    if amount is None:
        send_telegram("⚠️ 未能取得六合彩頭獎基金資料")
        return
    
    amount_str = f"${amount:,}"
    print(f"Current jackpot: {amount_str}")
    
    if amount >= JACKPOT_THRESHOLD:
        msg = f"🎰 <b>頭獎基金警報！</b>\n💰 {amount_str}\n✅ 超過 ${JACKPOT_THRESHOLD:,}！"
        send_telegram(msg)
    else:
        print("Below threshold, no notification")

if __name__ == "__main__":
    main()
