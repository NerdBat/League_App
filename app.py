import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="LoL Esport Dashboard",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CHARGEMENT DES DONNÉES ---
DATA_FILE = "esport_data.json"

@st.cache_data # Empêche de recharger le fichier à chaque clic (optimisation)
def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return None

raw_data = load_data()

# --- SIDEBAR (FILTRES) ---
st.sidebar.title("🎛️ Paramètres")
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/LoL_Icon_Render.png/640px-LoL_Icon_Render.png", width=100)

if raw_data:
    last_update = raw_data.get("last_update", "Inconnue")
    st.sidebar.caption(f"📅 Dernière MàJ : {last_update}")
    
    # Liste des joueurs
    players_list = list(raw_data["players"].keys())
    selected_player = st.sidebar.selectbox("Sélectionner un joueur", players_list)
    
    # Récupération des matchs du joueur
    matches = raw_data["players"][selected_player]
    df = pd.DataFrame(matches)
    
    # Conversion date
    df['date'] = pd.to_datetime(df['game_date'], unit='ms')
    
else:
    st.error(f"❌ Fichier '{DATA_FILE}' introuvable. Lance d'abord Fetch_data.py !")
    st.stop()

# --- CORPS PRINCIPAL ---
st.title(f"📊 Analyse : {selected_player}")

if df.empty:
    st.warning("Aucune donnée pour ce joueur.")
    st.stop()

# 1. KPIs (Indicateurs Clés)
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

# 2. ONGLETS D'ANALYSE
tab1, tab2, tab3 = st.tabs(["⚔️ Champions", "📈 Performance", "📝 Historique"])

with tab1:
    col_graph1, col_graph2 = st.columns([2, 1])
    
    with col_graph1:
        st.subheader("Pool de Champions")
        # Regroupement par champion
        champ_stats = df.groupby("champion").agg(
            Games=('match_id', 'count'),
            Wins=('win', 'sum'),
            Avg_DPM=('dpm', 'mean')
        ).reset_index()
        champ_stats['Winrate'] = (champ_stats['Wins'] / champ_stats['Games']) * 100
        champ_stats = champ_stats.sort_values(by="Games", ascending=False)
        
        # Graphique interactif
        fig = px.bar(
            champ_stats, 
            x="champion", 
            y="Games", 
            color="Winrate",
            color_continuous_scale=["red", "yellow", "green"],
            range_color=[0, 100],
            text="Winrate",
            title="Matchs joués & Winrate par Champion"
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
        
        most_played = champ_stats.iloc[0]
        st.write(f"**🛡️ Main:** {most_played['champion']}")

with tab2:
    st.subheader("Évolution des Dégâts (DPM)")
    # Graphique de ligne
    fig2 = px.line(
        df.sort_values(by="game_date"), 
        x="date", 
        y="dpm", 
        markers=True, 
        color="win",
        color_discrete_map={True: "green", False: "red"},
        hover_data=["champion", "kda"],
        title="DPM par partie (Vert = Victoire / Rouge = Défaite)"
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    st.subheader("Corrélation Or vs Dégâts")
    fig3 = px.scatter(
        df, 
        x="gpm", 
        y="dpm", 
        color="champion", 
        size="kda", 
        hover_name="champion",
        title="Gold/min vs Dégâts/min (Taille = KDA)"
    )
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    st.subheader("Détail des Matchs")
    
    # Mise en forme du tableau pour qu'il soit joli
    display_df = df[[
        "date", "champion", "win", "kda", "kills", "deaths", "assists", 
        "dpm", "cs_min", "vision_score"
    ]].copy()
    
    display_df["win"] = display_df["win"].apply(lambda x: "✅ VICTOIRE" if x else "❌ DÉFAITE")
    display_df["date"] = display_df["date"].dt.strftime("%d/%m %H:%M")
    
    st.dataframe(
        display_df.style.background_gradient(subset=["kda", "dpm"], cmap="Blues"),
        use_container_width=True,
        hide_index=True
    )