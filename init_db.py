import sqlite3
from werkzeug.security import generate_password_hash

# Conexão com banco
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Adiciona coluna status se não existir
try:
    cursor.execute("ALTER TABLE imoveis ADD COLUMN status TEXT DEFAULT 'pendente'")
    print("Coluna 'status' adicionada com sucesso.")
except sqlite3.OperationalError:
    print("Coluna 'status' já existe.")

# Atualiza imóveis sem status
cursor.execute("UPDATE imoveis SET status = 'pendente' WHERE status IS NULL OR status = ''")

# Cria usuário admin (troque usuário e senha conforme desejar)
username = "admin"
password = "123456"
nome = "Administrador"
telefone = "0000-0000"
endereco = "Endereço Admin"
hashed_password = generate_password_hash(password)

try:
    cursor.execute("""
    INSERT INTO usuarios (username, password, nome, telefone, endereco, is_admin)
    VALUES (?, ?, ?, ?, ?, 1)
    """, (username, hashed_password, nome, telefone, endereco))
    print(f"Usuário admin '{username}' criado com sucesso.")
except sqlite3.IntegrityError:
    print("Usuário admin já existe.")

conn.commit()
conn.close()
