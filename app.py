# =========================================================
# APP.PY
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px

from ta.trend import ADXIndicator
from ta.trend import EMAIndicator
from ta.momentum import StochasticOscillator

from datetime import datetime

# =========================================================
# CONFIGURAÇÃO
# =========================================================

st.set_page_config(
    page_title="Scanner Quantitativo B3",
    page_icon="📈",
    layout="wide"
)

# =========================================================
# PARÂMETROS
# =========================================================

GAIN_FIXO = 0.03
LOSS_FIXO = 0.04

ADX_MINIMO = 20
VOLUME_MINIMO = 20_000_000

# =========================================================
# ATIVOS
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
    "GGBR4.SA",
    "CSNA3.SA",
    "GOAU4.SA",
    "RAIL3.SA",
    "SUZB3.SA",
    "JBSS3.SA",
    "EQTL3.SA",
    "VIVT3.SA",
    "TIMS3.SA",
    "RADL3.SA",
    "TOTS3.SA",
    "EMBR3.SA",

    # ETFs

    "BOVA11.SA",
    "IVVB11.SA",
    "SMAL11.SA",
    "HASH11.SA",

    # BDRs

    "AAPL34.SA",
    "GOGL34.SA",
    "MSFT34.SA",
    "TSLA34.SA",
    "META34.SA",
    "NVDC34.SA"
]

# =========================================================
# DOWNLOAD
# =========================================================

@st.cache_data(ttl=3600)
def baixar_dados(
    ativo,
    periodo="5y",
    intervalo="1d"
):

    try:

        df = yf.download(
            ativo,
            period=periodo,
            interval=intervalo,
            auto_adjust=True,
            progress=False,
            threads=False
        )

        if df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):

            df.columns = (
                df.columns
                .get_level_values(0)
            )

        colunas = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]

        for coluna in colunas:

            df[coluna] = pd.to_numeric(
                df[coluna],
                errors="coerce"
            )

        df.dropna(inplace=True)

        if len(df) < 100:
            return None

        return df

    except:

        return None

# =========================================================
# INDICADORES
# =========================================================

def calcular_indicadores(df):

    df = df.copy()

    # =====================================================
    # EMA21
    # =====================================================

    ema21 = EMAIndicator(
        close=df["Close"],
        window=21
    )

    df["EMA21"] = ema21.ema_indicator()

    # =====================================================
    # ESTOCÁSTICO
    # =====================================================

    estocastico = StochasticOscillator(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=14,
        smooth_window=3
    )

    df["K"] = estocastico.stoch()

    df["D"] = (
        df["K"]
        .rolling(3)
        .mean()
    )

    # =====================================================
    # ADX / DMI
    # =====================================================

    adx = ADXIndicator(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=14
    )

    df["ADX"] = adx.adx()

    df["DI_POS"] = adx.adx_pos()

    df["DI_NEG"] = adx.adx_neg()

    # =====================================================
    # VOLUME FINANCEIRO
    # =====================================================

    df["Financeiro"] = (
        df["Close"] *
        df["Volume"]
    )

    # =====================================================
    # EMA21 ASCENDENTE
    # =====================================================

    df["EMA21_ASC"] = (
        df["EMA21"] >
        df["EMA21"].shift(1)
    )

    # =====================================================
    # CANDLE ESTICADO
    # =====================================================

    df["AMPLITUDE"] = (
        (
            df["High"] -
            df["Low"]
        )
        /
        df["Close"]
    ) * 100

    df.dropna(inplace=True)

    return df

# =========================================================
# EXPECTÂNCIA
# =========================================================

def calcular_expectancia(winrate):

    pw = winrate / 100

    pl = 1 - pw

    expectativa = (

        (pw * GAIN_FIXO)

        -

        (pl * LOSS_FIXO)

    )

    return round(
        expectativa * 100,
        2
    )

# =========================================================
# BACKTEST
# =========================================================

def calcular_probabilidade(
    diario,
    semanal
):

    semanal["SEM_K_MAIOR"] = (
        semanal["K"] >
        semanal["D"]
    )

    total = 0

    gains = 0

    losses = 0

    for i in range(30, len(diario) - 30):

        try:

            candle = diario.iloc[i]

            data_candle = diario.index[i]

            semana = semanal[
                semanal.index <= data_candle
            ]

            if semana.empty:
                continue

            semana = semana.iloc[-1]

            # =================================================
            # FILTROS
            # =================================================

            filtro = (

                candle["K"] >
                candle["D"]

                and

                candle["DI_POS"] >
                candle["DI_NEG"]

                and

                candle["ADX"] > ADX_MINIMO

                and

                candle["Close"] >
                candle["EMA21"]

                and

                candle["EMA21_ASC"]

                and

                candle["Financeiro"] >
                VOLUME_MINIMO

                and

                candle["AMPLITUDE"] < 6

                and

                semana["SEM_K_MAIOR"]

            )

            if not filtro:
                continue

            entrada = candle["High"]

            gain = (
                entrada *
                (1 + GAIN_FIXO)
            )

            loss = (
                entrada *
                (1 - LOSS_FIXO)
            )

            total += 1

            futuro = diario.iloc[
                i + 1:i + 31
            ]

            resultado = None

            entrada_acionada = False

            for _, prox in futuro.iterrows():

                # =============================================
                # ENTRADA ACIONADA
                # =============================================

                if not entrada_acionada:

                    if prox["High"] >= entrada:

                        entrada_acionada = True

                    else:

                        continue

                # =============================================
                # GAIN
                # =============================================

                if prox["High"] >= gain:

                    resultado = "GAIN"

                    break

                # =============================================
                # LOSS
                # =============================================

                if prox["Low"] <= loss:

                    resultado = "LOSS"

                    break

            # =============================================
            # EXPIRAÇÃO
            # =============================================

            if resultado is None:

                fechamento_final = (
                    futuro.iloc[-1]["Close"]
                )

                if fechamento_final >= entrada:

                    resultado = "GAIN"

                else:

                    resultado = "LOSS"

            # =============================================
            # CONTABILIZAÇÃO
            # =============================================

            if resultado == "GAIN":

                gains += 1

            else:

                losses += 1

        except:

            continue

    if total == 0:

        return {

            "winrate": 0,

            "expectancia": 0,

            "gains": 0,

            "losses": 0,

            "sinais": 0
        }

    winrate = round(
        (gains / total) * 100,
        1
    )

    expectancia = calcular_expectancia(
        winrate
    )

    return {

        "winrate": winrate,

        "expectancia": expectancia,

        "gains": gains,

        "losses": losses,

        "sinais": total
    }

# =========================================================
# SCANNER
# =========================================================

def executar_scanner():

    aprovados = []

    barra = st.progress(0)

    total_ativos = len(ATIVOS)

    for i, ativo in enumerate(ATIVOS):

        barra.progress(
            (i + 1) / total_ativos
        )

        try:

            diario = baixar_dados(
                ativo,
                intervalo="1d"
            )

            semanal = baixar_dados(
                ativo,
                intervalo="1wk"
            )

            if diario is None or semanal is None:
                continue

            diario = calcular_indicadores(diario)

            semanal = calcular_indicadores(semanal)

            d = diario.iloc[-2]

            s = semanal.iloc[-2]

            # =================================================
            # FILTROS ATUAIS
            # =================================================

            filtros = (

                d["K"] > d["D"]

                and

                d["DI_POS"] > d["DI_NEG"]

                and

                d["ADX"] > ADX_MINIMO

                and

                d["Close"] > d["EMA21"]

                and

                d["EMA21_ASC"]

                and

                d["Financeiro"] >
                VOLUME_MINIMO

                and

                d["AMPLITUDE"] < 6

                and

                s["K"] > s["D"]

            )

            if not filtros:
                continue

            estatistica = calcular_probabilidade(
                diario,
                semanal
            )

            entrada = round(
                float(d["High"]),
                2
            )

            gain = round(
                entrada *
                (1 + GAIN_FIXO),
                2
            )

            loss = round(
                entrada *
                (1 - LOSS_FIXO),
                2
            )

            aprovados.append({

                "Ativo": ativo,

                "Entrada": entrada,

                "Gain": gain,

                "Loss": loss,

                "Win Rate": (
                    f"{estatistica['winrate']}%"
                ),

                "Expectância": (
                    f"{estatistica['expectancia']}%"
                ),

                "ADX": round(
                    float(d["ADX"]),
                    1
                ),

                "Financeiro": round(
                    float(d["Financeiro"] / 1_000_000),
                    1
                ),

                "%K Diário": round(
                    float(d["K"]),
                    1
                ),

                "%D Diário": round(
                    float(d["D"]),
                    1
                ),

                "%K Semanal": round(
                    float(s["K"]),
                    1
                ),

                "%D Semanal": round(
                    float(s["D"]),
                    1
                ),

                "Sinais": (
                    estatistica["sinais"]
                ),

                "Gains": (
                    estatistica["gains"]
                ),

                "Losses": (
                    estatistica["losses"]
                ),

                "Score": (
                    estatistica["expectancia"]
                )
            })

        except:

            continue

    barra.empty()

    aprovados = pd.DataFrame(aprovados)

    if not aprovados.empty:

        aprovados = aprovados.sort_values(
            by="Score",
            ascending=False
        )

    return aprovados

# =========================================================
# HEADER
# =========================================================

st.title(
    "📈 Scanner Quantitativo B3"
)

st.markdown("""

### Setup Utilizado

- Estocástico Diário 14-3-3
- DMI Diário
- ADX > 20
- Fechamento acima EMA21
- EMA21 ascendente
- Volume financeiro > 20 milhões
- Candle não esticado
- Estocástico semanal alinhado
- Entrada acima da máxima
- Gain fixo 5%
- Loss fixo 4%

""")

st.markdown("---")

# =========================================================
# EXECUÇÃO
# =========================================================

if st.button("▶ Executar Scanner"):

    aprovados = executar_scanner()

    st.subheader(
        "✅ Ativos Aprovados"
    )

    if aprovados.empty:

        st.warning(
            "Nenhum ativo passou."
        )

    else:

        st.dataframe(
            aprovados.drop(
                columns=["Score"]
            ),
            use_container_width=True,
            hide_index=True,
            height=700
        )

        fig = px.scatter(

            aprovados,

            x="ADX",

            y="Score",

            size="Sinais",

            hover_data=["Ativo"],

            title="Mapa Quantitativo"

        )

        fig.update_layout(
            template="plotly_dark",
            height=700
        )

        st.plotly_chart(
            fig,
            use_container_width=True
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
