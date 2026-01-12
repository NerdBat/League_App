import requests
import json
import time
from datetime import datetime

import os
from dotenv import load_dotenv
load_dotenv() # Charge le fichier .env
API_KEY = os.getenv("RIOT_API_KEY")
OUTPUT_FILE = "leaderboard_data.json"
REGIONS = {"EUW": "euw1", "KR": "kr"}

HEADERS = {"X-Riot-Token": API_KEY}
session = requests.Session()
session.headers.update(HEADERS)

def safe_request(url):
    while True:
        try:
            resp = session.get(url)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 5))
                print(f"      ⚠️ Pause Rate Limit ({wait}s)...")
                time.sleep(wait)
            else:
                print(f"      ❌ Erreur HTTP {resp.status_code} sur {url}")
                return None
        except Exception as e:
            print(f"      ❌ Exception: {e}")
            return None

def get_riot_id(region, player_data):
    """
    Récupère le Riot ID (Nom#Tag) de la manière la plus efficace possible.
    S'adapte selon si on a le PUUID ou le SummonerID.
    """
    puuid = player_data.get("puuid")
    summoner_id = player_data.get("summonerId")
    
    # CAS 1 : On a déjà le PUUID (Le top du top, merci Riot)
    if puuid:
        routing = "europe" if region == "euw1" else "asia"
        url_acc = f"https://{routing}.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}"
        data_acc = safe_request(url_acc)
        if data_acc:
            return f"{data_acc['gameName']}#{data_acc['tagLine']}"
            
    # CAS 2 : On a seulement le SummonerID (La méthode classique)
    elif summoner_id:
        # Étape A : SummonerID -> PUUID
        url_sum = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}"
        data_sum = safe_request(url_sum)
        
        if data_sum and "puuid" in data_sum:
            puuid = data_sum["puuid"]
            # Étape B : PUUID -> Riot ID
            routing = "europe" if region == "euw1" else "asia"
            url_acc = f"https://{routing}.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}"
            data_acc = safe_request(url_acc)
            if data_acc:
                return f"{data_acc['gameName']}#{data_acc['tagLine']}"
    
    # Si tout échoue
    return "Unknown Player"

def main():
    print("🚀 DÉMARRAGE DU SCANNER LADDER PRO V2\n")
    
    global_data = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "regions": {}
    }

    for name, code in REGIONS.items():
        print(f"🌍 Analyse {name} ({code})...")
        
        url = f"https://{code}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5"
        data = safe_request(url)
        
        if not data: 
            print("   ❌ Impossible de récupérer la ligue.")
            continue
        
        entries = data["entries"]
        entries.sort(key=lambda x: x['leaguePoints'], reverse=True)
        top_players = entries[:100] 
        
        processed = []
        print(f"   ⚙️ Traitement du Top {len(top_players)}...")
        
        # DEBUG : Affiche les clés du premier joueur pour comprendre l'erreur
        if len(top_players) > 0:
            print(f"   🔍 DEBUG (Clés disponibles) : {list(top_players[0].keys())}")

        for i, p in enumerate(top_players):
            # On passe tout l'objet 'p' à la fonction pour qu'elle se débrouille
            real_name = get_riot_id(code, p)
            
            wins = p.get("wins", 0)
            losses = p.get("losses", 0)
            total = wins + losses
            wr = (wins/total*100) if total > 0 else 0
            
            print(f"      [{i+1}] {real_name} ({p['leaguePoints']} LP)")
            
            processed.append({
                "rank": i+1,
                "name": real_name,
                "lp": p["leaguePoints"],
                "winrate": round(wr, 1),
                "wins": wins,
                "losses": losses,
                "tier": "CHALLENGER"
            })
            
            time.sleep(0.05) # Petite pause sécurité

        global_data["regions"][name] = processed

    print(f"\n💾 Sauvegarde dans '{OUTPUT_FILE}'...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(global_data, f, indent=4)
    print("✅ Terminé !")

if __name__ == "__main__":
    main()