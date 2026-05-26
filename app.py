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

if "seed" not in st.session_state:
    st.session_state.seed = 42

# =========================================================
# GERADOR DINÂMICO
# =========================================================

def gerar_base_ativos(seed):

    np.random.seed(seed)

    ativos = [
        # =====================================================
    # AÇÕES
    # =====================================================

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

    # =====================================================
    # ETFs
    # =====================================================

    "BOVA11.SA",
    "IVVB11.SA",
    "SMAL11.SA",
    "HASH11.SA",
    "GOLD11.SA",
    "DIVO11.SA",
    "NDIV11.SA",

    # =====================================================
    # FIIs
    # =====================================================

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

    # =====================================================
    # BDRs
    # =====================================================

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

    setups = [
        "Pullback EMA09",
        "Pullback EMA29",
        "Rompimento",
        "IFR2"
    ]

    lista = []

    for ativo in ativos:

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

        score = np.random.randint(55, 99)

        volume = round(
            np.random.uniform(0.5, 4.5),
            2
        )

        adx = round(
            np.random.uniform(10, 50),
            1
        )

        setup = np.random.choice(setups)

        lista.append({
            "Ativo": ativo,
            "Setup": setup,
            "Entrada": entrada,
            "Alvo": alvo,
            "Stop": stop,
            "Score": score,
            "Volume Relativo": volume,
            "ADX": adx,
            "Tendência": "Alta"
        })

    return pd.DataFrame(lista)

# =========================================================
# FUNÇÕES
# =========================================================

def aplicar_filtros(
    df,
    score_min,
    volume_min,
    adx_min,
    setup
):

    resultado = df.copy()

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

    return resultado.sort_values(
        by="Score",
        ascending=False
    )

def calcular_indice(df):

    if len(df) == 0:
        return 0

    score = df["Score"].mean()

    adx = df["ADX"].mean()

    indice = (
        score * 0.7 +
        adx * 0.3
    ) / 10

    return round(indice, 1)

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

# =========================================================
# BOTÃO GLOBAL DE RECÁLCULO
# =========================================================

if st.sidebar.button("🔄 Recalcular Mercado"):

    st.session_state.seed = np.random.randint(
        1,
        100000
    )

    st.rerun()

# =========================================================
# BASE PRINCIPAL
# =========================================================

df_base = gerar_base_ativos(
    st.session_state.seed
)

# =========================================================
# HEADER
# =========================================================

indice = calcular_indice(df_base)

col1, col2 = st.columns([5, 1])

with col1:

    st.title(
        "📈 Swing Trade Profissional"
    )

with col2:

    st.metric(
        "Mercado",
        f"{indice}/10"
    )

st.markdown("---")

# =========================================================
# DASHBOARD
# =========================================================

if menu == "Dashboard":

    st.subheader("📊 Dashboard Geral")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Ativos",
            len(df_base)
        )

    with col2:

        st.metric(
            "Score Médio",
            round(
                df_base["Score"].mean(),
                1
            )
        )

    with col3:

        st.metric(
            "ADX Médio",
            round(
                df_base["ADX"].mean(),
                1
            )
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

    melhores = df_base.sort_values(
        by="Score",
        ascending=False
    )

    st.subheader(
        "🏆 Ranking das Oportunidades"
    )

    st.dataframe(
        melhores,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    fig = px.bar(
        melhores.head(10),
        x="Ativo",
        y="Score",
        color="Setup",
        title="Top 10 Scores"
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

    st.subheader(
        "🔎 Scanner Inteligente"
    )

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

    # =====================================================
    # BOTÃO DE EXECUÇÃO
    # =====================================================

    if st.button("▶ Executar Scanner"):

        resultado = aplicar_filtros(
            df_base,
            score_min,
            volume_min,
            adx_min,
            setup
        )

        st.success(
            f"{len(resultado)} ativos encontrados."
        )

        st.markdown("---")

        if len(resultado) == 0:

            st.warning(
                "Nenhum ativo encontrado."
            )

        else:

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Quantidade",
                    len(resultado)
                )

            with col2:

                st.metric(
                    "Maior Score",
                    resultado["Score"].max()
                )

            with col3:

                st.metric(
                    "ADX Médio",
                    round(
                        resultado["ADX"].mean(),
                        1
                    )
                )

            st.markdown("---")

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
                template="plotly_dark",
                title="Força dos Ativos",
                height=500
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
            "Quantidade de Trades",
            20,
            300,
            100
        )

    if st.button("▶ Rodar Backtest"):

        seed = np.random.randint(
            1,
            100000
        )

        np.random.seed(seed)

        winrate = round(
            np.random.uniform(55, 80),
            1
        )

        payoff = round(
            np.random.uniform(1.0, 2.5),
            2
        )

        lucro = round(
            np.random.uniform(10, 60),
            1
        )

        drawdown = round(
            np.random.uniform(2, 15),
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
            "Trade": range(1, trades + 1),
            "Resultado": np.random.normal(
                0.8,
                2.2,
                trades
            ).cumsum()
        })

        st.markdown("---")

        fig = px.line(
            historico,
            x="Trade",
            y="Resultado",
            title=f"Evolução Patrimonial — {setup_bt}"
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
# CONFIGURAÇÕES
# =========================================================

elif menu == "Configurações":

    st.subheader(
        "⚙️ Configurações"
    )

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
        "Score mínimo padrão",
        50,
        100,
        80
    )

    volume = st.slider(
        "Volume mínimo padrão",
        0.5,
        5.0,
        1.0
    )

    adx = st.slider(
        "ADX mínimo padrão",
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
