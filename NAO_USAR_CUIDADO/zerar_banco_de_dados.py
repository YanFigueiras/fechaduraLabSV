import sqlite3

db_path = '../dataBase/laboratorio.db'

# Conectar ao banco de dados
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Função para zerar o banco de dados
def reset_database(cursor):
    cursor.execute('DROP TABLE IF EXISTS administradores')
    cursor.execute('DROP TABLE IF EXISTS usuarios')
    cursor.execute('DROP TABLE IF EXISTS registro_administrativo')
    cursor.execute('DROP TABLE IF EXISTS registro_acesso')
    cursor.execute('DROP TABLE IF EXISTS solicitacoes_cartao')

# Chamar a função para zerar o banco de dados
reset_database(cursor)

# Criação das tabelas
cursor.execute('''
CREATE TABLE administradores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    senha TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE usuarios (
    matricula TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    card_id TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE registro_administrativo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    acao TEXT NOT NULL,
    descricao TEXT NOT NULL,
    timestamp TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE registro_acesso (
    matricula TEXT NOT NULL,
    nome TEXT NOT NULL,
    timestamp TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE solicitacoes_cartao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL DEFAULT 'pendente',
    card_id TEXT
)
''')

# Inserção do administrador padrão admin com senha 'admin'
cursor.execute('''
INSERT INTO administradores (nome, senha) VALUES (?, ?)
''', ('admin', 'admin'))

# Confirmar as alterações e fechar a conexão
conn.commit()
conn.close()
