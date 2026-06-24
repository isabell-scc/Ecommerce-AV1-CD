# 📊 Dashboard de Vendas de E-commerce — AV2

Projeto desenvolvido para as Avaliações 1 e 2 da disciplina de Ciência de Dados (NES).

O sistema simula dados de um e-commerce, armazena-os em um banco relacional SQLite, expõe uma API REST com FastAPI e disponibiliza um dashboard interativo preditivo com Streamlit.


---

## Rotas da API

| Método | Rota       | Descrição |
|--------|------------|-----------|
| GET    | `/health`  | Health check — retorna `{"status": "ok"}` |
| GET    | `/dados`   | Registros do banco com filtros opcionais |
| GET    | `/resumo`  | KPIs agregados (faturamento, pedidos, ticket médio) |

**Query params disponíveis em `/dados` e `/resumo`:**
- `categoria` — ex: `Eletrônicos`, `Roupas`, `Casa`, `Livros`
- `estado` — ex: `SP`, `RJ`, `MG`
- `data_inicio` e `data_fim` — formato `YYYY-MM-DD`

**Documentação interativa:** http://localhost:8000/docs

---

## ▶ Como Executar

### Pré-requisito
- Docker instalado

### Subir tudo
```bash
docker compose up --build
```

Aguarde os três serviços iniciarem. Depois acesse:
- **Dashboard:** http://localhost:8501
- **API (docs):** http://localhost:8000/docs

---

## Modelos Preditivos

O dashboard permite selecionar entre dois modelos:

- **Random Forest** com Grid Search (3-fold CV) otimizando hiperparâmetros `n_estimators`, `max_depth` e `min_samples_split`
- **Prophet** com sazonalidade semanal, anual, mensal e feriados brasileiros

**Métricas exibidas no dashboard:** MAE, RMSE e MAPE no período de teste (dados após t0).

---

## Estrutura do Projeto

```
.
├── api/
│   └── main.py          # FastAPI com rotas /health, /dados, /resumo
├── dashboard/
│   ├── dashboard.py     # Interface Streamlit
│   └── modelo.py        # Lógica de ML (Random Forest + Prophet)
├── src/
│   └── gerador.py       # Gerador de dados sintéticos
├── data/
│   └── ecommerce.db     # Banco SQLite (gerado automaticamente)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.MD
```
