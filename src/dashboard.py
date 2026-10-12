
import os
from pathlib import Path

import plotly.express as px
import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=os.getenv("POSTGRES_PORT"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB"),
    )


# Configuração geral do dashboard
st.title("Dashboard de Temperatura IoT")
st.write("Projeto de análise de leituras de temperatura.")

st.subheader("Filtros")

col_data_inicio, col_data_fim = st.columns(2)

with col_data_inicio:
    data_inicio = st.date_input(
        "Data inicial",
        value=pd.to_datetime("2018-07-28").date(),
        min_value=pd.to_datetime("2018-07-28").date(),
        max_value=pd.to_datetime("2018-12-08").date(),
    )

with col_data_fim:
    data_fim = st.date_input(
        "Data final",
        value=pd.to_datetime("2018-12-08").date(),
        min_value=pd.to_datetime("2018-07-28").date(),
        max_value=pd.to_datetime("2018-12-08").date(),
    )

if data_inicio > data_fim:
    st.error("A data inicial não pode ser posterior à data final.")
    st.stop()


connection = None

try:
    connection = get_connection()

    data_fim_exclusiva = (
        pd.Timestamp(data_fim) + pd.Timedelta(days=1)
    )

    # Indicadores gerais
    indicadores = pd.read_sql_query(
        """
        SELECT
            COUNT(*) AS total_leituras,
            AVG(temperature) AS temperatura_media,
            MAX(temperature) AS temperatura_maxima
        FROM temperature_readings
        WHERE reading_time >= %s
          AND reading_time < %s
        """,
        connection,
        params=(data_inicio, data_fim_exclusiva),
    )

    total = int(indicadores.loc[0, "total_leituras"])
    media = indicadores.loc[0, "temperatura_media"]
    maxima = indicadores.loc[0, "temperatura_maxima"]

    st.subheader("Indicadores gerais")
    st.caption("Resumo das leituras no período selecionado.")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total de leituras",
        f"{total:,}".replace(",", "."),
    )

    if total > 0:
        col2.metric(
            "Temperatura média",
            f"{media:.2f} °C",
        )
        col3.metric(
            "Temperatura máxima",
            f"{int(maxima)} °C",
        )
    else:
        col2.metric("Temperatura média", "Sem dados")
        col3.metric("Temperatura máxima", "Sem dados")
        st.info("Não existem leituras para o período selecionado.")

 # Tabela e gráfico de temperatura diária
    df = pd.read_sql_query(
        """
        SELECT *
        FROM vw_temperatura_diaria
        WHERE dia >= %s
          AND dia <= %s
        ORDER BY dia
        """,
        connection,
        params=(data_inicio, data_fim),
    )

    st.subheader("Temperatura Diária")
    st.caption(
        "Tabela com o total de leituras e a temperatura média de cada dia."
    )

    if not df.empty:
        st.dataframe(df, use_container_width=True)

        st.subheader("Variação da Temperatura Média por Dia")
        st.caption("Evolução da temperatura média ao longo dos dias.")

        st.line_chart(
            df,
            x="dia",
            y="temperatura_media",
        )
    else:
        st.info("Não há dados diários para exibir neste período.")


    # Gráfico contagem de leituras por hora
    df_leituras_hora = pd.read_sql_query(
        """
        SELECT
            EXTRACT(HOUR FROM reading_time)::INTEGER AS hora,
            COUNT(*) AS contagem
        FROM temperature_readings
        WHERE reading_time >= %s
          AND reading_time < %s
        GROUP BY EXTRACT(HOUR FROM reading_time)
        ORDER BY hora
        """,
        connection,
        params=(data_inicio, data_fim_exclusiva),
    )

    st.subheader("Leituras por Hora do Dia")
    st.caption(
        "Mostra a quantidade de leituras registradas em cada hora "
        "do dia no período selecionado."
    )

    if not df_leituras_hora.empty:
        fig2 = px.line(
            df_leituras_hora,
            x="hora",
            y="contagem",
            markers=True,
            labels={
                "hora": "Hora do dia",
                "contagem": "Quantidade de leituras",
            },
        )
        fig2.update_xaxes(tickmode="linear", dtick=1)
        fig2.update_layout(title=None)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Não há leituras para o período selecionado.")


    # Gráfico temperaturas máximas e mínimas por dia
    df_temp_max_min = pd.read_sql_query(
        """
        SELECT
            DATE(reading_time) AS data,
            MAX(temperature) AS temp_max,
            MIN(temperature) AS temp_min
        FROM temperature_readings
        WHERE reading_time >= %s
          AND reading_time < %s
        GROUP BY DATE(reading_time)
        ORDER BY data
        """,
        connection,
        params=(data_inicio, data_fim_exclusiva),
    )

    st.subheader("Temperaturas Máximas e Mínimas por Dia")
    st.caption(
        "Compara a maior e a menor temperatura registrada em cada dia."
    )

    if not df_temp_max_min.empty:
        fig3 = px.line(
            df_temp_max_min,
            x="data",
            y=["temp_max", "temp_min"],
            markers=True,
            labels={
                "data": "Data",
                "value": "Temperatura (°C)",
                "variable": "Tipo de temperatura",
                "temp_max": "Temperatura máxima",
                "temp_min": "Temperatura mínima",
            },
        )
        fig3.update_layout(title=None)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Não há dados para exibir no período selecionado.")

    # Gráfico de temperatura por localização ao longo dos dias
    df_localizacao = pd.read_sql_query(
        """
        SELECT *
        FROM vw_temperatura_diaria_localizacao
        WHERE dia >= %s
          AND dia <= %s
        ORDER BY dia
        """,
        connection,
        params=(data_inicio, data_fim),
    )

    st.subheader("Temperatura por Localização ao Longo dos Dias")
    st.caption(
        "Permite comparar a temperatura média diária em ambientes "
        "internos e externos."
    )

    tipo_localizacao = st.selectbox(
        "Selecione a localização",
        ["Todas", "In", "Out"],
    )

    if tipo_localizacao != "Todas":
        df_localizacao = df_localizacao[
            df_localizacao["location_type"] == tipo_localizacao
        ]

    if not df_localizacao.empty:
        st.line_chart(
            df_localizacao,
            x="dia",
            y="temperatura_media",
            color="location_type",
        )
    else:
        st.info(
            "Não há dados para a localização e o período selecionados."
        )

# Gráfico média de temperatura por localização
    df_avg_temp = pd.read_sql_query(
        """
        SELECT
            location_type,
            ROUND(AVG(temperature), 2) AS avg_temp
        FROM temperature_readings
        WHERE reading_time >= %s
          AND reading_time < %s
        GROUP BY location_type
        ORDER BY location_type
        """,
        connection,
        params=(data_inicio, data_fim_exclusiva),
    )

    st.subheader("Média de Temperatura por Localização")
    st.caption(
        "Compara a temperatura média dos ambientes internos (In) "
        "e externos (Out)."
    )

    if not df_avg_temp.empty:
        fig1 = px.bar(
            df_avg_temp,
            x="location_type",
            y="avg_temp",
            labels={
                "location_type": "Tipo de localização",
                "avg_temp": "Temperatura média (°C)",
            },
        )
        fig1.update_layout(title=None)
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("Não há dados para calcular a média no período selecionado.")

except Exception as error:
    st.error("Ocorreu um erro ao consultar o PostgreSQL.")
    st.exception(error)

finally:
    if connection is not None:
        connection.close()
