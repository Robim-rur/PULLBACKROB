import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path
from datetime import datetime
import plotly.express as px

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
# PASTAS
# =========================================================

Path("data").mkdir(exist_ok=True)

DB_PATH = "data/historico.db"

# =========================================================
# CSS
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
            volume REAL,
            adx REAL,
            data TEXT
        )
    """)

    conn.commit()
    conn.close()

inicializar_db()

# =========================================================
# SESSION STATE
# =========================================================

if "dados" not in st.session_state:
    st.session_state.dados = None

if "scanner_resultado" not in st.session_state:
    st.session_state.scanner_resultado = None

if "backtest_resultado" not in st.session_state:
    st.session_state.backtest_resultado = None

# =========================================================
# LISTA DE ATIVOS
# =========================================================

ATIVOS = [

    "PETR4.SA",
    "VALE3.SA",
    "BBAS3.SA",
    "ITUB4.SA",
    "BBDC4.SA",
    "WEGE3.SA",
    "PRIO3.SA",
    "RENT3.SA",
    "ELET3.SA",
    "ELET6.SA",
    "CPLE6.SA",
    "CMIG4.SA",
    "TAEE11.SA",
    "EGIE3.SA",
    "VIVT3.SA",
    "TIMS3.SA",
    "ABEV3.SA",
    "RADL3.SA",
    "SUZB3.SA",
    "GGBR4.SA",
    "GOAU4.SA",
    "USIM5.SA",
    "CSNA3.SA",
    "RAIL3.SA",
    "SBSP3.SA",
    "EQTL3.SA",
    "HYPE3.SA",
    "MULT3.SA",
    "LREN3.SA",
    "ARZZ3.SA",
    "TOTS3.SA",
    "EMBR3.SA",
    "JBSS3.SA",
    "BEEF3.SA",
    "MRFG3.SA",
    "BRFS3.SA",
    "SLCE3.SA",
    "SMTO3.SA",
    "B3SA3.SA",
    "BBSE3.SA",
    "BPAC11.SA",
    "SANB11.SA",
    "ITSA4.SA",
    "BRSR6.SA",
    "CXSE3.SA",
    "POMO4.SA",
    "STBP3.SA",
    "TUPY3.SA",
    "DIRR3.SA",
    "CYRE3.SA",
    "EZTC3.SA",
    "JHSF3.SA",
    "KEPL3.SA",
    "POSI3.SA",
    "MOVI3.SA",
    "PETZ3.SA",
    "COGN3.SA",
    "YDUQ3.SA",
    "MGLU3.SA",
    "NTCO3.SA",
    "AZUL4.SA",
    "GOLL4.SA",
    "CVCB3.SA",
    "RRRP3.SA",
    "RECV3.SA",
    "ENAT3.SA",
    "ORVR3.SA",
    "AURE3.SA",
    "ENEV3.SA",
    "UGPA3.SA",

    "BOVA11.SA",
    "IVVB11.SA",
    "SMAL11.SA",
    "HASH11.SA",
    "GOLD11.SA",
    "DIVO11.SA",
    "NDIV11.SA",

    "HGLG11.SA",
    "XPLG11.SA",
    "VISC11.SA",
    "MXRF11.SA",
    "KNRI11.SA",
    "KNCR11.SA",
    "KNIP11.SA",
    "CPTS11.SA",
    "IRDM11.SA",
    "TRXF11.SA",
    "TGAR11.SA",
    "HGRU11.SA",
    "ALZR11.SA",
    "AUVP11.SA",
    "GARE11.SA",
    "IEEX11.SA",
    "UTLL11.SA",
    "GGRC11.SA",

    "AAPL34.SA",
    "AMZO34.SA",
    "GOGL34.SA",
    "MSFT34.SA",
    "TSLA34.SA",
    "META34.SA",
    "NFLX34.SA",
    "NVDC34.SA",
    "MELI34.SA",
    "BABA34.SA",
    "DISB34.SA",
    "PYPL34.SA",
    "JNJB34.SA",
    "VISA34.SA",
    "WMTB34.SA",
    "NIKE34.SA",
    "ADBE34.SA",
    "CSCO34.SA",
    "INTC34.SA",
    "JPMC34.SA",
    "ORCL34.SA"
]

# =========================================================
# GERAR DADOS
# =========================================================

def gerar_dados():

    setups = [
        "Pullback EMA09",
        "Pullback EMA29",
        "Rompimento",
        "IFR2"
    ]

    lista = []

    for ativo in ATIVOS:

        entrada = round(
            np.random.uniform(10, 80),
            2
        )

        alvo = round(
            entrada * np.random.uniform(1.03, 1.12),
            2
        )

        stop = round(
            entrada * np.random.uniform(0.92, 0.97),
            2
        )

        lista.append({

            "Ativo": ativo,

            "Setup": np.random.choice(setups),

            "Entrada": entrada,

            "Alvo": alvo,

            "Stop": stop,

            "Score": np.random.randint(50, 100),

            "Volume Relativo": round(
                np.random.uniform(0.5, 5),
                2
            ),

            "ADX": round(
                np.random.uniform(10, 50),
                1
            ),

            "Tendência": "Alta"
        })

    return pd.DataFrame(lista)

# =========================================================
# INICIALIZAÇÃO
# =========================================================

if st.session_state.dados is None:
    st.session_state.dados = gerar_dados()

df_base = st.session_state.dados

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("📈 Swing Trade AUVP11")

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

# =========================================================
# BOTÃO GLOBAL
# =========================================================

if st.sidebar.button("🔄 Gerar Novo Mercado"):

    st.session_state.dados = gerar_dados()

    st.session_state.scanner_resultado = None

    st.session_state.backtest_resultado = None

    st.success("Novo mercado gerado.")

# =========================================================
# HEADER
# =========================================================

indice = round(
    (
        df_base["Score"].mean() * 0.7 +
        df_base["ADX"].mean() * 0.3
    ) / 10,
    1
)

col1, col2 = st.columns([5, 1])

with col1:
    st.title("📈 Swing Trade Profissional")

with col2:
    st.metric("Mercado", f"{indice}/10")

st.markdown("---")

# =========================================================
# DASHBOARD
# =========================================================

if menu == "Dashboard":

    st.subheader("📊 Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Ativos", len(df_base))

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

    ranking = df_base.sort_values(
        by="Score",
        ascending=False
    )

    st.dataframe(
        ranking,
        use_container_width=True,
        hide_index=True,
        height=650
    )

    st.markdown("---")

    fig = px.bar(
        ranking.head(15),
        x="Ativo",
        y="Score",
        color="Setup",
        title="Top 15 Scores"
    )

    fig.update_layout(
        template="plotly_dark",
        height=500
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =========================================================
# SCANNER
# =========================================================

elif menu == "Scanner":

    st.subheader("🔎 Scanner")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        score_min = st.slider(
            "Score mínimo",
            50,
            100,
            80
        )

    with col2:
        volume_min = st.slider(
            "Volume mínimo",
            0.5,
            5.0,
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

    st.markdown("---")

    if st.button("▶ Executar Scanner"):

        resultado = df_base.copy()

        resultado = resultado[
            resultado["Score"] >= score_min
        ]

        resultado = resultado[
            resultado["Volume Relativo"] >= volume_min
        ]

        resultado = resultado[
            resultado["ADX"] >= adx_min
        ]

        if setup != "Todos":

            resultado = resultado[
                resultado["Setup"] == setup
            ]

        resultado = resultado.sort_values(
            by="Score",
            ascending=False
        )

        st.session_state.scanner_resultado = resultado

    if st.session_state.scanner_resultado is not None:

        resultado = st.session_state.scanner_resultado

        st.success(
            f"{len(resultado)} ativos encontrados."
        )

        st.dataframe(
            resultado,
            use_container_width=True,
            hide_index=True,
            height=650
        )

        st.markdown("---")

        fig = px.scatter(
            resultado,
            x="ADX",
            y="Score",
            color="Setup",
            size="Volume Relativo",
            hover_data=["Ativo"],
            title="Força Relativa"
        )

        fig.update_layout(
            template="plotly_dark",
            height=600
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

        trades = st.slider(
            "Trades",
            20,
            300,
            100
        )

    st.markdown("---")

    if st.button("▶ Rodar Backtest"):

        # =====================================================
        # RESULTADOS DIFERENTES POR SETUP
        # =====================================================

        parametros = {

            "Pullback EMA09": {
                "win_min": 65,
                "win_max": 80,
                "payoff_min": 1.1,
                "payoff_max": 1.8,
                "volatilidade": 1.5
            },

            "Pullback EMA29": {
                "win_min": 55,
                "win_max": 72,
                "payoff_min": 1.4,
                "payoff_max": 2.3,
                "volatilidade": 2.2
            },

            "Rompimento": {
                "win_min": 45,
                "win_max": 65,
                "payoff_min": 1.8,
                "payoff_max": 3.5,
                "volatilidade": 3.5
            },

            "IFR2": {
                "win_min": 70,
                "win_max": 88,
                "payoff_min": 0.8,
                "payoff_max": 1.4,
                "volatilidade": 1.2
            }
        }

        p = parametros[setup_bt]

        winrate = round(
            np.random.uniform(
                p["win_min"],
                p["win_max"]
            ),
            1
        )

        payoff = round(
            np.random.uniform(
                p["payoff_min"],
                p["payoff_max"]
            ),
            2
        )

        lucro = round(
            (
                winrate / 100
            ) * payoff * np.random.uniform(15, 35),
            1
        )

        drawdown = round(
            np.random.uniform(2, 15),
            1
        )

        historico = pd.DataFrame({

            "Trade": range(
                1,
                trades + 1
            ),

            "Resultado": np.random.normal(
                payoff,
                p["volatilidade"],
                trades
            ).cumsum()
        })

        st.session_state.backtest_resultado = {
            "setup": setup_bt,
            "winrate": winrate,
            "payoff": payoff,
            "lucro": lucro,
            "drawdown": drawdown,
            "historico": historico
        }

    # =====================================================
    # EXIBIÇÃO
    # =====================================================

    if st.session_state.backtest_resultado is not None:

        bt = st.session_state.backtest_resultado

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Win Rate",
                f"{bt['winrate']}%"
            )

        with col2:
            st.metric(
                "Payoff",
                bt["payoff"]
            )

        with col3:
            st.metric(
                "Lucro",
                f"+{bt['lucro']}%"
            )

        with col4:
            st.metric(
                "Drawdown",
                f"-{bt['drawdown']}%"
            )

        st.markdown("---")

        fig = px.line(
            bt["historico"],
            x="Trade",
            y="Resultado",
            title=f"Evolução Patrimonial — {bt['setup']}"
        )

        fig.update_layout(
            template="plotly_dark",
            height=550
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
        20.0,
        8.0
    )

    stop = st.slider(
        "Stop Loss (%)",
        1.0,
        15.0,
        5.0
    )

    score = st.slider(
        "Score padrão",
        50,
        100,
        80
    )

    volume = st.slider(
        "Volume padrão",
        0.5,
        5.0,
        1.0
    )

    adx = st.slider(
        "ADX padrão",
        10,
        50,
        20
    )

    st.markdown("---")

    if st.button("💾 Salvar Configurações"):

        conn = conectar_db()

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO configuracoes (
                gain,
                stop,
                score,
                volume,
                adx,
                data
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            gain,
            stop,
            score,
            volume,
            adx,
            datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"
            )
        ))

        conn.commit()
        conn.close()

        st.success(
            "Configurações salvas."
        )

# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    f"""
Última atualização:
{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""
)
