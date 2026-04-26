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
