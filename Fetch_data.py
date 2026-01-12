import requests
import time
from collections import defaultdict
from datetime import datetime

# --- CONFIGURATION ---
API_KEY = "RGAPI-3fbd8214-526e-4c96-b5b6-077020f75b95"
REGION_ROUTING = "europe" # europe, americas, asia

# Date de début (Format Jour/Mois/Année)
# Ex: "10/01/2024" pour le début de la saison 14 (environ)
START_DATE = "08/01/2026"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Python Script)",
    "X-Riot-Token": API_KEY
}

TEAM_PLAYERS = [
    {"gameName": "Kaneki", "tagLine": "3008"},
    # Ajoute les autres ici
]

# --- 1. LE MOTEUR (Gestion des requêtes) ---
def safe_request(url, params=None):
    """Gère les appels API et les temps d'attente (Rate Limits)"""
    while True:
        response = requests.get(url, headers=HEADERS, params=params)
        
        if response.status_code == 200:
            data = response.json()
            # Petite pause pour être gentil avec les serveurs Riot
            time.sleep(1.2) 
            return data
            
        elif response.status_code == 429:
            # Si Riot dit stop, on attend le temps demandé
            wait_time = int(response.headers.get("Retry-After", 10))
            print(f"   ⚠️ Pause forcée par Riot : {wait_time}s d'attente...")
            time.sleep(wait_time)
            
        elif response.status_code == 404:
            return None # Donnée non trouvée
            
        else:
            print(f"   ❌ Erreur Technique {response.status_code} sur {url}")
            return None

# --- 2. LES OUTILS (Récupération des données) ---
def get_puuid(game_name, tag_line):
    url = f"https://{REGION_ROUTING}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    data = safe_request(url)
    return data.get("puuid") if data else None

def get_matches_since(puuid, date_string):
    """Récupère TOUS les IDs de match depuis une date précise (avec pagination)"""
    
    # Conversion date string -> Timestamp (secondes)
    date_obj = datetime.strptime(date_string, "%d/%m/%Y")
    start_timestamp = int(date_obj.timestamp())
    
    all_match_ids = []
    start_index = 0
    
    print(f"   📅 Recherche des matchs depuis le {date_string}...")
    
    while True:
        url = f"https://{REGION_ROUTING}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params = {
            "startTime": start_timestamp,
            "start": start_index,
            "count": 100 # Maximum autorisé par appel
        }
        
        batch = safe_request(url, params)
        
        if not batch: # Si liste vide, on a fini
            break
            
        all_match_ids.extend(batch)
        print(f"      ↳ Trouvé {len(batch)} matchs (Total: {len(all_match_ids)})...")
        
        if len(batch) < 100: # Si on reçoit moins de 100 matchs, c'est la dernière page
            break
            
        start_index += 100 # On prépare la page suivante
        
    return all_match_ids

def analyze_stats(puuid, match_ids):
    """Analyse détaillée des performances"""
    
    # Stockage : {'Ahri': {'games': 0, 'wins': 0, 'dmg': 0}, ...}
    champ_stats = defaultdict(lambda: {'games': 0, 'wins': 0, 'dmg': 0})
    
    total_wins = 0
    valid_games = 0
    
    print(f"   ⏳ Analyse détaillée des stats (ça peut être long)...")
    
    for i, match_id in enumerate(match_ids):
        # Petit log pour voir l'avancement
        if i % 5 == 0: print(f"      Traitement match {i+1}/{len(match_ids)}...")
            
        url = f"https://{REGION_ROUTING}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        data = safe_request(url)
        
        if not data: continue
        
        info = data["info"]
        duration = info["gameDuration"]
        
        if duration < 300: continue # Ignorer les remakes
        
        # Trouver le joueur
        player = next((p for p in info["participants"] if p["puuid"] == puuid), None)
        
        if player:
            champ = player["championName"]
            damage = player["totalDamageDealtToChampions"]
            dpm = damage / (duration / 60)
            win = player["win"]
            
            valid_games += 1
            if win: total_wins += 1
            
            # Stats par champion
            champ_stats[champ]['games'] += 1
            if win: champ_stats[champ]['wins'] += 1
            champ_stats[champ]['dmg'] += dpm

    if valid_games == 0: return None

    # --- Synthèse ---
    global_wr = (total_wins / valid_games) * 100
    
    final_list = []
    for name, s in champ_stats.items():
        final_list.append({
            "name": name,
            "games": s['games'],
            "winrate": (s['wins'] / s['games']) * 100,
            "dpm": s['dmg'] / s['games']
        })
        
    # Tris
    most_played = sorted(final_list, key=lambda x: x['games'], reverse=True)[0]
    
    # Pour le meilleur WR, on prend ceux avec > 1 game si possible
    pool = [c for c in final_list if c['games'] > 1] or final_list
    best_wr = sorted(pool, key=lambda x: x['winrate'], reverse=True)[0]
    
    best_dpm = sorted(final_list, key=lambda x: x['dpm'], reverse=True)[0]

    return {
        "count": valid_games,
        "wr": global_wr,
        "main": most_played,
        "best_wr": best_wr,
        "best_dpm": best_dpm
    }

# --- 3. L'EXÉCUTION ---
def main():
    print("🚀 DÉMARRAGE DE L'ANALYSEUR ESPORT\n")
    
    for p in TEAM_PLAYERS:
        full_name = f"{p['gameName']}#{p['tagLine']}"
        print(f"👤 ANALYSE DU JOUEUR : {full_name}")
        
        # 1. PUUID
        puuid = get_puuid(p['gameName'], p['tagLine'])
        if not puuid:
            print("   ❌ Joueur introuvable.")
            continue
            
        # 2. MATCHS IDs (Loop temporel)
        match_ids = get_matches_since(puuid, START_DATE)
        
        if not match_ids:
            print("   ❌ Aucun match trouvé sur cette période.")
            continue
            
        # 3. STATS (Le gros morceau)
        stats = analyze_stats(puuid, match_ids)
        
        if stats:
            print(f"\n📊 BILAN DEPUIS LE {START_DATE} ({stats['count']} games) :")
            print(f"   🏆 Winrate Global : {stats['wr']:.1f}%")
            print(f"   🛡️ Main Champ     : {stats['main']['name']} ({stats['main']['games']} games)")
            print(f"   📈 Best Winrate   : {stats['best_wr']['name']} ({stats['best_wr']['winrate']:.0f}%)")
            print(f"   ⚔️ Top DPM        : {stats['best_dpm']['name']} ({int(stats['best_dpm']['dpm'])} DPM)")
        
        print("-" * 50)
        
    print("\n🏁 TERMINE !")

if __name__ == "__main__":
    main()