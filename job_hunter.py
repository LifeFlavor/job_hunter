
import requests
from bs4 import BeautifulSoup
import time
import os
from datetime import datetime
import re

# 1. 設定監控目標
TARGET_JOBS = [
    {"company": "OKX", "url": "https://www.okx.com/join-us/openings"},
    {"company": "LINE", "url": "https://careers.linecorp.com/jobs?ca=All&ci=Taipei&co=East%20Asia"},
]

# 只通知「符合的職缺關鍵字」；否則回傳「無新增職缺」
# 用 regex 避免誤判，例如 Taipei 內的 "ai"
KEYWORD_PATTERNS = [
    ("product manager", r"\bproduct manager\b"),
    ("product marketing manager", r"\bproduct marketing manager\b"),
    ("AI相關", r"\bai\b"),
    ("AI相關", r"artificial intelligence"),
    ("AI相關", r"\bmachine learning\b"),
]

# 2. Telegram 設定
TELEGRAM_TOKEN = "8670801991:AAHBDLoMK-GzNqwRX2UPqURszcG78kl4vb8"
TELEGRAM_CHAT_ID = "6025065776D"
HISTORY_FILE = "job_history.txt"

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"發送失敗: {e}")

def get_old_jobs():
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f.readlines())

def save_jobs(job_titles):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        for title in job_titles:
            f.write(f"{title}\n")

def check_jobs():
    old_jobs = get_old_jobs()
    current_all_titles = set()
    new_found = []

    def contains_relevant_keyword(text):
        matched = []
        for label, pattern in KEYWORD_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                matched.append(label)
        # 去重但保留順序
        return list(dict.fromkeys(matched))

    for job in TARGET_JOBS:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在掃描 {job['company']}...")
        try:
            response = requests.get(job['url'], timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 抓取頁面所有文字（簡化版邏輯）
            page_text = soup.get_text()
            
            # 這裡我們用簡單的邏輯：如果該公司名稱+頁面特徵不在舊紀錄裡，就算新職缺
            # 實務上建議抓取具體的 <a> 標籤標題，這裡先以頁面特徵示範
            identifier = f"{job['company']}_{len(page_text)}" 
            current_all_titles.add(identifier)

            if identifier not in old_jobs:
                matched_keywords = contains_relevant_keyword(page_text)
                if matched_keywords:
                    new_found.append(
                        f"🚀 {job['company']} 可能有新增相關職缺！\n連結：{job['url']}\n命中關鍵字：{', '.join(matched_keywords)}"
                    )
        
        except Exception as e:
            print(f"掃描 {job['company']} 失敗: {e}")

    # 有命中就送更新訊息；沒有命中就送「無新增職缺」
    try:
        if new_found:
            for msg in new_found:
                send_telegram_msg(msg)
            has_relevant = True
        else:
            send_telegram_msg("無新增職缺")
            has_relevant = False
    finally:
        save_jobs(current_all_titles)

    return has_relevant

if __name__ == "__main__":
    # 這裡可以不用發「進入監控模式」的訊息，因為每次執行都是獨立的
    print("🕒 開始執行定時掃描...")
    check_jobs()
    print("✅ 掃描完成，程式結束。")
