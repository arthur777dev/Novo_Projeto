import sqlite3

conn = sqlite3.connect("database.db")

try:
    conn.execute("ALTER TABLE imoveis ADD COLUMN endereco TEXT")
    conn.execute("ALTER TABLE imoveis ADD COLUMN tipo TEXT")
    conn.execute("ALTER TABLE imoveis ADD COLUMN area REAL")
    conn.execute("ALTER TABLE imoveis ADD COLUMN quartos INTEGER")
    conn.execute("ALTER TABLE imoveis ADD COLUMN banheiros INTEGER")
    conn.execute("ALTER TABLE imoveis ADD COLUMN vagas INTEGER")
    conn.execute("ALTER TABLE imoveis ADD COLUMN caracteristicas TEXT")
    conn.execute("ALTER TABLE imoveis ADD COLUMN contato TEXT")
except sqlite3.OperationalError:
    print("Algumas colunas já existem. Prosseguindo...")

conn.commit()
conn.close()
print("Banco atualizado com sucesso.")
