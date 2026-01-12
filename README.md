# 🏆 LoL Esports Analytics Dashboard

Un outil d'analyse de performance pour équipes League of Legends.
Ce projet récupère les données de match via l'API Riot Games et génère un tableau de bord interactif pour visualiser les performances des joueurs (Winrate, DPM, Gold, Vision, etc.).

## 📋 Prérequis

Avant de commencer, assure-toi d'avoir :
1.  **Python** installé sur ta machine (version 3.8 ou supérieure).
2.  Une **Clé API Riot** valide.

### 🔑 Récupérer sa Clé API Riot
1.  Rends-toi sur le [Portail Développeur Riot Games](https://developer.riotgames.com/).
2.  Connecte-toi avec ton compte Riot.
3.  Copie la clé sous la section **"Development API Key"**.
    * *⚠️ Attention : Cette clé expire toutes les 24h. Il faudra la régénérer si tu relances le script le lendemain.*

---

## ⚙️ Installation

### 1. Cloner ou télécharger le projet
Place-toi dans le dossier du projet via ton terminal.

### 2. Créer un environnement virtuel (Recommandé)
Cela évite de mélanger les librairies avec celles de ton système.

* **Sur Windows :**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

* **Sur Mac / Linux :**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

### 3. Installer les librairies
Lance cette commande pour installer tout le nécessaire (Streamlit, Pandas, Plotly, etc.) :

```bash
pip install requests pandas streamlit plotly matplotlib


## 🖱️ Lancement Facile (Mode "Double-clic")

Une fois l'installation terminée, pas besoin d'ouvrir le terminal à chaque fois !

### 👉 Pour Windows 🪟
Double-cliquez simplement sur le fichier :
📂 **`Lancer_Windows.bat`**

### 👉 Pour Mac 🍎
Double-cliquez sur le fichier :
📂 **`Lancer_Mac.command`**

> **Note pour Mac :** Si le fichier ne se lance pas la première fois (permission refusée), faites ceci une seule fois :
> 1. Ouvrez le terminal.
> 2. Tapez `chmod +x ` (avec un espace après le x).
> 3. Glissez le fichier `Lancer_Mac.command` dans la fenêtre du terminal.
> 4. Appuyez sur Entrée. C'est bon pour toujours !

---
