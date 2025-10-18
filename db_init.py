import sqlite3

DB = "users.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()
    print("Initialized database:", DB)

if __name__ == "__main__":
    init_db()
