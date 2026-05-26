import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px

from ta.trend import EMAIndicator
from ta.trend import ADXIndicator
from ta.volatility import AverageTrueRange
from ta.momentum import RSIIndicator

from datetime import datetime

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(
    page_title="Swing Trade Real",
    page_icon="📈",
    layout="wide"
)

# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.main {
    background-color: #0E1117;
}

section[data-testid="stSidebar"] {
    background-color: #111827;
}

h1, h2, h3 {
    color: white;
}

div[data-testid="stMetric"] {
    background-color: #161B22;
    border: 1px solid #2A2F3A;
    border-radius: 12px;
    padding: 15px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# LISTA DE ATIVOS
# =========================================================

ATIVOS = [

    # AÇÕES

    "PETR4.SA",
    "VALE3.SA",
    "BBAS3.SA",
    "ITUB4.SA",
    "WEGE3.SA",
    "PRIO3.SA",
    "RENT3.SA",
    "BBDC4.SA",

    # ETFs

    "BOVA11.SA",
    "IVVB11.SA",
    "SMAL11.SA",
    "HASH11.SA",

    # FIIs

    "HGLG11.SA",
    "MXRF11.SA",
    "KNRI11.SA",
    "AUVP11.SA",

    # BDRs

    "AAPL34.SA",
    "GOGL34.SA",
    "MSFT34.SA",
    "TSLA34.SA"
]

# =========================================================
# CACHE
# =========================================================

@st.cache_data(ttl=1800)
def baixar_dados(ativo):

    df = yf.download(
        ativo,
        period="1y",
        interval="1d",
        progress=False,
        auto_adjust=True
    )

    if df.empty:
        return None

    df.dropna(inplace=True)

    return df

# =========================================================
# INDICADORES
# =========================================================

def calcular_indicadores(df):

    df = df.copy()

    # EMA 9

    df["EMA9"] = EMAIndicator(
        close=df["Close"],
        window=9
    ).ema_indicator()

    # EMA 21

    df["EMA21"] = EMAIndicator(
        close=df["Close"],
        window=21
    ).ema_indicator()

    # EMA 50

    df["EMA50"] = EMAIndicator(
        close=df["Close"],
        window=50
    ).ema_indicator()

    # RSI

    df["RSI"] = RSIIndicator(
        close=df["Close"],
        window=14
    ).rsi()

    # ATR

    df["ATR"] = AverageTrueRange(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=14
    ).average_true_range()

    # ADX

    adx = ADXIndicator(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=14
    )

    df["ADX"] = adx.adx()

    # Volume médio

    df["VOL_MEDIA"] = df["Volume"].rolling(20).mean()

    # Volume relativo

    df["VOL_REL"] = (
        df["Volume"] / df["VOL_MEDIA"]
    )

    return df

# =========================================================
# SCANNER
# =========================================================

def executar_scanner():

    resultados = []

    progresso = st.progress(0)

    total = len(ATIVOS)

    for i, ativo in enumerate(ATIVOS):

        try:

            progresso.progress((i + 1) / total)

            df = baixar_dados(ativo)

            if df is None:
                continue

            df = calcular_indicadores(df)

            ultimo = df.iloc[-1]

            setup = None

            # =================================================
            # PULLBACK EMA9
            # =================================================

            if (
                ultimo["Close"] > ultimo["EMA21"]
                and ultimo["Close"] > ultimo["EMA50"]
                and ultimo["ADX"] > 20
                and ultimo["RSI"] > 50
            ):

                setup = "Pullback EMA9"

            # =================================================
            # ROMPIMENTO
            # =================================================

            max_20 = df["High"].rolling(20).max().iloc[-2]

            if (
                ultimo["Close"] > max_20
                and ultimo["VOL_REL"] > 1.5
            ):

                setup = "Rompimento"

            # =================================================
            # IFR2
            # =================================================

            if ultimo["RSI"] < 25:

                setup = "IFR2"

            # =================================================
            # GERAR OPERAÇÃO
            # =================================================

            if setup:

                entrada = round(float(ultimo["Close"]), 2)

                atr = round(float(ultimo["ATR"]), 2)

                stop = round(
                    entrada - (atr * 1.5),
                    2
                )

                alvo = round(
                    entrada + (atr * 3),
                    2
                )

                score = int(
                    (
                        ultimo["ADX"] * 0.4 +
                        ultimo["VOL_REL"] * 20 +
                        ultimo["RSI"] * 0.4
                    )
                )

                resultados.append({

                    "Ativo": ativo,

                    "Setup": setup,

                    "Preço": entrada,

                    "ATR": atr,

                    "ADX": round(float(ultimo["ADX"]), 1),

                    "RSI": round(float(ultimo["RSI"]), 1),

                    "Volume Relativo": round(
                        float(ultimo["VOL_REL"]),
                        2
                    ),

                    "Alvo": alvo,

                    "Stop": stop,

                    "Score": score
                })

        except:
            pass

    progresso.empty()

    if len(resultados) == 0:
        return pd.DataFrame()

    resultado = pd.DataFrame(resultados)

    resultado = resultado.sort_values(
        by="Score",
        ascending=False
    )

    return resultado

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("📈 Swing Trade Real")

menu = st.sidebar.radio(
    "Menu",
    [
        "Dashboard",
        "Scanner",
        "Gráfico"
    ]
)

st.sidebar.markdown("---")

# =========================================================
# DASHBOARD
# =========================================================

if menu == "Dashboard":

    st.title("📊 Dashboard")

    st.info(
        "Dados reais via Yahoo Finance"
    )

    st.markdown("---")

    if st.button("🔄 Atualizar Mercado"):

        st.cache_data.clear()

    scanner = executar_scanner()

    if scanner.empty:

        st.warning(
            "Nenhuma oportunidade encontrada."
        )

    else:

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Ativos",
                len(scanner)
            )

        with col2:
            st.metric(
                "Score Médio",
                round(scanner["Score"].mean(), 1)
            )

        with col3:
            st.metric(
                "ADX Médio",
                round(scanner["ADX"].mean(), 1)
            )

        with col4:
            st.metric(
                "ATR Médio",
                round(scanner["ATR"].mean(), 2)
            )

        st.markdown("---")

        st.dataframe(
            scanner,
            use_container_width=True,
            hide_index=True,
            height=650
        )

        fig = px.bar(
            scanner.head(15),
            x="Ativo",
            y="Score",
            color="Setup",
            title="Top Operações"
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

    st.title("🔎 Scanner Operacional")

    col1, col2 = st.columns(2)

    with col1:

        score_min = st.slider(
            "Score mínimo",
            0,
            100,
            50
        )

    with col2:

        adx_min = st.slider(
            "ADX mínimo",
            10,
            50,
            20
        )

    st.markdown("---")

    if st.button("▶ Executar Scanner"):

        scanner = executar_scanner()

        if scanner.empty:

            st.warning(
                "Nenhum ativo encontrado."
            )

        else:

            scanner = scanner[
                scanner["Score"] >= score_min
            ]

            scanner = scanner[
                scanner["ADX"] >= adx_min
            ]

            st.success(
                f"{len(scanner)} oportunidades encontradas."
            )

            st.dataframe(
                scanner,
                use_container_width=True,
                hide_index=True,
                height=650
            )

            fig = px.scatter(
                scanner,
                x="ADX",
                y="Score",
                size="ATR",
                color="Setup",
                hover_data=["Ativo"],
                title="Mapa de Força"
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
# GRÁFICO
# =========================================================

elif menu == "Gráfico":

    st.title("📉 Análise Técnica")

    ativo = st.selectbox(
        "Escolha o ativo",
        ATIVOS
    )

    df = baixar_dados(ativo)

    if df is not None:

        df = calcular_indicadores(df)

        fig = px.line(
            df,
            y=[
                "Close",
                "EMA9",
                "EMA21",
                "EMA50"
            ],
            title=ativo
        )

        fig.update_layout(
            template="plotly_dark",
            height=700
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        ultimo = df.iloc[-1]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Preço",
                round(float(ultimo["Close"]), 2)
            )

        with col2:
            st.metric(
                "RSI",
                round(float(ultimo["RSI"]), 1)
            )

        with col3:
            st.metric(
                "ADX",
                round(float(ultimo["ADX"]), 1)
            )

        with col4:
            st.metric(
                "ATR",
                round(float(ultimo["ATR"]), 2)
            )

# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    f'''
Última atualização:
{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
'''
)
