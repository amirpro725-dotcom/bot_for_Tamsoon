import sqlite3
import random

DB_PATH = "bot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        special_name TEXT UNIQUE,
        code INTEGER UNIQUE,
        coins INTEGER DEFAULT 100,
        spins INTEGER DEFAULT 1,
        wins INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0,
        last_daily_spin TEXT,
        joined INTEGER DEFAULT 0
    )""")
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def get_user_by_code(code):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE code=?", (code,))
    row = c.fetchone()
    conn.close()
    return row

def name_exists(name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE special_name=?", (name,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def create_user(user_id, special_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    while True:
        code = random.randint(1000, 9999)
        c.execute("SELECT 1 FROM users WHERE code=?", (code,))
        if not c.fetchone():
            break
    c.execute(
        "INSERT INTO users (user_id, special_name, code, coins, spins, joined) VALUES (?,?,?,?,?,1)",
        (user_id, special_name, code, 100, 1)
    )
    conn.commit()
    conn.close()
    return code

def update_user(user_id, **kwargs):
    if not kwargs:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for key, val in kwargs.items():
        c.execute(f"UPDATE users SET {key}=? WHERE user_id=?", (val, user_id))
    conn.commit()
    conn.close()

def update_user_by_code(code, **kwargs):
    if not kwargs:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for key, val in kwargs.items():
        c.execute(f"UPDATE users SET {key}=? WHERE code=?", (val, code))
    conn.commit()
    conn.close()

def set_joined(user_id):
    update_user(user_id, joined=1)

def is_joined(user_id):
    user = get_user(user_id)
    return user is not None and user[8] == 1
