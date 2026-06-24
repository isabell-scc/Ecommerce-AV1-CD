import os
import sqlite3
from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List

app = FastAPI(title="API E-commerce - AV2")

# Descobre a pasta raiz do projeto de forma dinâmica (sobe um nível a partir de 'api/')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "ecommerce.db")

def get_db_connection():
    if not os.path.exists(DB_PATH):
        raise HTTPException(
            status_code=500, 
            detail=f"Banco de dados não encontrado em {DB_PATH}. Certifique-se de rodar o gerador primeiro."
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 1. ROTA HEALTH CHECK
@app.get("/health")
def health_check():
    return {"status": "ok", "database": "conectado", "path": DB_PATH}

# 2. ROTA RESUMO (KPIs)
@app.get("/resumo")
def get_resumo(
    categoria: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    estado: Optional[str] = Query(None)
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                SUM(pe.valor_total) AS faturamento_total,
                COUNT(*) AS total_pedidos,
                AVG(pe.valor_total) AS ticket_medio
            FROM pedidos pe
            JOIN produtos pr ON pe.produto_id = pr.id
            JOIN categorias c ON pr.categoria_id = c.id
            JOIN clientes cl ON pe.cliente_id = cl.id
        """

        where_clauses = []
        params = []

        if categoria and categoria != "Todas":
            if categoria == "Vestuário":
                categoria = "Roupas"

            where_clauses.append("c.nome = ?")
            params.append(categoria)

        if data_inicio:
            where_clauses.append("pe.data >= ?")
            params.append(data_inicio)

        if data_fim:
            where_clauses.append("pe.data <= ?")
            params.append(data_fim)

        if estado and estado != "Todos":
            where_clauses.append("cl.estado = ?")
            params.append(estado)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        cursor.execute(query, params)

        row = cursor.fetchone()
        conn.close()

        return {
            "faturamento_total": row["faturamento_total"] or 0,
            "total_pedidos": row["total_pedidos"] or 0,
            "ticket_medio": row["ticket_medio"] or 0
        }

    except sqlite3.OperationalError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro operacional no banco: {str(e)}"
        )

# 3. ROTA DADOS BRUTOS COM FILTROS para o dashboard
@app.get("/dados")
def get_dados(
    categoria: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    estado: Optional[str] = Query(None)
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query base trazendo o histórico completo estruturado
        query = """
            SELECT 
                pe.id,
                pe.data,
                pe.quantidade,
                pe.valor_total,
                pr.nome AS produto,
                c.nome AS categoria,
                cl.estado
            FROM pedidos pe
            JOIN produtos pr ON pe.produto_id = pr.id
            JOIN categorias c ON pr.categoria_id = c.id
            JOIN clientes cl ON pe.cliente_id = cl.id
        """
        
        where_clauses = []
        params = []
      
        if categoria and categoria != "Todas":
            if categoria == "Vestuário":
                categoria = "Roupas"
            where_clauses.append("c.nome = ?")
            params.append(categoria)
            
        if data_inicio:
            where_clauses.append("pe.data >= ?")
            params.append(data_inicio)
            
        if data_fim:
            where_clauses.append("pe.data <= ?")
            params.append(data_fim)
            
        if estado and estado != "Todos":
            where_clauses.append("cl.estado = ?")
            params.append(estado)
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
            
        query += " ORDER BY pe.data ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        resultado = []
        for row in rows:
            resultado.append({
                "id": row["id"],
                "data": row["data"],
                "quantidade": row["quantidade"],
                "valor_total": row["valor_total"],
                "produto": row["produto"],
                "categoria": row["categoria"],
                "estado": row["estado"]
            })
            
        return resultado

    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados: {str(e)}")