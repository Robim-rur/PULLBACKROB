import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px

from ta.trend import ADXIndicator
from ta.momentum import StochasticOscillator

from datetime import datetime

# =========================================================
# CONFIGURAÇÃO
# =========================================================

st.set_page_config(
    page_title="Scanner Quantitativo Profissional",
    page_icon="📈",
    layout="wide"
)

# =========================================================
# PARÂMETROS
# =========================================================

GAIN_PERCENTUAL = 0.07
LOSS_PERCENTUAL = 0.05

ADX_MINIMO = 17

LOOKBACK_CRUZAMENTO = 3

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
# ATIVOS
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
# CRUZAMENTO RECENTE
# =========================================================

def cruzamento_recente(df):

    ultimos = df.tail(LOOKBACK_CRUZAMENTO + 1)

    for i in range(1, len(ultimos)):

        anterior = ultimos.iloc[i - 1]

        atual = ultimos.iloc[i]

        cruzou = (

            anterior["K"] <= anterior["D"]

            and

            atual["K"] > atual["D"]

        )

        if cruzou:
            return True

    return False

# =========================================================
# PROBABILIDADE HISTÓRICA
# =========================================================

def calcular_probabilidade_historica(
    diario,
    semanal
):

    total_sinais = 0

    gains = 0

    losses = 0

    semanal["SEM_K_MAIOR"] = (
        semanal["K"] >
        semanal["D"]
    )

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

            filtro_diario = (

                candle["K"] >
                candle["D"]

                and

                candle["DI_POS"] >
                candle["DI_NEG"]

                and

                candle["ADX"] > ADX_MINIMO

            )

            filtro_semanal = (
                semana["SEM_K_MAIOR"]
            )

            if not (
                filtro_diario
                and filtro_semanal
            ):
                continue

            total_sinais += 1

            entrada = candle["Close"]

            gain = (
                entrada *
                (1 + GAIN_PERCENTUAL)
            )

            loss = (
                entrada *
                (1 - LOSS_PERCENTUAL)
            )

            futuro = diario.iloc[
                i + 1:i + 31
            ]

            resultado = None

            for _, prox in futuro.iterrows():

                maximo = prox["High"]

                minimo = prox["Low"]

                if maximo >= gain:

                    resultado = "GAIN"

                    break

                if minimo <= loss:

                    resultado = "LOSS"

                    break

            if resultado == "GAIN":
                gains += 1

            elif resultado == "LOSS":
                losses += 1

        except:
            continue

    if total_sinais == 0:

        return {
            "probabilidade": 0,
            "sinais": 0,
            "gains": 0,
            "losses": 0
        }

    probabilidade = round(
        (gains / total_sinais) * 100,
        1
    )

    return {

        "probabilidade": probabilidade,

        "sinais": total_sinais,

        "gains": gains,

        "losses": losses
    }

# =========================================================
# EXECUTAR SCANNER
# =========================================================

def executar_scanner():

    aprovados = []

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

            filtro_cruzamento = (
                cruzamento_recente(diario)
            )

            # =================================================
            # MOTIVOS
            # =================================================

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

            if not filtro_cruzamento:
                motivos.append(
                    "Sem cruzamento recente"
                )

            # =================================================
            # APROVADO
            # =================================================

            if (
                filtro_estoc_diario
                and
                filtro_dmi
                and
                filtro_adx
                and
                filtro_estoc_semanal
                and
                filtro_cruzamento
            ):

                estatistica = (
                    calcular_probabilidade_historica(
                        diario,
                        semanal
                    )
                )

                entrada = round(
                    float(d["Close"]),
                    2
                )

                gain = round(
                    entrada *
                    (1 + GAIN_PERCENTUAL),
                    2
                )

                loss = round(
                    entrada *
                    (1 - LOSS_PERCENTUAL),
                    2
                )

                risco = entrada - loss

                retorno = gain - entrada

                rr = round(
                    retorno / risco,
                    2
                )

                aprovados.append({

                    "Ativo": ativo,

                    "Entrada": entrada,

                    "Gain": gain,

                    "Loss": loss,

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

                    "Probabilidade": (
                        f"{estatistica['probabilidade']}%"
                    ),

                    "Sinais Históricos": (
                        estatistica["sinais"]
                    ),

                    "Gains": (
                        estatistica["gains"]
                    ),

                    "Losses": (
                        estatistica["losses"]
                    ),

                    "Score": (
                        estatistica["probabilidade"]
                    )
                })

            else:

                reprovados.append({

                    "Ativo": ativo,

                    "Motivos": ", ".join(
                        motivos
                    )
                })

        except Exception as erro:

            reprovados.append({

                "Ativo": ativo,

                "Motivos": str(erro)
            })

            continue

    progresso.empty()

    aprovados_df = pd.DataFrame(aprovados)

    reprovados_df = pd.DataFrame(reprovados)

    if not aprovados_df.empty:

        aprovados_df = (
            aprovados_df
            .sort_values(
                by="Score",
                ascending=False
            )
        )

    return aprovados_df, reprovados_df

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title(
    "📈 Scanner Quantitativo"
)

st.sidebar.markdown(
    f"""
### Setup Operacional

✔ Estocástico Diário  
✔ DMI Diário  
✔ ADX > {ADX_MINIMO}  
✔ Estocástico Semanal  
✔ Cruzamento Recente  

### Gestão

🎯 Gain: {int(GAIN_PERCENTUAL * 100)}%  
🛑 Loss: {int(LOSS_PERCENTUAL * 100)}%
"""
)

# =========================================================
# HEADER
# =========================================================

st.title(
    "📈 Scanner Quantitativo Profissional"
)

st.markdown(
    """
Scanner quantitativo baseado em:

- Estocástico 14-3-3
- DMI
- ADX
- Confirmação semanal
- Cruzamento recente
- Probabilidade histórica
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
                "Probabilidade Média",
                f"{round(aprovados['Score'].mean(),1)}%"
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
                "R/R Médio",
                round(
                    aprovados["R/R"].mean(),
                    2
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

        fig = px.scatter(

            aprovados,

            x="ADX",

            y="Score",

            size="Sinais Históricos",

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

        height=500
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
