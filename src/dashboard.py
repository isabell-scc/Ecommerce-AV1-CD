import streamlit as st
import pandas as pd
import os
from sqlalchemy import create_engine, text
import plotly.express as px

st.set_page_config(page_title="Dashboard E-commerce", layout="wide")

DB_PATH = os.environ.get("DATABASE_URL", "data/ecommerce.db")
engine = create_engine(f"sqlite:///{DB_PATH}")

st.title("🛒 Dashboard de Vendas")


# FILTROS
estados_df = pd.read_sql("SELECT DISTINCT estado FROM clientes", engine)
estado = st.selectbox("Estado:", ["Todos"] + sorted(estados_df["estado"]))

anos_df = pd.read_sql("SELECT DISTINCT substr(data,1,4) AS ano FROM pedidos", engine)
ano = st.selectbox("Ano:", ["Todos"] + sorted(anos_df["ano"]))

mes_inicio, mes_fim = st.slider(
    "Período (meses):",
    1, 12, (1, 12)
)

where_clauses = []
params = {}

# estado
if estado != "Todos":
    where_clauses.append("cl.estado = :estado")
    params["estado"] = estado

# ano
if ano != "Todos":
    where_clauses.append("substr(pe.data,1,4) = :ano")
    params["ano"] = ano

# mês 
where_clauses.append(
    "CAST(substr(pe.data,6,2) AS INTEGER) BETWEEN :mes_inicio AND :mes_fim"
)
params["mes_inicio"] = mes_inicio
params["mes_fim"] = mes_fim

where = ""
if where_clauses:
    where = "WHERE " + " AND ".join(where_clauses)

filtros = []
if estado != "Todos":
    filtros.append(f"Estado: {estado}")
if ano != "Todos":
    filtros.append(f"Ano: {ano}")
filtros.append(f"Meses: {mes_inicio}-{mes_fim}")

st.info("Filtros ativos: " + " | ".join(filtros))

# KPIs

df_kpi = pd.read_sql(text(f"""
SELECT
    SUM(pe.valor_total) AS faturamento,
    COUNT(*) AS pedidos
FROM pedidos pe
JOIN produtos pr ON pe.produto_id = pr.id
JOIN clientes cl ON pe.cliente_id = cl.id
{where}
"""), engine, params=params)

faturamento = df_kpi["faturamento"].iloc[0] or 0
pedidos = df_kpi["pedidos"].iloc[0] or 0
ticket = faturamento / pedidos if pedidos > 0 else 0

col1, col2, col3 = st.columns(3)

col1.metric("💰 Faturamento Total", f"R$ {faturamento:,.2f}")
col2.metric("📦 Total de Pedidos", f"{int(pedidos)}")
col3.metric("🧾 Ticket Médio", f"R$ {ticket:,.2f}")

st.divider()

# GRÁFICO 1 - CATEGORIAS

df_cat = pd.read_sql(text(f"""
SELECT c.nome AS categoria,
       SUM(pe.valor_total) AS faturamento
FROM pedidos pe
JOIN produtos pr ON pe.produto_id = pr.id
JOIN categorias c ON pr.categoria_id = c.id
JOIN clientes cl ON pe.cliente_id = cl.id
{where}
GROUP BY c.nome
ORDER BY faturamento DESC
"""), engine, params=params)

st.subheader("💰 Faturamento por Categoria")
st.plotly_chart(px.bar(
    df_cat, x="categoria", y="faturamento", color="categoria",
    labels={"categoria": "Categoria", "faturamento": "Faturamento (R$)"}
), use_container_width=True)


# GRÁFICO 2 - PRODUTOS
df_prod = pd.read_sql(text(f"""
SELECT pr.nome,
       SUM(pe.quantidade) AS total_vendido
FROM pedidos pe
JOIN produtos pr ON pe.produto_id = pr.id
JOIN clientes cl ON pe.cliente_id = cl.id
{where}
GROUP BY pr.nome
ORDER BY total_vendido DESC
LIMIT 10
"""), engine, params=params)

# tabela ranking
st.subheader("📋 Ranking de Produtos")
df_rank = df_prod.reset_index(drop=True)
df_rank.index += 1
df_rank.columns = ["Produto", "Unidades Vendidas"]
st.dataframe(df_rank, use_container_width=True)

# GRÁFICOS 3 E 4 - EVOLUÇÃO

df_receita_mes = pd.read_sql(text(f"""
SELECT substr(pe.data,1,7) AS mes,
       SUM(pe.valor_total) AS receita
FROM pedidos pe
JOIN clientes cl ON pe.cliente_id = cl.id
{where}
GROUP BY mes
ORDER BY mes
"""), engine, params=params)

st.subheader("📈 Receita Mensal ao Longo do Tempo")

fig_receita = px.line(
    df_receita_mes,
    x="mes",
    y="receita",
    labels={"mes": "Mês", "receita": "Receita (R$)"}
)

st.plotly_chart(fig_receita, use_container_width=True)


df_time = pd.read_sql(text(f"""
SELECT substr(pe.data,1,7) AS mes,
       COUNT(*) AS total
FROM pedidos pe
JOIN produtos pr ON pe.produto_id = pr.id
JOIN clientes cl ON pe.cliente_id = cl.id
{where}
GROUP BY mes
ORDER BY mes
"""), engine, params=params)

st.subheader("🛒 Quantidade de Transações")

fig3 = px.line(
    df_time, x="mes", y="total",
    labels={"mes": "Mês", "total": "Pedidos"}
)
st.plotly_chart(fig3, use_container_width=True)