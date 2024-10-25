# auth.py
import sqlite3

def init_db():
    conn = sqlite3.connect('users.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
    conn.commit()

def register_user(username, password):
    conn = sqlite3.connect('users.db')
    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()

def login_user(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    return cursor.fetchone()
