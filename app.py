from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
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
            return redirect(url_for('login'))
        conn = get_db()
        user = conn.execute("SELECT * FROM usuarios WHERE id = ?", (session['user_id'],)).fetchone()
        conn.close()
        if not user or user['is_admin'] != 1:
            flash("Acesso negado! Apenas administradores podem acessar esta página.", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    # Pega os valores do formulário que vêm pela URL (GET)
    operacao = request.args.get('operacao', '')
    tipo = request.args.get('tipo', '')
    cidade = request.args.get('cidade', '')
    bairro = request.args.get('bairro', '')
    valor_min = request.args.get('faixa_valor', '')
    valor_max = request.args.get('faixa_valor_max', '')

    conn = get_db()
    
    # Começa a montar a consulta SQL
    query = "SELECT * FROM imoveis WHERE status = 'aprovado'"
    params = []

    # Verifica se algum filtro foi aplicado
    search_active = bool(operacao or tipo or cidade or bairro or valor_min or valor_max)

    # Adiciona filtros à consulta dinamicamente
    if operacao:
        query += " AND operacao = ?"
        params.append(operacao)
    if tipo:
        query += " AND tipo = ?"
        params.append(tipo)
    if cidade:
        query += " AND endereco LIKE ?"
        params.append(f'%{cidade}%')
    if bairro:
        query += " AND endereco LIKE ?"
        params.append(f'%{bairro}%')
    
    # Filtro de Preço Mínimo
    if valor_min:
        try:
            preco_min_float = float(valor_min)
            query += " AND preco >= ?"
            params.append(preco_min_float)
        except ValueError:
            pass # Ignora se o valor não for um número

    # Filtro de Preço Máximo
    if valor_max:
        try:
            preco_max_float = float(valor_max)
            query += " AND preco <= ?"
            params.append(preco_max_float)
        except ValueError:
            pass # Ignora se o valor não for um número

    # Executa a consulta com os parâmetros seguros
    imoveis = conn.execute(query, params).fetchall()
    conn.close()
    
    if search_active:
        # Se uma busca foi feita, mostra apenas os resultados
        return render_template('index.html', 
                               imoveis_resultado=imoveis, 
                               search_active=True)
    else:
        # Se a página foi carregada normally (sem busca), mostra os destaques
        imoveis_compra = [i for i in imoveis if i['operacao'] == 'compra']
        imoveis_aluguel = [i for i in imoveis if i['operacao'] == 'aluguel']
        return render_template('index.html', 
                               imoveis_compra=imoveis_compra, 
                               imoveis_aluguel=imoveis_aluguel,
                               search_active=False)

# ROTA: Página de Detalhes do Imóvel
@app.route('/imovel/<int:imovel_id>')
def imovel_detalhe(imovel_id):
    conn = get_db()
    # Busca apenas imóveis aprovados para visualização pública
    imovel = conn.execute("SELECT * FROM imoveis WHERE id = ? AND status = 'aprovado'", (imovel_id,)).fetchone()
    conn.close()
    
    if imovel is None:
        flash("Imóvel não encontrado ou ainda não aprovado para visualização.", "error")
        return redirect(url_for('index'))

    # Prepara a lista de fotos e características
    # Filtra fotos vazias
    fotos_list = [f for f in imovel['fotos'].split(',') if f.strip()] if imovel['fotos'] else []
    caracteristicas_list = imovel['caracteristicas'].split(',') if imovel['caracteristicas'] else []
        
    return render_template('imovel_detalhe.html', imovel=imovel, fotos_list=fotos_list, caracteristicas_list=caracteristicas_list)

# === NOVAS ROTAS ADICIONADAS ===

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/contato')
def contato():
    return render_template('contato.html')

# =================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # MUDANÇA: Login agora usa 'email'
        email = request.form['email']
        password = request.form['password']
        conn = get_db()
        # MUDANÇA: Buscar pelo novo campo 'email'
        user = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            
            # MUDANÇA: Armazenar o primeiro nome para exibição no topo
            full_name = user['nome']
            if full_name:
                # Pega apenas o primeiro nome
                first_name = full_name.split()[0]
            else:
                # Fallback para o email se o nome for nulo
                first_name = user['email'] 
                
            session['first_name'] = first_name

            # Mantém session['username'] (que agora armazena o email) para compatibilidade 
            session['username'] = user['username'] 
            session['is_admin'] = user['is_admin']
            return redirect(url_for('index'))
        else:
            flash('E-mail ou senha inválidos!', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/cadastro_imovel', methods=['GET', 'POST'])
def cadastro_imovel():
    if 'user_id' not in session:
        flash("Você precisa estar logado para anunciar um imóvel.", "error")
        return redirect(url_for('login'))
    if request.method == 'POST':
        # CAMPO: OPERAÇÃO
        operacao = request.form['operacao']
        
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
            (titulo, descricao, preco, endereco, tipo, area, quartos, banheiros, vagas, caracteristicas, contato, fotos, status, usuario_id, operacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pendente', ?, ?)
        ''', (titulo, descricao, preco, endereco, tipo, area, quartos, banheiros, vagas, caracteristicas_str, contato, fotos_str, usuario_id, operacao))
        conn.commit()
        conn.close()
        
        flash('Seu imóvel foi enviado para análise e será publicado em breve!', 'success')
        return redirect(url_for('index'))
        
    return render_template('cadastro_imovel.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        telefone = request.form['telefone']
        # MUDANÇA: Novo campo de e-mail e cpf do formulário
        email = request.form['email'] 
        cpf = request.form['cpf']
        # O campo 'username' é preenchido com o 'email' para compatibilidade com o DB.
        username_for_db = email 
        
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        try:
            conn = get_db()
            # MUDANÇA: Atualizado o INSERT para incluir 'email' e 'cpf' e remover 'endereco'.
            conn.execute('''
                INSERT INTO usuarios (username, password, nome, telefone, is_admin, email, cpf)
                VALUES (?, ?, ?, ?, 0, ?, ?)
            ''', (username_for_db, hashed_password, nome, telefone, email, cpf))
            conn.commit()
            conn.close()
            flash('Conta criada com sucesso! Faça o login.', 'success')
        except sqlite3.IntegrityError as e:
            if 'username' in str(e) or 'email' in str(e):
                flash('Este e-mail já está em uso. Tente outro.', 'error')
            else:
                flash('Erro ao registrar. Tente novamente.', 'error')
            return redirect(url_for('register'))
        return redirect(url_for('login'))
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
    return redirect(url_for('admin_imoveis'))

@app.route('/admin/rejeitar/<int:imovel_id>')
@admin_required
def rejeitar_imovel(imovel_id):
    conn = get_db()
    conn.execute("UPDATE imoveis SET status = 'rejeitado' WHERE id = ?", (imovel_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_imoveis'))

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    from atualiza_db import update_db_schema
    update_db_schema()

    conn = get_db()
    # MUDANÇA: Admin verificado por e-mail
    admin_user = conn.execute("SELECT * FROM usuarios WHERE email = 'admin@jtfimoveis.com.br'").fetchone()
    if not admin_user:
        # MUDANÇA: Inserção com campos email e is_admin. Senha: '123456'
        conn.execute(
            "INSERT INTO usuarios (username, password, nome, is_admin, email) VALUES (?, ?, ?, ?, ?)",
            ('admin@jtfimoveis.com.br', generate_password_hash('123456'), 'Administrador', 1, 'admin@jtfimoveis.com.br')
        )
        conn.commit()
        print("✅ Admin criado com sucesso!")
    else:
        print("ℹ️ Admin já existe.")
    conn.close()

    app.run(debug=True)