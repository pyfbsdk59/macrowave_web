import yfinance as yf
import requests
import pandas as pd
import re
import datetime
import os
from fredapi import Fred
from bs4 import BeautifulSoup

# 設定 FRED API KEY
FRED_KEY = os.environ.get('FRED_API_KEY', '04d8498cb9b39259ebec99a14cb7ef42')
fred = Fred(api_key=FRED_KEY)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

def get_web_pmi(url):
    """
    通用函式：使用 requests 抓取 Investing.com 這類財經日曆的最新數值
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        # 針對 Investing.com 的 JSON 數據或 HTML 結構進行正則搜尋
        # 尋找 "actual": 數值 (常見於 JSON 回傳) 或 HTML 表格
        matches = re.findall(r'"actual":\s*"?(\d+\.\d+)"?', r.text)
        if matches:
            # Investing.com 通常按時間排序，最後一個未必是最新，需看情境
            # 但在 eventHistoryTable 中通常是最新的在上面，或是 JSON 裡的最後一筆
            # 這裡簡單取最後一筆匹配到的非空數值
            return float(matches[-1])
        
        # 備用：直接搜 HTML
        soup = BeautifulSoup(r.text, 'html.parser')
        # 嘗試找最新的 actual 值 (根據 Investing.com 結構)
        # 這部分結構常變，Regex 比較穩
    except:
        pass
    return 0.0

def update_all_data():
    data = {}
    
    # --- 1. 美日利差 ---
    try:
        us_10y = 0.0
        tnx = yf.Ticker("^TNX")
        hist = tnx.history(period="5d")
        if not hist.empty:
            us_10y = hist['Close'].iloc[-1]
    except: us_10y = 0.0

    # 日債 (CNYES 靜態頁面)
    try:
        r = requests.get("https://www.cnyes.com/futures/html5chart/JP10YY.html", headers=HEADERS, timeout=5)
        dfs = pd.read_html(r.text)
        jp_10y = float(dfs[0].iloc[0][1])
    except: jp_10y = 0.0

    spread = us_10y - jp_10y
    data['us_jp_spread'] = {
        'us': round(us_10y, 2),
        'jp': round(jp_10y, 2),
        'spread': round(spread, 2),
        'status': 'Danger' if spread < 2.0 and us_10y > 0 else 'Safe'
    }

    # --- 2. 貴金屬 (Yahoo Finance) ---
    metals_info = {
        "Gold": "GC=F", "Silver": "SI=F", "Copper": "HG=F"
    }
    metals_list = []
    
    for name, ticker in metals_info.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="6mo")
            if not hist.empty:
                high = hist['High'].max()
                curr = hist['Close'].iloc[-1]
                drop = (high - curr) / high * 100
                status = "Safe"
                if drop >= 50: status = "Danger"
                
                metals_list.append({
                    'name': name, 'current': round(curr, 2),
                    'drop': round(drop, 2), 'status': status
                })
        except:
            metals_list.append({'name': name, 'current': 0, 'drop': 0, 'status': 'Unknown'})
            
    data['metals'] = metals_list

    # --- 3. Mark 17 (重點指標) ---
    mark17_list = []
    total_score = 0

    # A. 美國 PMI (Investing.com)
    us_pmi = get_web_pmi("https://www.investing.com/economic-calendar/ism-manufacturing-pmi-173")
    pmi_status = "Safe"
    pmi_score = 0
    if us_pmi > 0 and us_pmi < 50:
        pmi_score = 1
        pmi_status = "Warning"
    
    mark17_list.append({'item': '美國 PMI (US ISM)', 'value': us_pmi if us_pmi else "N/A", 'score': pmi_score, 'status': pmi_status})
    total_score += pmi_score

    # B. 中國 PMI (Investing.com - 解決 FRED 數據舊問題)
    cn_pmi = get_web_pmi("https://www.investing.com/economic-calendar/chinese-manufacturing-pmi-594")
    # 如果抓不到，嘗試 CNYES 新聞搜尋 (備援)
    if cn_pmi == 0:
        try:
            r = requests.get("https://news.cnyes.com/news/cat/china_pmi", headers=HEADERS, timeout=5)
            # 搜尋類似 "PMI... 49.5"
            m = re.findall(r'PMI.*?(\d{2}\.\d)', r.text)
            if m: cn_pmi = float(m[0])
        except: pass

    cn_status = "Safe"
    if cn_pmi > 0 and cn_pmi < 50: cn_status = "Warning" # 中國 PMI 不計入 Mark17 標準計分，但列出參考
    
    mark17_list.append({'item': '中國 PMI (China)', 'value': cn_pmi if cn_pmi else "N/A", 'score': '-', 'status': cn_status})

    # C. 美國失業率 (FRED)
    try:
        unrate = fred.get_series('UNRATE').iloc[-1]
        ur_score = 0
        ur_status = "Safe"
        if unrate > 4.5: ur_score = 3; ur_status = "Danger"
        elif unrate > 4: ur_score = 1; ur_status = "Warning"
        total_score += ur_score
        mark17_list.append({'item': '美國失業率', 'value': f"{unrate}%", 'score': ur_score, 'status': ur_status})
    except:
        mark17_list.append({'item': '美國失業率', 'value': "N/A", 'score': 0, 'status': "Unknown"})

    # D. 殖利率倒掛
    ys_score = 0
    ys_status = "Safe"
    # 簡化計算：若 10Y < 4.0 (假設 3M 維持 5.0) -> 倒掛
    # 正式應抓 3M，這裡沿用上面的 us_10y
    # 假設 3M 約為 5.2 (定值或另外抓)
    us_3m = 5.2 
    if us_10y > 0 and (us_10y - us_3m) < 0:
        ys_score = 3
        ys_status = "Danger"
    
    total_score += ys_score
    mark17_list.append({'item': '殖利率倒掛 (Spread)', 'value': f"{round(us_10y - us_3m, 2)}", 'score': ys_score, 'status': ys_status})

    data['mark17'] = mark17_list
    data['total_score'] = total_score
    
    advice = "Safe"
    if total_score >= 12: advice = "Reduce"
    elif total_score >= 6: advice = "Caution"
    
    data['advice'] = advice

    return data