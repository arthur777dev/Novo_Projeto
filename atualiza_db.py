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
            -- is_admin será adicionada abaixo se não existir
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
            -- fotos e status serão adicionados abaixo se não existirem
        )
    ''')

    # Verifica colunas da tabela imoveis
    cursor.execute("PRAGMA table_info(imoveis)")
    imoveis_cols = [col[1] for col in cursor.fetchall()]
    if 'status' not in imoveis_cols:
        cursor.execute("ALTER TABLE imoveis ADD COLUMN status TEXT DEFAULT 'pendente'")
        print("Coluna 'status' adicionada em 'imoveis'")
    if 'fotos' not in imoveis_cols:
        cursor.execute("ALTER TABLE imoveis ADD COLUMN fotos TEXT")
        print("Coluna 'fotos' adicionada em 'imoveis'")

    # Verifica colunas da tabela usuarios
    cursor.execute("PRAGMA table_info(usuarios)")
    usuarios_cols = [col[1] for col in cursor.fetchall()]
    if 'is_admin' not in usuarios_cols:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN is_admin INTEGER DEFAULT 0")
        print("Coluna 'is_admin' adicionada em 'usuarios'")

    # Garante que imóveis pendentes estejam atualizados
    cursor.execute("UPDATE imoveis SET status = 'pendente' WHERE status IS NULL OR status = ''")

    conn.commit()
    conn.close()
    print("Atualização do banco finalizada com sucesso.")

if __name__ == "__main__":
    update_db_schema()