import time
import requests
import os
import json
from threading import Thread
from flask import Flask
import openai

app = Flask(__name__)

# ------------------------
# VARIABLES ENV
# ------------------------
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

def send(msg):
    if not TOKEN or not CHAT_ID:
        print("❌ Variables Telegram manquantes")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

# ------------------------
# Mots clés POSITIFS & BLACKLIST
# ------------------------
KEYWORDS = [
    "tableau", "peinture", "signée", "huile", "gravure", "art nouveau", "impressionnisme",
    "argent massif", "925", "poinçon", "or 18k", "750", "louis d’or", "napoléon",
    "bronze", "marbre", "régule", "terre cuite", "lalique", "gallé", "daum",
    "faïence", "porcelaine", "sevres", "limoges", "cristal", "baccarat",
    "bijoux anciens", "montre ancienne", "vintage", "gousset",
    "antiquité", "curiosité", "objet ancien", "grenier",
    "casque", "sabre", "médaille", "militaria"
]

BLACKLIST = [
    "copie", "imitation", "reproduction", "faux", "style", "façon", "réplique",
    "plaqué", "doré", "fantaisie", "look gallé", "type", "genre"
]

# ------------------------
# Charger annonces déjà vues
# ------------------------
if not os.path.exists("seen.json"):
    with open("seen.json", "w") as f:
        json.dump([], f)

with open("seen.json", "r") as f:
    SEEN = json.load(f)

# ------------------------
# SCRAPER LBC (version simple)
# ------------------------
def scrap_lbc():
    url = "https://api.leboncoin.fr/api/adfinder/v1/search"

    payload = {
        "filters": {
            "category": {"id": "3"},  # généraliste, tu peux changer
            "location": {"region": ["ile_de_france"]}  # région (modifiable)
        },
        "limit": 20,
    }

    try:
        r = requests.post(url, json=payload, timeout=8)
        r.raise_for_status()
        data = r.json()
        return data.get("ads", [])
    except Exception as e:
        print("Erreur scrap LBC:", e)
        return []

# ------------------------
# SCORE BASE (sans IA)
# ------------------------
def basic_score(title, description, price):
    title_low = title.lower()
    desc_low = description.lower()
    score = 0

    for kw in KEYWORDS:
        if kw in title_low or kw in desc_low:
            score += 8

    for bad in BLACKLIST:
        if bad in title_low or bad in desc_low:
            score -= 60

    try:
        p = int(price)
        if p < 50:
            score += 10
        if p < 20:
            score += 20
    except:
        pass

    return max(-50, min(score, 100))

# ------------------------
# IA OPENAI : AVIS EXPERT
# ------------------------
def ai_evaluate_deal(title, description, price, url):
    if not OPENAI_API_KEY:
        return "⚠️ IA désactivée (clé OpenAI manquante)", 0

    prompt = f"""
Tu es un expert en art, antiquités, objets de collection et estimation de valeur.

Analyse l'annonce suivante :

Titre : {title}
Description : {description}
Prix : {price} €

Ta mission :
1. Dire si c'est une bonne affaire, normale, douteuse ou une arnaque probable.
2. Repérer les éléments suspects : copie, contrefaçon, incohérences, prix trop bas, vocabulaire louche.
3. Donner une estimation réaliste de la valeur (même approximative).
4. Donner un score entre 0 et 100 de crédibilité.

Réponds strictement :
Verdict : ...
Score : X/100
Analyse :
- ...
- ...
Valeur estimée : ...
"""

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un expert en objets anciens, prudent, et tu n'affirmes jamais une authenticité à 100%."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        text = resp["choices"][0]["message"]["content"]

        import re
        ai_score = 0
        m = re.search(r"(\d+)\s*/\s*100", text)
        if m:
            ai_score = int(m.group(1))

        return text, ai_score
    except Exception as e:
        print("Erreur IA :", e)
        return "⚠️ Erreur IA (OpenAI)", 0

# ------------------------
# BOUCLE PRINCIPALE DU BOT
# ------------------------
def bot_loop():
    send("🤖 *Bot PRO + IA Chasseur de Trésors ACTIVÉ !*")

    global SEEN

    while True:
        ads = scrap_lbc()
        print(f"Nombre d'annonces récupérées : {len(ads)}")

        for ad in ads:
            ad_id = ad.get("list_id")
            title = ad.get("subject", "")
            price = ad.get("price", 0)
            desc = ad.get("body", "")
            url = ad.get("url", "Lien indisponible")

            if not ad_id:
                continue

            if ad_id in SEEN:
                continue

            base_score = basic_score(title, desc, price)
            ai_text, ai_score = ai_evaluate_deal(title, desc, price, url)

            global_score = max(0, min(100, int((base_score + ai_score) / 2)))

            if global_score >= 70:
                msg = f"""
🟢 *TRÉSOR POTENTIEL (IA)*

Titre : *{title}*
Prix : *{price} €*
Score global : *{global_score}/100*

Analyse IA :
{ai_text}

🔗 {url}
"""
                send(msg)

            SEEN.append(ad_id)
            with open("seen.json", "w") as f:
                json.dump(SEEN, f)

        time.sleep(30)

# ------------------------
# THREAD RENDER + FLASK
# ------------------------
t = Thread(target=bot_loop)
t.daemon = True
t.start()

@app.route("/")
def home():
    return "Bot Treasure PRO + IA Running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
