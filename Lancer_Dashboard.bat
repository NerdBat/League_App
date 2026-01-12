@echo off
echo 🚀 Lancement de l'Analyseur Esport...

:: 1. Fetch Data
echo 📥 Mise a jour des stats Riot...
python dev/Fetch_data.py

echo 🌍 Mise a jour du Leaderboard...
python dev/Fetch_leaderboard.py

echo 📊 Ouverture du Dashboard...

:: Vérifie s'il y a eu une erreur
if %errorlevel% neq 0 (
    echo ❌ Erreur lors du fetch data.
    pause
    exit /b
)

:: 2. Streamlit
streamlit run app.py