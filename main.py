import time
import requests
import os
import json

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not os.path.exists("seen.json"):
    with open("seen.json", "w") as f:
        json.dump([], f)

with open("seen.json", "r") as f:
    seen = json.load(f)

def send(msg):
    if not TOKEN or not CHAT_ID:
        print("❌ Variables Telegram manquantes")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

print("🤖 Bot chasseurs de trésors lancé.")
send("🤖 Bot chasseurs de trésors lancé !")

while True:
    print("🔁 Scan…")
    send("Scan test")
    time.sleep(20)

