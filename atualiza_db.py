import sqlite3

def update_db_schema(db_path='database.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Cria as tabelas caso não existam (sem perder dados)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nome TEXT,
            telefone TEXT,
            endereco TEXT
            -- is_admin, email, cpf serão adicionadas abaixo se não existirem
        )
    ''')

    cursor.execute('''
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
            contato TEXT
            -- fotos, status e operacao serão adicionados abaixo se não existirem
        )
    ''')

    # Verifica colunas da tabela imoveis
    cursor.execute("PRAGMA table_info(imoveis)")
    imoveis_cols = [col[1] for col in cursor.fetchall()]
    
    # Adicionando 'status'
    if 'status' not in imoveis_cols:
        cursor.execute("ALTER TABLE imoveis ADD COLUMN status TEXT DEFAULT 'pendente'")
        print("Coluna 'status' adicionada em 'imoveis'")
        
    # Adicionando 'fotos'
    if 'fotos' not in imoveis_cols:
        cursor.execute("ALTER TABLE imoveis ADD COLUMN fotos TEXT")
        print("Coluna 'fotos' adicionada em 'imoveis'")

    # Adicionando 'operacao'
    if 'operacao' not in imoveis_cols:
        cursor.execute("ALTER TABLE imoveis ADD COLUMN operacao TEXT DEFAULT 'compra'") 
        print("Coluna 'operacao' adicionada em 'imoveis'")
        
    # Verifica colunas da tabela usuarios
    cursor.execute("PRAGMA table_info(usuarios)")
    usuarios_cols = [col[1] for col in cursor.fetchall()]
    
    # Adicionando 'is_admin'
    if 'is_admin' not in usuarios_cols:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN is_admin INTEGER DEFAULT 0")
        print("Coluna 'is_admin' adicionada em 'usuarios'")

    # === NOVAS COLUNAS PARA USUARIOS ===
    # Adicionando 'email' (usado para login)
    if 'email' not in usuarios_cols:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN email TEXT")
        print("Coluna 'email' adicionada em 'usuarios'")
        # Atualiza a coluna 'email' com os valores existentes de 'username'
        cursor.execute("UPDATE usuarios SET email = username WHERE email IS NULL")
        
    # Adicionando 'cpf'
    if 'cpf' not in usuarios_cols:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN cpf TEXT")
        print("Coluna 'cpf' adicionada em 'usuarios'")
    # ===================================
        
    # Garante que imóveis pendentes estejam atualizados
    cursor.execute("UPDATE imoveis SET status = 'pendente' WHERE status IS NULL OR status = ''")
    
    # Atualiza 'operacao' para 'compra' onde for nulo ou vazio
    cursor.execute("UPDATE imoveis SET operacao = 'compra' WHERE operacao IS NULL OR operacao = ''")

    conn.commit()
    conn.close()
    print("Atualização do banco finalizada com sucesso.")

if __name__ == "__main__":
    update_db_schema()