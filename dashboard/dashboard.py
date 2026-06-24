import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import date
from modelo import preparar_dados_temporais, treinar_e_prever

st.set_page_config(page_title="Dashboard E-commerce - AV2", layout="wide")

import os

API_URL = os.getenv(
    "API_URL",
    "http://localhost:8000"
)

# Função auxiliar para buscar dados de forma segura
def buscar_dados_api(endpoint, params=None):
    try:
        url = f"{API_URL}{endpoint}"
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

st.title("🛒 Dashboard de Vendas")


# FILTROS (Consumindo dados dinâmicos da API)
dados_brutos = buscar_dados_api("/dados")

if dados_brutos:
    df_base = pd.DataFrame(dados_brutos)
    
    # Criando os seletores na tela
    df_base["data"] = pd.to_datetime(df_base["data"])

    col_f1, col_f2 = st.columns(2)

    with col_f1:
        estado = st.selectbox(
            "Estado",
            ["Todos"] + sorted(df_base["estado"].unique())
        )

    with col_f2:
        categoria_selecionada = st.selectbox(
            "Categoria",
            ["Todas"] + sorted(df_base["categoria"].unique())
        )

    periodo = st.date_input(
        "Período de análise",
        value=(
            df_base["data"].min().date(),
            df_base["data"].max().date()
        ),
        min_value=date(2024, 1, 1),
        max_value=date(2026, 12, 31)
    )

    # Montando os query params para enviar para a API intermediária
    params_api = {}
    if categoria_selecionada != "Todas":
        params_api["categoria"] = categoria_selecionada
    if estado != "Todos":
        params_api["estado"] = estado
    if len(periodo) == 2:
        params_api["data_inicio"] = str(periodo[0])
        params_api["data_fim"] = str(periodo[1])

    # 1. KPIs (Consumindo a rota /resumo)
    resumo_json = buscar_dados_api("/resumo", params=params_api)

    if resumo_json:
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Faturamento Total", f"R$ {resumo_json['faturamento_total']:,.2f}")
        col2.metric("📦 Total de Pedidos", f"{resumo_json['total_pedidos']}")
        col3.metric("🧾 Ticket Médio", f"R$ {resumo_json['ticket_medio']:,.2f}")
    
    st.divider()

   
    dados_filtrados = buscar_dados_api("/dados", params=params_api)
    if dados_filtrados:
        df_filtrado = pd.DataFrame(dados_filtrados)
        
        if not df_filtrado.empty:
            
            # GRÁFICO 1 - CATEGORIAS
            st.subheader("💰 Faturamento por Categoria")
            df_cat = df_filtrado.groupby("categoria")["valor_total"].sum().reset_index()
            df_cat.columns = ["categoria", "faturamento"]
            
            st.plotly_chart(px.bar(
                df_cat, x="categoria", y="faturamento", color="categoria",
                labels={"categoria": "Categoria", "faturamento": "Faturamento (R$)"}
            ), use_container_width=True)

            # GRÁFICO 2 - PRODUTOS (Ranking)
            st.subheader("📋 Ranking de Produtos")
            df_prod = df_filtrado.groupby("produto")["quantidade"].sum().reset_index()
            df_prod = df_prod.sort_values(by="quantidade", ascending=False).head(10).reset_index(drop=True)
            df_prod.index += 1
            df_prod.columns = ["Produto", "Unidades Vendidas"]
            st.dataframe(df_prod, use_container_width=True)

            # GRÁFICOS 3 E 4 - EVOLUÇÃO NO TEMPO
            df_filtrado["mes"] = df_filtrado["data"].str.slice(0, 7)
            
            df_receita_mes = df_filtrado.groupby("mes")["valor_total"].sum().reset_index()
            df_receita_mes.columns = ["mes", "receita"]
            
            st.subheader("📈 Receita Mensal ao Longo do Tempo")
            fig_receita = px.line(df_receita_mes, x="mes", y="receita", labels={"mes": "Mês", "receita": "Receita (R$)"})
            st.plotly_chart(fig_receita, use_container_width=True)

            # Quantidade de Transações
            df_transacoes = df_filtrado.groupby("mes")["id"].count().reset_index()
            df_transacoes.columns = ["mes", "total"]
            
            st.subheader("🛒 Quantidade de Transações")
            fig3 = px.line(df_transacoes, x="mes", y="total", labels={"mes": "Mês", "total": "Pedidos"})
            st.plotly_chart(fig3, use_container_width=True)
            
          
            # MODELO PREDITIVO 
            st.divider()
            st.subheader("🧠 Previsão de Faturamento")
            
        
            df_diario = preparar_dados_temporais(dados_filtrados)
            
            if not df_diario.empty:
                col_m1, col_m2, col_m3 = st.columns(3)
                
                with col_m1:
                    modelo_escolhido = st.radio(
                        "Modelo Preditivo",
                        [
                            "Random Forest",
                            "Prophet"
                        ],
                        horizontal=True)
                with col_m2:
                    data_min = df_diario["data"].min().date()

                    data_max = df_diario["data"].max().date()

                    t0 = st.date_input(
                        "Data de Corte (t0)",
                        value=data_max - pd.Timedelta(days=90),
                        min_value=data_min,
                        max_value=data_max
                    )
                
                with col_m3:
                    horizonte = st.slider("Dias para prever no futuro:", 7, 60, 30)
                
                # Executa o treino e gera as previsões
                (
    df_previsao,
    df_teste,
    mae,
    rmse,
    mape,
    y_pred_teste
) = treinar_e_prever(
                    df_diario, t0, modelo_escolhido, horizonte_dias=horizonte
                )
                
                if df_previsao is not None:
                    # Exibe as métricas de avaliação (MAE e RMSE)
                    col_met1, col_met2, col_met3 = st.columns(3)
                    col_met1.metric(f"📉 Erro Médio Absoluto (MAE) - {modelo_escolhido}", f"R$ {mae:,.2f}")
                    col_met2.metric(f"📐 Raiz do Erro Quadrático Médio (RMSE)", f"R$ {rmse:,.2f}")
                    col_met3.metric(f"📊 MAPE", f"{mape:.2f}%")

                    st.subheader("🎯 Comparação Real x Previsto")

                    df_comp = pd.DataFrame({
                        "data": df_teste["data"],
                        "Real": df_teste["valor_total"],
                        "Previsto": y_pred_teste[:len(df_teste)]
                    })

                    fig_comp = px.line(
                        df_comp,
                        x="data",
                        y=["Real", "Previsto"],
                        title="Avaliação do Modelo"
                    )

                    st.plotly_chart(
                        fig_comp,
                        use_container_width=True
                    )
                    
                    # Formata os dados para o gráfico unificado
                    df_diario_copy = df_diario.copy()
                    df_diario_copy['Tipo'] = 'Histórico Real'
                    
                    df_previsao_copy = df_previsao.copy()
                    df_previsao_copy['Tipo'] = f'Previsão Futura({modelo_escolhido})'
                    df_previsao_copy['valor_total'] = df_previsao_copy['previsao']
                    
                    df_grafico_ml = pd.concat([
                        df_diario_copy[['data', 'valor_total', 'Tipo']], 
                        df_previsao_copy[['data', 'valor_total', 'Tipo']]
                    ])
                    
                    fig_ml = px.line(
                        df_grafico_ml, 
                        x="data", 
                        y="valor_total", 
                        color="Tipo",
                        title=f"Histórico de Faturamento e Cenário Projetado a partir de {t0}",
                        labels={"data": "Data", "valor_total": "Faturamento Diário (R$)"}
                    )
                    
                    # Adiciona a linha vertical vermelha tracejada no ponto t0
                    fig_ml.add_vline(x=pd.to_datetime(t0).timestamp() * 1000, line_width=2, line_dash="dash", line_color="red")
                    
                    st.plotly_chart(fig_ml, use_container_width=True)
                else:
                    st.warning("Dados insuficientes após a data t0 para calcular as métricas de teste.")
            else:
                st.warning("Não há dados diários suficientes para o modelo preditivo.")
        else:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")
else:
    st.error("❌ Não foi possível conectar à API FastAPI. Verifique se o servidor está rodando.")