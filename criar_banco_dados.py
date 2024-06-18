import sqlite3

db_path = 'dataBase/laboratorio.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Criação das tabelas
cursor.execute('''
CREATE TABLE IF NOT EXISTS administradores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    senha TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    matricula TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    card_id TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS registro_administrativo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    acao TEXT NOT NULL,
    descricao TEXT NOT NULL,
    timestamp TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS registro_acesso (
    matricula TEXT NOT NULL,
    nome TEXT NOT NULL,
    timestamp TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS solicitacoes_cartao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL DEFAULT 'pendente',
    card_id TEXT
)
''')

# Inserção do administrador Yan com senha '123'
cursor.execute('''
INSERT INTO administradores (nome, senha) VALUES (?, ?)
''', ('Yan', '123'))

conn.commit()
conn.close()
