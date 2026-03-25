
import requests
from bs4 import BeautifulSoup
import time
import os
from datetime import datetime

# 1. 設定監控目標
TARGET_JOBS = [
    {"company": "OKX", "url": "https://www.okx.com/join-us/openings"},
    {"company": "LINE", "url": "https://careers.linecorp.com/jobs?ca=All&ci=Taipei&co=East%20Asia"},
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
                new_found.append(f"🚀 {job['company']} 網頁內容有更新！\n連結：{job['url']}")
        
        except Exception as e:
            print(f"掃描 {job['company']} 失敗: {e}")

    # 如果有新發現，才發通知
    if new_found:
        for msg in new_found:
            send_telegram_msg(msg)
        save_jobs(current_all_titles)
        return True
    return False

if __name__ == "__main__":
    send_telegram_msg("🤖 獵頭機器人已進入「每日 09:00 定時監控」模式")
    
    while True:
        now = datetime.now()
        # 判斷是否為早上 09:00 (或是 09:00 到 09:01 之間)
        if now.hour == 9 and now.minute == 0:
            print("🕒 到達設定時間，開始執行掃描...")
            has_new = check_jobs()
            if not has_new:
                print("查無新職缺，繼續待命。")
            # 執行完後睡 65 秒，避開同一分鐘內重複偵測
            time.sleep(65) 
        
        # 每分鐘檢查一次時間
        time.sleep(30)