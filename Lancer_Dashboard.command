#!/bin/bash

# Cette ligne permet de se placer dans le dossier du fichier (important !)
cd "$(dirname "$0")"

echo "🚀 Lancement de l'Analyseur Esport..."

# 1. Fetch Data
python3 dev/Fetch_data.py

# 2. Streamlit
streamlit run app.py