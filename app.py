import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px

from ta.trend import ADXIndicator
from ta.momentum import StochasticOscillator

from datetime import datetime

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(
    page_title="Scanner Quantitativo Inteligente",
    page_icon="📈",
    layout="wide"
)

# =========================================================
# PARÂMETROS
# =========================================================

LOSS_FIXO = 0.05

GAINS_TESTADOS = [
    0.055,
    0.06,
    0.065,
    0.07,
    0.08,
    0.09,
    0.10
]

ADX_MINIMO = 17

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

    "PETR4.SA",
    "VALE3.SA",
    "BBAS3.SA",
    "ITUB4.SA",
    "WEGE3.SA",
    "PRIO3.SA",
    "RENT3.SA",
    "BBDC4.SA",
    "GGBR4.SA",

    "BOVA11.SA",
    "IVVB11.SA",
    "SMAL11.SA",
    "HASH11.SA",

    "HGLG11.SA",
    "MXRF11.SA",
    "KNRI11.SA",
    "AUVP11.SA",

    "AAPL34.SA",
    "GOGL34.SA",
    "MSFT34.SA",
    "TSLA34.SA"
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
    # LIMPEZA
    # =====================================================

    df.replace(
        [np.inf, -np.inf],
        np.nan,
        inplace=True
    )

    df.dropna(inplace=True)

    return df

# =========================================================
# EXPECTÂNCIA
# =========================================================

def calcular_expectancia(
    winrate,
    gain,
    loss
):

    pw = winrate / 100

    pl = 1 - pw

    expectativa = (
        (pw * gain)
        -
        (pl * loss)
    )

    return round(
        expectativa,
        4
    )

# =========================================================
# OTIMIZADOR
# =========================================================

def otimizar_gain(
    diario,
    semanal
):

    melhor_resultado = None

    semanal["SEM_K_MAIOR"] = (
        semanal["K"] >
        semanal["D"]
    )

    for gain_testado in GAINS_TESTADOS:

        total_sinais = 0

        gains = 0

        losses = 0

        # =================================================
        # LOOP HISTÓRICO
        # =================================================

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

                # =============================================
                # FILTROS
                # =============================================

                filtro = (

                    candle["K"] >
                    candle["D"]

                    and

                    candle["DI_POS"] >
                    candle["DI_NEG"]

                    and

                    candle["ADX"] > ADX_MINIMO

                    and

                    semana["SEM_K_MAIOR"]

                )

                if not filtro:
                    continue

                total_sinais += 1

                entrada = candle["Close"]

                gain = (
                    entrada *
                    (1 + gain_testado)
                )

                loss = (
                    entrada *
                    (1 - LOSS_FIXO)
                )

                futuro = diario.iloc[
                    i + 1:i + 31
                ]

                resultado = None

                for _, prox in futuro.iterrows():

                    if prox["High"] >= gain:

                        resultado = "GAIN"

                        break

                    if prox["Low"] <= loss:

                        resultado = "LOSS"

                        break

                if resultado == "GAIN":
                    gains += 1

                elif resultado == "LOSS":
                    losses += 1

            except:
                continue

        # =================================================
        # ESTATÍSTICAS
        # =================================================

        if total_sinais == 0:
            continue

        winrate = (
            gains / total_sinais
        ) * 100

        expectativa = calcular_expectancia(
            winrate,
            gain_testado,
            LOSS_FIXO
        )

        # =================================================
        # SCORE FINAL
        # =================================================

        score = (
            expectativa * 100
        )

        # =================================================
        # MELHOR RESULTADO
        # =================================================

        if (
            melhor_resultado is None
            or
            score > melhor_resultado["score"]
        ):

            melhor_resultado = {

                "gain": gain_testado,

                "winrate": round(
                    winrate,
                    1
                ),

                "expectativa": expectativa,

                "score": round(
                    score,
                    2
                ),

                "sinais": total_sinais,

                "gains": gains,

                "losses": losses
            }

    return melhor_resultado

# =========================================================
# EXECUTAR SCANNER
# =========================================================

def executar_scanner():

    resultados = []

    reprovados = []

    progresso = st.progress(0)

    total = len(ATIVOS)

    for i, ativo in enumerate(ATIVOS):

        progresso.progress(
            (i + 1) / total
        )

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
            # CANDLE FECHADO
            # =================================================

            d = diario.iloc[-2]

            s = semanal.iloc[-2]

            # =================================================
            # FILTROS
            # =================================================

            filtro_estoc_diario = (
                d["K"] > d["D"]
            )

            filtro_dmi = (
                d["DI_POS"] > d["DI_NEG"]
            )

            filtro_adx = (
                d["ADX"] > ADX_MINIMO
            )

            filtro_estoc_semanal = (
                s["K"] > s["D"]
            )

            if not (

                filtro_estoc_diario

                and

                filtro_dmi

                and

                filtro_adx

                and

                filtro_estoc_semanal

            ):

                motivos = []

                if not filtro_estoc_diario:
                    motivos.append(
                        "K diário abaixo D"
                    )

                if not filtro_dmi:
                    motivos.append(
                        "DI+ abaixo DI-"
                    )

                if not filtro_adx:
                    motivos.append(
                        f"ADX abaixo {ADX_MINIMO}"
                    )

                if not filtro_estoc_semanal:
                    motivos.append(
                        "K semanal abaixo D"
                    )

                reprovados.append({

                    "Ativo": ativo,

                    "Motivos": ", ".join(
                        motivos
                    )
                })

                continue

            # =================================================
            # OTIMIZAÇÃO
            # =================================================

            melhor = otimizar_gain(
                diario,
                semanal
            )

            if melhor is None:
                continue

            # =================================================
            # PREÇOS
            # =================================================

            entrada = round(
                float(d["Close"]),
                2
            )

            gain_preco = round(
                entrada *
                (1 + melhor["gain"]),
                2
            )

            loss_preco = round(
                entrada *
                (1 - LOSS_FIXO),
                2
            )

            rr = round(
                melhor["gain"] / LOSS_FIXO,
                2
            )

            resultados.append({

                "Ativo": ativo,

                "Entrada": entrada,

                "Gain %": (
                    f"{round(melhor['gain'] * 100,1)}%"
                ),

                "Gain Preço": gain_preco,

                "Loss %": (
                    f"{int(LOSS_FIXO * 100)}%"
                ),

                "Loss Preço": loss_preco,

                "Win Rate": (
                    f"{melhor['winrate']}%"
                ),

                "Expectância": (
                    melhor["expectativa"]
                ),

                "R/R": rr,

                "ADX": round(
                    float(d["ADX"]),
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
                    melhor["sinais"]
                ),

                "Gains": (
                    melhor["gains"]
                ),

                "Losses": (
                    melhor["losses"]
                ),

                "Score": (
                    melhor["score"]
                )
            })

        except Exception as erro:

            reprovados.append({

                "Ativo": ativo,

                "Motivos": str(erro)
            })

    progresso.empty()

    aprovados = pd.DataFrame(resultados)

    reprovados = pd.DataFrame(reprovados)

    if not aprovados.empty:

        aprovados = aprovados.sort_values(
            by="Score",
            ascending=False
        )

    return aprovados, reprovados

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title(
    "📈 Scanner Quantitativo"
)

st.sidebar.markdown(
    f"""
### Setup

✔ Estocástico Diário  
✔ DMI Diário  
✔ ADX > {ADX_MINIMO}  
✔ Estocástico Semanal  

### Gestão

🛑 Loss Fixo:
{int(LOSS_FIXO * 100)}%

🎯 Gain Dinâmico:
otimizado automaticamente
"""
)

# =========================================================
# HEADER
# =========================================================

st.title(
    "📈 Scanner Quantitativo Inteligente"
)

st.markdown(
    """
O sistema procura:

- melhor gain histórico;
- maior probabilidade;
- maior expectância;
- melhor equilíbrio matemático;
- gain atingido antes do stop.
"""
)

st.markdown("---")

# =========================================================
# EXECUTAR
# =========================================================

if st.button("▶ Executar Scanner"):

    aprovados, reprovados = executar_scanner()

    # =====================================================
    # APROVADOS
    # =====================================================

    st.subheader("✅ Ativos Aprovados")

    if aprovados.empty:

        st.warning(
            "Nenhum ativo passou."
        )

    else:

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Ativos",
                len(aprovados)
            )

        with col2:

            st.metric(
                "Win Rate Médio",
                f"{round(aprovados['Score'].mean(),1)}"
            )

        with col3:

            st.metric(
                "ADX Médio",
                round(
                    aprovados["ADX"].mean(),
                    1
                )
            )

        with col4:

            st.metric(
                "Expectância Média",
                round(
                    aprovados["Expectância"].mean(),
                    3
                )
            )

        st.dataframe(

            aprovados.drop(
                columns=["Score"]
            ),

            use_container_width=True,

            hide_index=True,

            height=700
        )

        # =================================================
        # GRÁFICO
        # =================================================

        fig = px.scatter(

            aprovados,

            x="ADX",

            y="Expectância",

            size="Sinais",

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

    # =====================================================
    # REPROVADOS
    # =====================================================

    st.markdown("---")

    st.subheader(
        "❌ Ativos Reprovados"
    )

    st.dataframe(

        reprovados,

        use_container_width=True,

        hide_index=True,

        height=450
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
