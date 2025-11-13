import time
import requests
import os
import json
from threading import Thread
from flask import Flask

app = Flask(__name__)

# --- Variables Telegram ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Charger les annonces déjà vues ---
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

def loop_bot():
    print("🤖 Bot chasseurs de trésors lancé.")
    send("🤖 Bot chasseurs de trésors lancé !")

    while True:
        print("🔁 Scan…")
        send("Scan test")
        time.sleep(20)

# Lancer le bot en thread
t = Thread(target=loop_bot)
t.daemon = True
t.start()

# Route web minimale pour Render
@app.route("/")
def home():
    return "Bot Treasure running."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
