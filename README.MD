# 📊 Dashboard de Vendas de E-commerce

Projeto desenvolvido para a Avaliação 1 da disciplina de Ciência de Dados (NES).

O objetivo é simular dados de um e-commerce, armazená-los em um banco relacional e disponibilizar um dashboard interativo para análise das vendas.

---

## 🎯 Objetivo

Analisar o desempenho de vendas de um e-commerce, permitindo:

* Identificar padrões e tendências de vendas
* Avaliar faturamento por categoria
* Visualizar produtos mais vendidos
* Analisar a evolução temporal das vendas


---

## ⚙️ Arquitetura do Projeto

O sistema é composto por três partes principais:

1. **Gerador de dados**

   * Script em Python que cria dados simulados
   * Uso de Faker para dados realistas
   * Uso de `random.seed(42)` para reprodutibilidade

2. **Banco de dados (SQLite)**

   * Armazena os dados gerados
   * Estrutura relacional

3. **Dashboard (Streamlit)**

   * Visualização interativa dos dados
   * Filtros dinâmicos e gráficos

Fluxo do sistema:

Gerador → Banco → Dashboard

---

## 📊 Dashboard

O dashboard permite análise interativa com:

### KPIs

* 💰 Faturamento total
* 📦 Número de pedidos
* 🧾 Ticket médio

### Visualizações

* Faturamento por categoria
* Produtos mais vendidos
* Evolução temporal das vendas

### Filtros

* Estado
* Ano
* Intervalo de meses

---


## ▶️ Como Executar o Projeto

### Pré-requisitos

* Docker instalado

### Passos

```bash
docker compose up
```

Após executar, acesse o dashboard em:

http://localhost:8501

---

## 📁 Estrutura do Projeto

```bash
.
├── src/
│   ├── dashboard.py
│   └── gerador.py
├── data/
├── slides/
│   ├── apresentacao_ecommerce.tex
│   └── apresentacai_ecommerce.pdf
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```



---
