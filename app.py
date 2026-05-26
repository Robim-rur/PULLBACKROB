import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(
    page_title="Swing Trade AUVP11",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# PASTA / DATABASE
# =========================================================

Path("data").mkdir(exist_ok=True)

DB_PATH = "data/historico.db"

# =========================================================
# CSS MELHORADO
# =========================================================

st.markdown("""
<style>

.main {
    background-color: #0E1117;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
}

section[data-testid="stSidebar"] {
    background-color: #111827;
}

div[data-testid="stMetric"] {
    background-color: #161B22;
    border: 1px solid #2A2F3A;
    border-radius: 12px;
    padding: 15px;
}

.stDataFrame {
    border: 1px solid #2A2F3A;
    border-radius: 12px;
}

h1, h2, h3 {
    color: white;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# DATABASE
# =========================================================

def conectar_db():
    return sqlite3.connect(DB_PATH)

def inicializar_db():

    conn = conectar_db()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gain REAL,
            stop REAL,
            score INTEGER,
            volume REAL
        )
    """)

    conn.commit()
    conn.close()

inicializar_db()

# =========================================================
# GERADOR DINÂMICO DE DADOS
# =========================================================

@st.cache_data
def gerar_base_ativos():

    np.random.seed(42)

    ativos = [
        "PETR4", "VALE3", "ITUB4", "WEGE3",
        "BBAS3", "PRIO3", "BBDC4", "ABEV3",
        "EGIE3", "CMIG4", "TAEE11", "CPLE6",
        "SUZB3", "GGBR4", "RENT3", "RADL3",
        "LREN3", "JBSS3", "CYRE3", "ELET3"
    ]

    setups = [
        "Pullback EMA09",
        "Pullback EMA29",
        "Rompimento",
        "IFR2"
    ]

    lista = []

    for ativo in ativos:

        entrada = round(np.random.uniform(10, 80), 2)

        variacao = np.random.uniform(0.03, 0.10)

        alvo = round(
            entrada * (1 + variacao),
            2
        )

        stop = round(
            entrada * (1 - np.random.uniform(0.03, 0.06)),
            2
        )

        lista.append({
            "Ativo": ativo,
            "Setup": np.random.choice(setups),
            "Entrada": entrada,
            "Alvo": alvo,
            "Stop": stop,
            "Score": np.random.randint(60, 98),
            "Volume Relativo": round(
                np.random.uniform(0.8, 3.5),
                2
            ),
            "ADX": round(
                np.random.uniform(18, 45),
                1
            ),
            "Tendência": "Alta"
        })

    return pd.DataFrame(lista)

# =========================================================
# FUNÇÕES
# =========================================================

def calcular_indice_mercado(df):

    media_score = df["Score"].mean()

    media_adx = df["ADX"].mean()

    indice = (
        (media_score * 0.7) +
        (media_adx * 0.3)
    ) / 10

    return round(indice, 1)

def aplicar_filtros(
    df,
    score_min,
    setup,
    volume_min,
    adx_min
):

    filtrado = df.copy()

    filtrado = filtrado[
        filtrado["Score"] >= score_min
    ]

    filtrado = filtrado[
        filtrado["Volume Relativo"] >= volume_min
    ]

    filtrado = filtrado[
        filtrado["ADX"] >= adx_min
    ]

    if setup != "Todos":
        filtrado = filtrado[
            filtrado["Setup"] == setup
        ]

    return filtrado

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("📈 Swing Trade AUVP11")

st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Menu",
    [
        "Dashboard",
        "Scanner",
        "Backtest",
        "Configurações"
    ]
)

st.sidebar.markdown("---")

st.sidebar.markdown("""
### Estratégia

✅ Operações compradas  
✅ Tendência de alta  
✅ Filtro ADX  
✅ Gestão de risco  
✅ Continuidade de tendência  
""")

# =========================================================
# BASE PRINCIPAL
# =========================================================

df_base = gerar_base_ativos()

# =========================================================
# HEADER
# =========================================================

indice_mercado = calcular_indice_mercado(df_base)

col1, col2 = st.columns([5, 1])

with col1:
    st.title("📈 Swing Trade Profissional")

with col2:
    st.metric(
        "Mercado",
        f"{indice_mercado}/10"
    )

st.markdown("---")

# =========================================================
# DASHBOARD
# =========================================================

if menu == "Dashboard":

    st.subheader("📊 Dashboard Geral")

    melhores = df_base.sort_values(
        by="Score",
        ascending=False
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Ativos",
            len(df_base)
        )

    with col2:
        st.metric(
            "Score Médio",
            round(df_base["Score"].mean(), 1)
        )

    with col3:
        st.metric(
            "ADX Médio",
            round(df_base["ADX"].mean(), 1)
        )

    with col4:
        st.metric(
            "Volume Médio",
            round(
                df_base["Volume Relativo"].mean(),
                2
            )
        )

    st.markdown("---")

    st.subheader("🏆 Top Oportunidades")

    st.dataframe(
        melhores,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    grafico = px.bar(
        melhores.head(10),
        x="Ativo",
        y="Score",
        color="Setup",
        title="Top 10 Scores"
    )

    st.plotly_chart(
        grafico,
        use_container_width=True
    )

# =========================================================
# SCANNER
# =========================================================

elif menu == "Scanner":

    st.subheader("🔎 Scanner Inteligente")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        score_min = st.slider(
            "Score mínimo",
            60,
            100,
            80
        )

    with col2:
        volume_min = st.slider(
            "Volume Relativo",
            0.5,
            4.0,
            1.0
        )

    with col3:
        adx_min = st.slider(
            "ADX mínimo",
            10,
            50,
            20
        )

    with col4:
        setup = st.selectbox(
            "Setup",
            [
                "Todos",
                "Pullback EMA09",
                "Pullback EMA29",
                "Rompimento",
                "IFR2"
            ]
        )

    resultado = aplicar_filtros(
        df_base,
        score_min,
        setup,
        volume_min,
        adx_min
    )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Resultados",
            len(resultado)
        )

    with col2:
        if len(resultado) > 0:
            st.metric(
                "Melhor Score",
                resultado["Score"].max()
            )
        else:
            st.metric(
                "Melhor Score",
                0
            )

    with col3:
        if len(resultado) > 0:
            st.metric(
                "ADX Médio",
                round(
                    resultado["ADX"].mean(),
                    1
                )
            )
        else:
            st.metric(
                "ADX Médio",
                0
            )

    st.markdown("---")

    if len(resultado) == 0:

        st.warning(
            "Nenhum ativo encontrado com os filtros atuais."
        )

    else:

        resultado = resultado.sort_values(
            by="Score",
            ascending=False
        )

        st.dataframe(
            resultado,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=resultado["Ativo"],
                y=resultado["Score"],
                mode="lines+markers",
                name="Score"
            )
        )

        fig.update_layout(
            title="Scores dos Ativos Filtrados",
            template="plotly_dark",
            height=450
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =========================================================
# BACKTEST
# =========================================================

elif menu == "Backtest":

    st.subheader("📈 Backtest")

    col1, col2 = st.columns(2)

    with col1:

        setup_bt = st.selectbox(
            "Setup",
            [
                "Pullback EMA09",
                "Pullback EMA29",
                "Rompimento",
                "IFR2"
            ]
        )

    with col2:

        quantidade = st.slider(
            "Quantidade de Trades",
            20,
            300,
            100
        )

    if st.button("▶ Rodar Backtest"):

        np.random.seed(1)

        winrate = round(
            np.random.uniform(55, 78),
            1
        )

        payoff = round(
            np.random.uniform(1.1, 2.0),
            2
        )

        lucro = round(
            (
                (winrate / 100) * payoff
            ) * quantidade / 5,
            1
        )

        drawdown = round(
            np.random.uniform(3, 12),
            1
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Win Rate",
                f"{winrate}%"
            )

        with col2:
            st.metric(
                "Payoff",
                payoff
            )

        with col3:
            st.metric(
                "Lucro",
                f"+{lucro}%"
            )

        with col4:
            st.metric(
                "Drawdown",
                f"-{drawdown}%"
            )

        historico = pd.DataFrame({
            "Trade": range(1, quantidade + 1),
            "Resultado": np.random.normal(
                0.8,
                2.5,
                quantidade
            ).cumsum()
        })

        fig = px.line(
            historico,
            x="Trade",
            y="Resultado",
            title=f"Evolução Patrimonial — {setup_bt}"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =========================================================
# CONFIGURAÇÕES
# =========================================================

elif menu == "Configurações":

    st.subheader("⚙️ Configurações")

    gain = st.slider(
        "Take Profit (%)",
        1.0,
        15.0,
        8.0
    )

    stop = st.slider(
        "Stop Loss (%)",
        1.0,
        10.0,
        5.0
    )

    score = st.slider(
        "Score mínimo padrão",
        50,
        100,
        80
    )

    volume = st.slider(
        "Volume relativo mínimo",
        0.5,
        5.0,
        1.0
    )

    if st.button("💾 Salvar"):

        conn = conectar_db()

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO configuracoes (
                gain,
                stop,
                score,
                volume
            )
            VALUES (?, ?, ?, ?)
        """, (
            gain,
            stop,
            score,
            volume
        ))

        conn.commit()
        conn.close()

        st.success(
            "Configurações salvas com sucesso."
        )

# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
)
