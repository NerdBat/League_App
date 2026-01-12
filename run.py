import subprocess
import sys
import os

def main():
    print("🚀 INITIALISATION DU DASHBOARD ESPORT...")

    # 1. Lancer le script de récupération de données
    print("\n[1/2] 📥 Récupération des dernières données Riot...")
    # On utilise sys.executable pour être sûr d'utiliser le même python que l'environnement actuel
    try:
        # check=True arrête tout si Fetch_data plante
        subprocess.run([sys.executable, "dev/Fetch_data.py"], check=True)
    except subprocess.CalledProcessError:
        print("❌ Erreur lors de la récupération des données. Arrêt.")
        return

    print("\n[2/3] 🌍 Récupération du Ladder EUW/KR...")
    subprocess.run([sys.executable, "dev/Fetch_leaderboard.py"], check=False) # check=False pour ne pas bloquer si erreur réseau
    
    print("\n[3/3] 📊 Lancement Web...")
    # ...
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Fermeture du dashboard.")

if __name__ == "__main__":
    main()