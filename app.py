from flask import Flask, render_template, request, redirect, url_for, session, g
from functools import wraps
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = b'@\x1d\xa7\\N\xf1\xb7\xb4\x18\xa1\xb7\x92\xbf\x93\xbf\x8bu\x8a\x86\xe3|\xd0c+'
db_path = '/home/avant/fechaduraLabSV/dataBase/laboratorio.db'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def before_request():
    g.username = session.get('username')

def execute_db_query_with_retry(query, params=(), retries=5, delay=1):
    while retries > 0:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            cursor.close()
            conn.close()
            return
        except sqlite3.OperationalError as e:
            if 'locked' in str(e):
                retries -= 1
                time.sleep(delay)
            else:
                raise
    raise sqlite3.OperationalError("Max retries reached, database is still locked")

def registrar_acao(nome, acao, descricao):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    query = "INSERT INTO registro_administrativo (nome, acao, descricao, timestamp) VALUES (?, ?, ?, ?)"
    params = (nome, acao, descricao, timestamp)
    execute_db_query_with_retry(query, params)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM administradores WHERE nome=? AND senha=?", (username, password))
        admin = cursor.fetchone()
        conn.close()
        if admin:
            session['logged_in'] = True
            session['username'] = username
            registrar_acao(username, 'login', 'Usuário logou no sistema')
            return redirect(url_for('home'))
        else:
            error = "Login falhou. Verifique suas credenciais."
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout_route():
    nome = session.get('username')
    registrar_acao(nome, 'logout', 'Usuário deslogou do sistema')
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    return render_template('home.html')

@app.route('/adicionar_usuario', methods=['GET', 'POST'])
@login_required
def adicionar_usuario():
    error = None
    if request.method == 'POST':
        if 'solicitar_cartao' in request.form:
            # Solicita a leitura do cartão
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO solicitacoes_cartao (status) VALUES ('pendente')")
            conn.commit()
            cursor.execute("SELECT id FROM solicitacoes_cartao WHERE status='pendente' ORDER BY id DESC LIMIT 1")
            solicitacao_id = cursor.fetchone()[0]
            conn.close()
            registrar_acao(session['username'], 'solicitar_cartao', f'Solicitação de leitura de cartão ID: {solicitacao_id}')
            return redirect(url_for('adicionar_usuario', solicitacao_id=solicitacao_id))
        
        elif 'confirmar_cadastro' in request.form:
            solicitacao_id = request.form['solicitacao_id']
            matricula = request.form['matricula']
            nome = request.form['nome']

            # Verifica se a solicitação foi concluída e obtém o card_id
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT card_id FROM solicitacoes_cartao WHERE id=? AND status='concluido'", (solicitacao_id,))
            resultado = cursor.fetchone()
            if resultado:
                card_id = resultado[0]
                query = "INSERT INTO usuarios (matricula, nome, card_id) VALUES (?, ?, ?)"
                params = (matricula, nome, card_id)
                execute_db_query_with_retry(query, params)
                registrar_acao(session['username'], 'adicionar_usuario', f'Adicionado usuário: {nome} (Matrícula: {matricula})')
                return redirect(url_for('home'))
            else:
                error = "Erro: Cartão não lido. Tente novamente."
    
    solicitacao_id = request.args.get('solicitacao_id')
    return render_template('adicionar_usuario.html', solicitacao_id=solicitacao_id, error=error)


@app.route('/administradores', methods=['GET', 'POST'])
@login_required
def administradores():
    if request.method == 'POST':
        if 'adicionar' in request.form:
            nome = request.form['nome']
            senha = request.form['senha']
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO administradores (nome, senha) VALUES (?, ?)", (nome, senha))
            conn.commit()
            conn.close()
            registrar_acao(session['username'], 'adicionar_administrador', f'Adicionado administrador: {nome}')
        elif 'editar' in request.form:
            id = request.form['id']
            nome = request.form['nome']
            senha = request.form['senha']
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE administradores SET nome=?, senha=? WHERE id=?", (nome, senha, id))
            conn.commit()
            conn.close()
            registrar_acao(session['username'], 'editar_administrador', f'Editado administrador: {nome}')
        elif 'remover' in request.form:
            id = request.form['id']
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM administradores WHERE id=?", (id,))
            conn.commit()
            conn.close()
            registrar_acao(session['username'], 'remover_administrador', f'Removido administrador com id: {id}')
        return redirect(url_for('administradores'))
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM administradores")
    administradores = cursor.fetchall()
    conn.close()
    return render_template('administradores.html', administradores=administradores)

@app.route('/alterar_usuario', methods=['GET', 'POST'])
@login_required
def alterar_usuario():
    if request.method == 'POST':
        matricula = request.form['matricula']
        novo_nome = request.form.get('novo_nome')
        novo_card_id = request.form.get('novo_card_id')
        
        if novo_nome:
            query_nome = "UPDATE usuarios SET nome=? WHERE matricula=?"
            params_nome = (novo_nome, matricula)
            execute_db_query_with_retry(query_nome, params_nome)
            registrar_acao(session['username'], 'alterar_usuario', f'Alterado nome do usuário: {novo_nome} (Matrícula: {matricula})')
        
        if novo_card_id:
            query_card_id = "UPDATE usuarios SET card_id=? WHERE matricula=?"
            params_card_id = (novo_card_id, matricula)
            execute_db_query_with_retry(query_card_id, params_card_id)
            registrar_acao(session['username'], 'alterar_usuario', f'Alterado Card ID do usuário: {novo_card_id} (Matrícula: {matricula})')
        
        return redirect(url_for('alterar_usuario'))
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT matricula, nome FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    
    usuario = None
    if 'matricula' in request.args:
        matricula = request.args.get('matricula')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT matricula, nome, card_id FROM usuarios WHERE matricula=?", (matricula,))
        usuario = cursor.fetchone()
        conn.close()
    
    return render_template('alterar_usuario.html', usuarios=usuarios, usuario=usuario)


@app.route('/listar_usuarios')
@login_required
def listar_usuarios():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT matricula, nome, card_id FROM usuarios ORDER BY nome")
    usuarios = cursor.fetchall()
    conn.close()
    registrar_acao(session['username'], 'listar_usuarios', 'Listou todos os usuários')
    return render_template('listar_usuarios.html', usuarios=usuarios)



@app.route('/remover_usuario', methods=['GET', 'POST'])
@login_required
def remover_usuario():
    if request.method == 'POST':
        matricula = request.form['matricula']
        query = "DELETE FROM usuarios WHERE matricula=?"
        params = (matricula,)
        execute_db_query_with_retry(query, params)
        registrar_acao(session['username'], 'remover_usuario', f'Removido usuário com matrícula: {matricula}')
        return redirect(url_for('home'))
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT matricula, nome FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return render_template('remover_usuario.html', usuarios=usuarios)

@app.route('/registros_acesso', methods=['GET', 'POST'])
@login_required
def registros_acesso():
    registros = []
    if request.method == 'POST':
        matricula = request.form.get('matricula')
        data_inicio = request.form.get('data_inicio')
        hora_inicio = request.form.get('hora_inicio')
        data_fim = request.form.get('data_fim')
        hora_fim = request.form.get('hora_fim')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        query = "SELECT * FROM registro_acesso WHERE 1=1"
        params = []
        
        if matricula:
            query += " AND matricula=?"
            params.append(matricula)
        if data_inicio:
            datetime_inicio = f"{data_inicio} {hora_inicio or '00:00:00'}"
            query += " AND timestamp >= ?"
            params.append(datetime_inicio)
        if data_fim:
            datetime_fim = f"{data_fim} {hora_fim or '23:59:59'}"
            query += " AND timestamp <= ?"
            params.append(datetime_fim)
        
        query += " ORDER BY timestamp DESC"
        cursor.execute(query, params)
        registros = cursor.fetchall()
        conn.close()
    registrar_acao(session['username'], 'listar_registros_acesso', 'Listou registros de acesso')
    return render_template('registros_acesso.html', registros=registros)


@app.route('/registros_administrativos', methods=['GET', 'POST'])
@login_required
def registros_administrativos():
    registros = []
    acoes = []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT acao FROM registro_administrativo")
    acoes = cursor.fetchall()
    conn.close()
    
    if request.method == 'POST':
        acao = request.form.get('acao')
        data_inicio = request.form.get('data_inicio')
        hora_inicio = request.form.get('hora_inicio')
        data_fim = request.form.get('data_fim')
        hora_fim = request.form.get('hora_fim')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        query = "SELECT * FROM registro_administrativo WHERE 1=1"
        params = []
        
        if acao:
            query += " AND acao=?"
            params.append(acao)
        if data_inicio:
            datetime_inicio = f"{data_inicio} {hora_inicio or '00:00:00'}"
            query += " AND timestamp >= ?"
            params.append(datetime_inicio)
        if data_fim:
            datetime_fim = f"{data_fim} {hora_fim or '23:59:59'}"
            query += " AND timestamp <= ?"
            params.append(datetime_fim)
        
        query += " ORDER BY timestamp DESC"
        cursor.execute(query, params)
        registros = cursor.fetchall()
        conn.close()
    registrar_acao(session['username'], 'listar_registros_administrativos', 'Listou registros administrativos')
    return render_template('registros_administrativos.html', registros=registros, acoes=acoes)

if __name__ == "__main__":
    app.run(debug=True)
