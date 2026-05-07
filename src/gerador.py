import random
import os
from faker import Faker
import sqlite3
from datetime import date

# Semente fixa para reproduzibilidade 42
random.seed(42)
fake = Faker("pt_BR")

DB_PATH = os.environ.get("DATABASE_URL", "data/ecommerce.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON")

cursor.execute("DROP TABLE IF EXISTS pedidos")
cursor.execute("DROP TABLE IF EXISTS produtos")
cursor.execute("DROP TABLE IF EXISTS clientes")
cursor.execute("DROP TABLE IF EXISTS categorias")

# TABELAS

cursor.execute("""
CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    estado TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    preco REAL NOT NULL,
    categoria_id INTEGER NOT NULL,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    data TEXT NOT NULL,
    valor_total REAL NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
)
""")

# CATEGORIAS
categorias = [("Eletrônicos",), ("Roupas",), ("Casa",), ("Livros",)]
cursor.executemany(
    "INSERT INTO categorias (nome) VALUES (?)", categorias)

# PRODUTOS
produtos = [
    ("celular", 1500, 1), ("notebook", 3500, 1), ("fone", 200, 1),
    ("camisa", 80, 2), ("tênis", 200, 2), ("jaqueta", 300, 2),
    ("panela", 120, 3), ("cadeira", 400, 3), ("mesa", 700, 3),
    ("what if?", 90, 4), ("mulherzinhas", 50, 4), ("a guerra da papoula", 40, 4)
]

cursor.executemany(
    "INSERT INTO produtos (nome, preco, categoria_id) VALUES (?, ?, ?)", produtos)


# CLIENTES
estados = ["SP", "RJ", "MG", "RS", "BA", "PR", "PI", "AL", "PE", "CE"]

for _ in range(50):
    cursor.execute(
        "INSERT INTO clientes (nome, estado) VALUES (?, ?)",
        (fake.name(), random.choice(estados))
    )


# PEDIDOS e SAZONALIDADE

cursor.execute("SELECT id, preco FROM produtos")
produtos_db = cursor.fetchall()

produtos_dict = {p[0]: p[1] for p in produtos_db}

pedidos = []

NUM_PEDIDOS = 5000
sazonalidade = {
1: (1, 2),   # janeiro (férias)
2: (1, 2),
3: (1, 1),
4: (1, 1),
5: (1, 2),   # dia das mães
6: (1, 2),
7: (1, 1),
8: (1, 1),
9: (1, 2),
10: (1, 2),
11: (2, 5),  # black friday
12: (2, 4)   # natal
}

for _ in range(NUM_PEDIDOS):
    data = fake.date_between(start_date= date(2024, 1, 1), end_date= date(2026, 12, 31))

    min_qtd, max_qtd = sazonalidade[data.month]
    qtd = random.randint(min_qtd, max_qtd)

    produto_id = random.choice(list(produtos_dict.keys()))
    preco = produtos_dict[produto_id]

    pedidos.append((
        random.randint(1, 50),
        produto_id,
        qtd,
        data.isoformat(),
        qtd * preco
    ))

cursor.executemany("""
INSERT INTO pedidos (
    cliente_id,
    produto_id,
    quantidade,
    data,
    valor_total
) VALUES (?, ?, ?, ?, ?)
""", pedidos)


conn.commit()
conn.close()

print("✅ Dados gerados com sucesso!")

