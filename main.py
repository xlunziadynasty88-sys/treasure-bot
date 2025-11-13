import time
import requests
import os
import json
from threading import Thread
from flask import Flask

app = Flask(__name__)

# ------------------------
# VARIABLES ENV
# ------------------------
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send(msg):
    if not TOKEN or not CHAT_ID:
        print("❌ Variables Telegram manquantes")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ------------------------
# MOTS CLÉS
# ------------------------
KEYWORDS = [
    "tableau","peinture","huile","signée","gravure",
    "bronze","marbre","régule","daum","gallé","lalique",
    "argent","925","miner","or","750",
    "baccarat","sevres","limoges",
    "antiquité","ancien","vintage","collection"
]

BLACKLIST = [
    "copie","faux","imitation","style","façon",
    "réplique","look","genre","type","plaqué","fantaisie"
]

# ------------------------
# SEEN FILE
# ------------------------
if not os.path.exists("seen.json"):
    with open("seen.json", "w") as f:
        json.dump([], f)

with open("seen.json", "r") as f:
    SEEN = json.load(f)

# ------------------------
# SCRAPER LEBONCOIN
# ------------------------
def scrap_lbc():
    url = "https://api.leboncoin.fr/api/adfinder/v1/search"

    payload = {
        "filters": {
            "category": {"id": "3"},
            "location": {"region": ["ile_de_france"]},
        },
        "limit": 20,
    }

    try:
        r = requests.post(url, json=payload, timeout=7)
        r.raise_for_status()
        return r.json().get("ads", [])
    except:
        return []

# ------------------------
# SCORE SIMPLE (sans IA)
# ------------------------
def score_item(title, desc, price):
    title, desc = title.lower(), desc.lower()
    score = 0
    
    for kw in KEYWORDS:
        if kw in title or kw in desc:
            score += 10

    for bad in BLACKLIST:
        if bad in title or bad in desc:
            score -= 50
    
    try:
        p = int(price)
        if p < 50: score += 10
        if p < 20: score += 20
    except:
        pass

    return max(0, min(score, 100))

# ------------------------
# LOOP BOT
# ------------------------
def bot_loop():
    send("🤖 Bot chasseurs de trésors ACTIVÉ !")

    global SEEN

    while True:
        ads = scrap_lbc()
        print("Annonces récupérées :", len(ads))

        for ad in ads:
            ad_id = ad.get("list_id")
            title = ad.get("subject","")
            desc = ad.get("body","")
            price = ad.get("price",0)
            url = ad.get("url","")

            if not ad_id or ad_id in SEEN:
                continue

            s = score_item(title, desc, price)

            if s >= 70:
                send(f"🟢 TRÉSOR DÉTECTÉ !\nTitre : {title}\nPrix : {price}€\nScore : {s}/100\nLien : {url}")

            SEEN.append(ad_id)
            with open("seen.json","w") as f:
                json.dump(SEEN, f)

        time.sleep(20)

# ------------------------
# START THREAD + FLASK
# ------------------------
t = Thread(target=bot_loop)
t.daemon = True
t.start()

@app.route("/")
def home():
    return "Bot Treasure Simple Running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
