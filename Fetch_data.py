import requests
import time
import json
import os
from datetime import datetime

# --- CONFIGURATION ---
API_KEY = "RGAPI-3fbd8214-526e-4c96-b5b6-077020f75b95" # ⚠️ Remplace par ta vraie clé
REGION_ROUTING = "europe" 
START_DATE = "08/01/2026"
DATA_FILE_PATH = "esport_data.json" # Fichier de sortie

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Python Script)",
    "X-Riot-Token": API_KEY
}

TEAM_PLAYERS = [
    {"gameName": "Kaneki", "tagLine": "3008"},
    # Ajoute les autres ici
]

# --- 1. LE MOTEUR API ---
def safe_request(url, params=None):
    while True:
        try:
            response = requests.get(url, headers=HEADERS, params=params)
            if response.status_code == 200:
                time.sleep(1.2) # Rate limit friendly
                return response.json()
            elif response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 10))
                print(f"   ⚠️ Pause Riot : {wait}s...")
                time.sleep(wait)
            elif response.status_code == 404:
                return None
            else:
                print(f"   ❌ Erreur {response.status_code} sur {url}")
                return None
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return None

def get_puuid(game_name, tag_line):
    url = f"https://{REGION_ROUTING}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    data = safe_request(url)
    return data.get("puuid") if data else None

def get_matches_since(puuid, date_string):
    date_obj = datetime.strptime(date_string, "%d/%m/%Y")
    start_timestamp = int(date_obj.timestamp())
    
    all_match_ids = []
    start_index = 0
    print(f"   📅 Recherche matchs depuis {date_string}...")
    
    while True:
        url = f"https://{REGION_ROUTING}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params = {"startTime": start_timestamp, "start": start_index, "count": 100}
        batch = safe_request(url, params)
        if not batch: break
        
        all_match_ids.extend(batch)
        print(f"      ↳ {len(all_match_ids)} matchs trouvés...")
        if len(batch) < 100: break
        start_index += 100
        
    return all_match_ids

# --- 2. EXTRACTION DE DONNÉES (RAW DATA) ---
def extract_match_data(puuid, match_ids):
    """Récupère les données BRUTES de chaque match pour le JSON"""
    matches_data = []
    
    print(f"   ⏳ Extraction détaillée ({len(match_ids)} matchs)...")
    
    for i, match_id in enumerate(match_ids):
        if i % 5 == 0: print(f"      Extraction {i+1}/{len(match_ids)}...")
            
        url = f"https://{REGION_ROUTING}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        data = safe_request(url)
        if not data: continue
        
        info = data["info"]
        if info["gameDuration"] < 300: continue # Skip remakes
        
        player = next((p for p in info["participants"] if p["puuid"] == puuid), None)
        if not player: continue

        # Calculs préliminaires
        duration_min = info["gameDuration"] / 60
        dpm = player["totalDamageDealtToChampions"] / duration_min
        gpm = player["goldEarned"] / duration_min

        # On structure l'objet match pour le JSON
        match_entry = {
            "match_id": match_id,
            "game_date": info["gameEndTimestamp"], # En ms
            "duration_sec": info["gameDuration"],
            "win": player["win"],
            
            # Identité
            "champion": player["championName"],
            "role": player["teamPosition"], # TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY
            
            # Combat
            "kills": player["kills"],
            "deaths": player["deaths"],
            "assists": player["assists"],
            "kda": player["challenges"].get("kda", 0), # Riot calcule le KDA parfois
            
            # Performance
            "damage_total": player["totalDamageDealtToChampions"],
            "dpm": round(dpm, 1),
            "gold_total": player["goldEarned"],
            "gpm": round(gpm, 1),
            "cs_total": player["totalMinionsKilled"] + player["neutralMinionsKilled"],
            "cs_min": round((player["totalMinionsKilled"] + player["neutralMinionsKilled"]) / duration_min, 1),
            
            # Vision
            "vision_score": player["visionScore"],
            "wards_placed": player["wardsPlaced"],
            "wards_killed": player["wardsKilled"]
        }
        matches_data.append(match_entry)

    return matches_data

# --- 3. FONCTION D'AFFICHAGE CONSOLE (Juste pour le style) ---
def print_summary_from_data(matches):
    if not matches: return
    
    total_games = len(matches)
    wins = sum(1 for m in matches if m['win'])
    wr = (wins / total_games) * 100
    
    # Trouver Main Champ
    champ_counts = {}
    for m in matches:
        champ_counts[m['champion']] = champ_counts.get(m['champion'], 0) + 1
    main_champ = max(champ_counts, key=champ_counts.get)
    
    # Trouver Best DPM
    best_dpm_game = max(matches, key=lambda x: x['dpm'])
    
    print(f"\n📊 BILAN ({total_games} games) :")
    print(f"   🏆 Winrate Global : {wr:.1f}%")
    print(f"   🛡️ Main Champ     : {main_champ} ({champ_counts[main_champ]} games)")
    print(f"   ⚔️ Top DPM        : {best_dpm_game['champion']} ({best_dpm_game['dpm']} DPM)")

# --- 4. EXÉCUTION & SAUVEGARDE ---
def main():
    print("🚀 DÉMARRAGE DE L'ANALYSEUR ESPORT (Mode JSON)\n")
    
    # Structure finale du JSON
    full_database = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "players": {}
    }
    
    for p in TEAM_PLAYERS:
        full_name = f"{p['gameName']}#{p['tagLine']}"
        print(f"👤 JOUEUR : {full_name}")
        
        puuid = get_puuid(p['gameName'], p['tagLine'])
        if not puuid: continue
            
        match_ids = get_matches_since(puuid, START_DATE)
        if not match_ids: continue
            
        # Récupération des données brutes
        player_matches = extract_match_data(puuid, match_ids)
        
        # Ajout au dictionnaire global
        full_database["players"][full_name] = player_matches
        
        # Affichage console pour vérifier que tout va bien
        print_summary_from_data(player_matches)
        print("-" * 50)
        
    # Sauvegarde dans le fichier JSON
    print(f"\n💾 Sauvegarde des données dans '{DATA_FILE_PATH}'...")
    try:
        with open(DATA_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(full_database, f, indent=4)
        print("✅ Sauvegarde réussie !")
    except Exception as e:
        print(f"❌ Erreur sauvegarde : {e}")

if __name__ == "__main__":
    main()