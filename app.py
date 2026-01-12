import streamlit as st
import pandas as pd
import json
import plotly.express as px
import requests  # NOUVEAU : Indispensable pour l'API
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv() # Charge le fichier .env
API_KEY = os.getenv("RIOT_API_KEY")
# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="LoL Esport Dashboard",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FONCTIONS UTILITAIRES ---
@st.cache_data
def load_data():
    try:
        with open("esport_data.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return None

# --- CHARGEMENT DES DONNÉES ---
raw_data = load_data()

# --- SIDEBAR (PARAMÈTRES & LIVE CHECK) ---
st.sidebar.title("🎛️ Dashboard LoL")
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/LoL_Icon_Render.png/640px-LoL_Icon_Render.png", width=100)

# 1. Sélection du joueur (On en a besoin pour tout le monde)
selected_player = None
if raw_data:
    st.sidebar.caption(f"📅 Data du : {raw_data.get('last_update', '?')}")
    players_list = list(raw_data["players"].keys())
    selected_player = st.sidebar.selectbox("Joueur", players_list)
else:
    st.sidebar.error("❌ Lance 'dev/Fetch_data.py' d'abord !")

# 2. Navigation
page = st.sidebar.radio("Navigation", ["🔍 Analyse Joueur", "🌍 Top Ladder (EUW/KR)"])

st.sidebar.markdown("---")

# 3. Bouton "Live Game" (Bonus)
if st.sidebar.button("🔴 Vérifier si en jeu ?"):
    if selected_player:
        load_dotenv() # Charge le fichier .env
        API_KEY = os.getenv("RIOT_API_KEY")
        HEADERS = {"X-Riot-Token": API_KEY}
        
        # On sépare le Pseudo du Tag (ex: "Kaneki#3008" -> "Kaneki", "3008")
        try:
            game_name, tag_line = selected_player.split("#")
            
            # A. On récupère le PUUID (appel rapide Account V1)
            url_account = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
            res_acc = requests.get(url_account, headers=HEADERS)
            
            if res_acc.status_code == 200:
                puuid = res_acc.json().get("puuid")
                
                # B. On regarde le Spectator V5
                url_spec = f"https://euw1.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{puuid}"
                res_spec = requests.get(url_spec, headers=HEADERS)
                
                if res_spec.status_code == 200:
                    game_info = res_spec.json()
                    mode = game_info['gameMode']
                    st.sidebar.success(f"⚔️ EN JEU ! ({mode})")
                elif res_spec.status_code == 404:
                    st.sidebar.info("💤 Le joueur ne joue pas.")
                else:
                    st.sidebar.warning(f"Erreur Spectator: {res_spec.status_code}")
            else:
                st.sidebar.error("❌ Joueur introuvable (Vérifie la clé API)")
        except Exception as e:
            st.sidebar.error(f"Erreur : {e}")
    else:
        st.sidebar.warning("Aucun joueur sélectionné.")

# =========================================================
# PAGE 1 : ANALYSE JOUEUR
# =========================================================
if page == "🔍 Analyse Joueur":
    if not raw_data or not selected_player:
        st.warning("Aucune donnée chargée.")
        st.stop()

    # Récupération des matchs du joueur sélectionné
    matches = raw_data["players"][selected_player]
    df = pd.DataFrame(matches)
    
    # Conversion date
    if not df.empty:
        df['date'] = pd.to_datetime(df['game_date'], unit='ms')

        st.title(f"📊 Analyse : {selected_player}")

        # --- 1. KPIs ---
        col1, col2, col3, col4 = st.columns(4)
        total_games = len(df)
        wins = df['win'].sum()
        winrate = (wins / total_games) * 100
        avg_kda = df['kda'].mean()
        avg_dpm = df['dpm'].mean()
        avg_cs = df['cs_min'].mean()

        col1.metric("Winrate", f"{winrate:.1f}%", f"{wins}V - {total_games-wins}D")
        col2.metric("KDA Moyen", f"{avg_kda:.2f}")
        col3.metric("Dégâts/min (DPM)", f"{int(avg_dpm)}")
        col4.metric("CS/min", f"{avg_cs:.1f}")

        st.markdown("---")

        # --- 2. ONGLETS ---
        tab1, tab2, tab3 = st.tabs(["⚔️ Champions", "📈 Performance", "📝 Historique"])

        with tab1:
            col_graph1, col_graph2 = st.columns([2, 1])
            with col_graph1:
                st.subheader("Pool de Champions")
                champ_stats = df.groupby("champion").agg(
                    Games=('match_id', 'count'),
                    Wins=('win', 'sum'),
                    Avg_DPM=('dpm', 'mean')
                ).reset_index()
                champ_stats['Winrate'] = (champ_stats['Wins'] / champ_stats['Games']) * 100
                champ_stats = champ_stats.sort_values(by="Games", ascending=False)
                
                fig = px.bar(
                    champ_stats, x="champion", y="Games", color="Winrate",
                    color_continuous_scale=["red", "yellow", "green"],
                    range_color=[0, 100], text="Winrate",
                    title="Matchs joués & Winrate"
                )
                fig.update_traces(texttemplate='%{text:.0f}%', textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
                
            with col_graph2:
                st.subheader("Top Stats")
                best_wr = champ_stats[champ_stats['Games'] >= 2].sort_values(by="Winrate", ascending=False).head(3)
                if not best_wr.empty:
                    st.write("**💪 Meilleurs Winrates (>1 game):**")
                    for _, row in best_wr.iterrows():
                        st.success(f"{row['champion']} : {row['Winrate']:.0f}% ({row['Games']} games)")
                
                if not champ_stats.empty:
                    most_played = champ_stats.iloc[0]
                    st.write(f"**🛡️ Main:** {most_played['champion']}")

        with tab2:
            st.subheader("Évolution des Dégâts (DPM)")
            fig2 = px.line(
                df.sort_values(by="game_date"), x="date", y="dpm", markers=True, 
                color="win", color_discrete_map={True: "green", False: "red"},
                hover_data=["champion", "kda"],
                title="DPM par partie"
            )
            st.plotly_chart(fig2, use_container_width=True)
            
            st.subheader("Corrélation Or vs Dégâts")
            fig3 = px.scatter(
                df, x="gpm", y="dpm", color="champion", size="kda", 
                hover_name="champion", title="Gold/min vs Dégâts/min"
            )
            st.plotly_chart(fig3, use_container_width=True)

        with tab3:
            st.subheader("Détail des Matchs")
            display_df = df[[
                "date", "champion", "win", "kda", "kills", "deaths", "assists", 
                "dpm", "cs_min", "vision_score"
            ]].copy()
            
            display_df["win"] = display_df["win"].apply(lambda x: "✅ VICTOIRE" if x else "❌ DÉFAITE")
            display_df["date"] = display_df["date"].dt.strftime("%d/%m %H:%M")
            
            # Version compatible (sans matplotlib)
            st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun match trouvé pour ce joueur.")

# =========================================================
# PAGE 2 : LADDER (CLASSEMENT)
# =========================================================
elif page == "🌍 Top Ladder (EUW/KR)":
    st.title("🌍 Classement SoloQ - Top 100")
    
    try:
        with open("leaderboard_data.json", "r") as f:
            ladder_data = json.load(f)
    except FileNotFoundError:
        st.error("⚠️ Fichier 'leaderboard_data.json' introuvable. Lance 'dev/Fetch_leaderboard.py' !")
        st.stop()
        
    st.caption(f"Dernière MàJ : {ladder_data.get('last_update', '?')}")
    
    region = st.selectbox("Choisir la région", ["EUW", "KR"])
    
    if region in ladder_data["regions"]:
        data = ladder_data["regions"][region]
        df_ladder = pd.DataFrame(data)
        
        # Ajout des médailles
        if not df_ladder.empty:
            df_ladder.insert(0, "Rank", range(1, len(df_ladder) + 1))
            def get_medal(rank):
                return "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else str(rank)
            df_ladder["Rank"] = df_ladder["Rank"].apply(get_medal)
            
            st.dataframe(
                df_ladder[["Rank", "name", "tier", "lp", "winrate", "wins", "losses"]],
                column_config={
                    "winrate": st.column_config.ProgressColumn(
                        "Winrate (%)", format="%.1f%%", min_value=0, max_value=100
                    ),
                    "tier": st.column_config.TextColumn("Tier"),
                },
                use_container_width=True,
                hide_index=True,
                height=800
            )
        else:
            st.warning("Liste vide pour cette région.")
    else:
        st.warning("Pas de données pour cette région.")