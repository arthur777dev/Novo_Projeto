from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
from functools import wraps
import uuid

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = 'segredo_supersecreto'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        conn = get_db()
        user = conn.execute("SELECT * FROM usuarios WHERE id = ?", (session['user_id'],)).fetchone()
        conn.close()
        if not user or user['is_admin'] != 1:
            return "Acesso negado! Apenas administradores podem acessar esta página.", 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    conn = get_db()
    imoveis = conn.execute("SELECT * FROM imoveis WHERE status = 'aprovado'").fetchall()
    conn.close()
    return render_template('index.html', imoveis=imoveis)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        user = conn.execute('SELECT * FROM usuarios WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            return redirect('/')
        else:
            return render_template('login.html', error='Usuário ou senha inválidos!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/cadastro_imovel', methods=['GET', 'POST'])
def cadastro_imovel():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        preco = request.form['preco']
        endereco = request.form['endereco']
        tipo = request.form['tipo']
        area = request.form['area']
        quartos = request.form['quartos']
        banheiros = request.form['banheiros']
        vagas = request.form['vagas']
        contato = request.form['contato']
        usuario_id = session['user_id']

        caracteristicas_selecionadas = request.form.getlist('caracteristicas')
        caracteristicas_str = ','.join(caracteristicas_selecionadas)

        arquivos = request.files.getlist('fotos')
        nomes_fotos = []
        for file in arquivos:
            if file and allowed_file(file.filename):
                extensao = file.filename.rsplit('.', 1)[1].lower()
                novo_nome = f"{uuid.uuid4().hex}.{extensao}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], novo_nome)
                file.save(file_path)
                nomes_fotos.append(novo_nome)
        
        fotos_str = ','.join(nomes_fotos)

        conn = get_db()
        conn.execute('''
            INSERT INTO imoveis 
            (titulo, descricao, preco, endereco, tipo, area, quartos, banheiros, vagas, caracteristicas, contato, fotos, status, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pendente', ?)
        ''', (titulo, descricao, preco, endereco, tipo, area, quartos, banheiros, vagas, caracteristicas_str, contato, fotos_str, usuario_id))
        conn.commit()
        conn.close()
        
        flash('Seu imóvel foi enviado para análise e será publicado em breve!', 'success')
        return redirect('/')
        
    return render_template('cadastro_imovel.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        telefone = request.form['telefone']
        endereco = request.form['endereco']
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        try:
            conn = get_db()
            conn.execute('''
                INSERT INTO usuarios (username, password, nome, telefone, endereco, is_admin)
                VALUES (?, ?, ?, ?, ?, 0)
            ''', (username, hashed_password, nome, telefone, endereco))
            conn.commit()
            conn.close()
            return redirect('/login')
        except sqlite3.IntegrityError:
            return render_template('register.html', error='Usuário já existe!')
    return render_template('register.html')

@app.route('/admin/imoveis')
@admin_required
def admin_imoveis():
    conn = get_db()
    imoveis_pendentes = conn.execute("SELECT * FROM imoveis WHERE status = 'pendente'").fetchall()
    conn.close()
    return render_template('admin_imoveis.html', imoveis=imoveis_pendentes)

@app.route('/admin/aprovar/<int:imovel_id>')
@admin_required
def aprovar_imovel(imovel_id):
    conn = get_db()
    conn.execute("UPDATE imoveis SET status = 'aprovado' WHERE id = ?", (imovel_id,))
    conn.commit()
    conn.close()
    return redirect('/admin/imoveis')

@app.route('/admin/rejeitar/<int:imovel_id>')
@admin_required
def rejeitar_imovel(imovel_id):
    conn = get_db()
    conn.execute("UPDATE imoveis SET status = 'rejeitado' WHERE id = ?", (imovel_id,))
    conn.commit()
    conn.close()
    return redirect('/admin/imoveis')

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nome TEXT,
            telefone TEXT,
            endereco TEXT,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS imoveis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT,
            preco REAL NOT NULL,
            endereco TEXT,
            tipo TEXT,
            area REAL,
            quartos INTEGER,
            banheiros INTEGER,
            vagas INTEGER,
            caracteristicas TEXT,
            contato TEXT,
            fotos TEXT,
            status TEXT DEFAULT 'pendente',
            usuario_id INTEGER,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    ''')
    conn.commit()

    admin_user = conn.execute("SELECT * FROM usuarios WHERE username = 'admin'").fetchone()
    if not admin_user:
        conn.execute(
            "INSERT INTO usuarios (username, password, nome, telefone, endereco, is_admin) VALUES (?, ?, ?, ?, ?, ?)",
            ('admin', generate_password_hash('123456'), 'Administrador', '', '', 1)
        )
        conn.commit()
        print("✅ Admin criado com sucesso!")
    else:
        print("ℹ️ Admin já existe.")
    conn.close()

    app.run(debug=True)