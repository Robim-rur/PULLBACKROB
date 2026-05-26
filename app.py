import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px

from ta.trend import ADXIndicator
from ta.volatility import AverageTrueRange
from ta.momentum import StochasticOscillator

from datetime import datetime

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(
    page_title="Scanner Quantitativo Swing Trade",
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

    # =====================================================
    # AÇÕES
    # =====================================================

    "PETR4.SA",
    "VALE3.SA",
    "BBAS3.SA",
    "ITUB4.SA",
    "WEGE3.SA",
    "PRIO3.SA",
    "RENT3.SA",
    "BBDC4.SA",

    # =====================================================
    # ETFs
    # =====================================================

    "BOVA11.SA",
    "IVVB11.SA",
    "SMAL11.SA",
    "HASH11.SA",

    # =====================================================
    # FIIs
    # =====================================================

    "HGLG11.SA",
    "MXRF11.SA",
    "KNRI11.SA",
    "AUVP11.SA",

    # =====================================================
    # BDRs
    # =====================================================

    "AAPL34.SA",
    "GOGL34.SA",
    "MSFT34.SA",
    "TSLA34.SA"
]

# =========================================================
# DOWNLOAD DOS DADOS
# =========================================================

@st.cache_data(ttl=3600)
def baixar_dados(ativo, periodo="2y", intervalo="1d"):

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

        # =====================================================
        # REMOVE MULTIINDEX DO YFINANCE
        # =====================================================

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # =====================================================
        # GARANTE NUMÉRICO
        # =====================================================

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

        # =====================================================
        # GARANTE MÍNIMO DE DADOS
        # =====================================================

        if len(df) < 50:
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
    # ESTOCÁSTICO 14-3-3
    # =====================================================

    estocastico = StochasticOscillator(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=14,
        smooth_window=3
    )

    df["K"] = estocastico.stoch()

    # =====================================================
    # %D
    # =====================================================

    df["D"] = (
        df["K"]
        .rolling(3)
        .mean()
    )

    # =====================================================
    # DMI / ADX
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
    # ATR
    # =====================================================

    atr = AverageTrueRange(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=14
    )

    df["ATR"] = atr.average_true_range()

    # =====================================================
    # REMOVE NAN
    # =====================================================

    df.dropna(inplace=True)

    return df

# =========================================================
# SCORE ESTATÍSTICO
# =========================================================

def calcular_score(
    adx,
    di_pos,
    di_neg,
    k_diario,
    d_diario,
    k_semanal,
    d_semanal
):

    score = 50

    # =====================================================
    # ADX
    # =====================================================

    if adx > 18:
        score += 10

    if adx > 22:
        score += 10

    if adx > 30:
        score += 10

    # =====================================================
    # FORÇA DMI
    # =====================================================

    diferenca_di = di_pos - di_neg

    if diferenca_di > 2:
        score += 5

    if diferenca_di > 5:
        score += 5

    if diferenca_di > 10:
        score += 10

    # =====================================================
    # ESTOCÁSTICO DIÁRIO
    # =====================================================

    diferenca_diario = k_diario - d_diario

    if diferenca_diario > 1:
        score += 5

    if diferenca_diario > 3:
        score += 5

    # =====================================================
    # ESTOCÁSTICO SEMANAL
    # =====================================================

    diferenca_semanal = k_semanal - d_semanal

    if diferenca_semanal > 1:
        score += 5

    if diferenca_semanal > 3:
        score += 5

    return min(round(score), 100)

# =========================================================
# EXECUTAR SCANNER
# =========================================================

def executar_scanner():

    resultados = []

    progresso = st.progress(0)

    total = len(ATIVOS)

    for i, ativo in enumerate(ATIVOS):

        progresso.progress((i + 1) / total)

        try:

            # =================================================
            # DIÁRIO
            # =================================================

            diario = baixar_dados(
                ativo,
                intervalo="1d"
            )

            if diario is None:
                continue

            diario = calcular_indicadores(diario)

            if diario.empty:
                continue

            # =================================================
            # SEMANAL
            # =================================================

            semanal = baixar_dados(
                ativo,
                intervalo="1wk"
            )

            if semanal is None:
                continue

            semanal = calcular_indicadores(semanal)

            if semanal.empty:
                continue

            # =================================================
            # ÚLTIMAS LINHAS
            # =================================================

            d = diario.iloc[-1]

            s = semanal.iloc[-1]

            # =================================================
            # FILTROS DIÁRIOS
            # =================================================

            filtro_estoc_diario = (
                d["K"] > d["D"]
            )

            filtro_dmi = (
                d["DI_POS"] > d["DI_NEG"]
            )

            filtro_adx = (
                d["ADX"] > 18
            )

            # =================================================
            # FILTRO SEMANAL
            # =================================================

            filtro_estoc_semanal = (
                s["K"] > s["D"]
            )

            # =================================================
            # FILTROS FINAIS
            # =================================================

            if (
                filtro_estoc_diario
                and filtro_dmi
                and filtro_adx
                and filtro_estoc_semanal
            ):

                entrada = round(
                    float(d["Close"]),
                    2
                )

                atr = round(
                    float(d["ATR"]),
                    2
                )

                # =============================================
                # GAIN E LOSS ATR
                # =============================================

                loss = round(
                    entrada - (atr * 1.5),
                    2
                )

                gain = round(
                    entrada + (atr * 3),
                    2
                )

                # =============================================
                # RISCO RETORNO
                # =============================================

                risco = entrada - loss

                retorno = gain - entrada

                rr = round(
                    retorno / risco,
                    2
                )

                # =============================================
                # SCORE
                # =============================================

                score = calcular_score(
                    d["ADX"],
                    d["DI_POS"],
                    d["DI_NEG"],
                    d["K"],
                    d["D"],
                    s["K"],
                    s["D"]
                )

                resultados.append({

                    "Ativo": ativo,

                    "Entrada": entrada,

                    "Gain": gain,

                    "Loss": loss,

                    "ATR": atr,

                    "ADX": round(
                        float(d["ADX"]),
                        1
                    ),

                    "DI+": round(
                        float(d["DI_POS"]),
                        1
                    ),

                    "DI-": round(
                        float(d["DI_NEG"]),
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

                    "R/R": rr,

                    "Probabilidade": f"{score}%",

                    "Score": score
                })

        except Exception as erro:

            print(f"Erro em {ativo}: {erro}")

            continue

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

st.sidebar.title(
    "📈 Scanner Quantitativo"
)

st.sidebar.markdown(
    """
### Filtros:

✔ Estocástico Diário  
✔ DMI Diário  
✔ ADX > 18  
✔ Estocástico Semanal  
✔ Gain/Loss ATR  
"""
)

# =========================================================
# HEADER
# =========================================================

st.title(
    "📈 Scanner Quantitativo Swing Trade"
)

st.markdown(
    """
Scanner quantitativo baseado em:

- Estocástico 14-3-3
- DMI
- ADX
- Confirmação semanal
- ATR 14
"""
)

st.markdown("---")

# =========================================================
# EXECUTAR
# =========================================================

if st.button("▶ Executar Scanner"):

    resultado = executar_scanner()

    if resultado.empty:

        st.warning(
            "Nenhum ativo passou pelos filtros hoje."
        )

    else:

        # =================================================
        # MÉTRICAS
        # =================================================

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Ativos",
                len(resultado)
            )

        with col2:
            st.metric(
                "Score Médio",
                round(
                    resultado["Score"].mean(),
                    1
                )
            )

        with col3:
            st.metric(
                "ADX Médio",
                round(
                    resultado["ADX"].mean(),
                    1
                )
            )

        with col4:
            st.metric(
                "R/R Médio",
                round(
                    resultado["R/R"].mean(),
                    2
                )
            )

        st.markdown("---")

        # =================================================
        # TABELA
        # =================================================

        st.dataframe(

            resultado.drop(
                columns=["Score"]
            ),

            use_container_width=True,

            hide_index=True,

            height=750
        )

        st.markdown("---")

        # =================================================
        # GRÁFICO
        # =================================================

        fig = px.scatter(

            resultado,

            x="ADX",

            y="Score",

            size="ATR",

            color="R/R",

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
