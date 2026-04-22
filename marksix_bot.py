import requests
import re
import os

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
JACKPOT_THRESHOLD = 40_000_000

def get_estimated_jackpot():
    # HKJC 前端真正用嘅 API
    api_urls = [
        "https://bet.hkjc.com/marksix/api/DrawResult/GetNextDraw",
        "https://bet.hkjc.com/api/v1/lotto/nextDraw?gameCode=MARK6",
        "https://info.cld.hkjc.com/graphql/query/",
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://bet.hkjc.com/marksix/",
        "Origin": "https://bet.hkjc.com",
    }
    
    # Method 1: 試 JSON API
    for url in api_urls:
        try:
            print(f"Trying: {url}")
            resp = requests.get(url, headers=headers, timeout=15)
            print(f"Status: {resp.status_code}, Length: {len(resp.text)}")
            print(f"Response preview: {resp.text[:300]}")
            if resp.status_code == 200 and len(resp.text) > 100:
                try:
                    data = resp.json()
                    print(f"JSON keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    text = str(data)
                    amounts = re.findall(r'\b([4-9]\d{7,}|[1-9]\d{8,})\b', text)
                    if amounts:
                        amount = max(int(a) for a in amounts)
                        print(f"Found: ${amount:,}")
                        return amount
                except Exception as e:
                    print(f"JSON parse error: {e}")
        except Exception as e:
            print(f"Error: {e}")
    
    return None

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    print(f"Telegram: {resp.status_code} - {resp.text}")

def main():
    print("=== Mark Six Jackpot Checker ===")
    amount = get_estimated_jackpot()
    if amount is None:
        print("Failed to retrieve jackpot amount.")
        send_telegram("⚠️ 未能取得六合彩頭獎基金資料，請手動查閱：https://bet.hkjc.com/marksix/")
        return
    print(f"Jackpot: ${amount:,}, Threshold: ${JACKPOT_THRESHOLD:,}")
    if amount >= JACKPOT_THRESHOLD:
        send_telegram(f"🎰 六合彩估計頭獎基金達 <b>${amount:,}</b>！\n已超過 $40,000,000 門檻！\nhttps://bet.hkjc.com/marksix/")
    else:
        print(f"Below threshold, no notification.")

main()
