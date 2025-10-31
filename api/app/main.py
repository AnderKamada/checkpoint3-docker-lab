import os
import time
import psycopg2
from fastapi import FastAPI
import uvicorn

# Lê envs passadas pelo docker-compose
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "appdb")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "apppass")

app = FastAPI(title="Checkpoint 3 - DevOps & Cloud", version="1.0.0")

def get_conn(retries=10, delay=2):
    """Tenta conectar no Postgres com retries (começo do container)."""
    for _ in range(retries):
        try:
            return psycopg2.connect(
                host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                user=DB_USER, password=DB_PASSWORD
            )
        except Exception:
            time.sleep(delay)
    raise RuntimeError("Não consegui conectar no Postgres.")

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.on_event("startup")
def on_startup():
    # Garante que a tabela exista
    init_db()
    # Demonstra o volume COMPARTILHADO: grava um arquivo em /app/shared
    os.makedirs("/app/shared", exist_ok=True)
    with open("/app/shared/hello.txt", "w", encoding="utf-8") as f:
        f.write("Arquivo gerado pela API para provar o volume compartilhado.\n")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/users/{name}")
def create_user(name: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO users(name) VALUES (%s) RETURNING id;", (name,))
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"id": new_id, "name": name}

@app.get("/users")
def list_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM users ORDER BY id;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "name": r[1]} for r in rows]

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=5111)
