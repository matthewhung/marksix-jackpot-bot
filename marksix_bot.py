import requests
import re
import os
import xml.etree.ElementTree as ET

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
JACKPOT_THRESHOLD = 40_000_000

def get_estimated_jackpot():
    # HKJC 靜態 XML data feeds（唔係 SPA）
    endpoints = [
        {
            "url": "https://bet.hkjc.com/marksix/marksix_index.xml",
            "type": "xml"
        },
        {
            "url": "https://www.hkjc.com/home/chi/betting-tips/marksix/index.aspx",
            "type": "html"
        },
        {
            "url": "https://bet.hkjc.com/marksix/result.aspx?lang=ch",
            "type": "html"
        },
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml,*/*",
        "Accept-Language": "zh-HK,zh;q=0.9",
    }
    
    for ep in endpoints:
        try:
            print(f"Trying: {ep['url']}")
            resp = requests.get(ep["url"], headers=headers, timeout=20, allow_redirects=True)
            print(f"Status: {resp.status_code}, Length: {len(resp.text)}")
            
            # 如果係 4830 chars 就係 SPA，跳過
            if len(resp.text) <= 5000 and "You need to enable JavaScript" in resp.text:
                print("SPA detected, skipping.")
                continue
            
            text = resp.text
            print(f"Preview: {text[:400]}")
            
            # 搵估計頭獎基金
            patterns = [
                r'估計頭獎基金[^\d$]*[\$＄]?\s*([\d,]+)',
                r'[Ee]st(?:imated)?\s*[Jj]ackpot[^\d$]*[\$＄]?\s*([\d,]+)',
                r'jackpot[^\d]*?([\d,]{7,})',
                r'EstJackpot[^\d]*([\d,]+)',
                r'([\d,]{8,})',  # 任何 8+ 位數字
            ]
            for p in patterns:
                m = re.search(p, text, re.IGNORECASE)
                if m:
                    amount = int(m.group(1).replace(",", ""))
                    if amount >= 5_000_000:
                        print(f"Found jackpot: ${amount:,}")
                        return amount
                        
            print("No jackpot amount found in this response.")
            
        except Exception as e:
            print(f"Error: {e}")
    
    return None

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    print(f"Telegram: {resp.status_code} - {resp.text[:200]}")

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
