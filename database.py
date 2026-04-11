import sqlite3
import os

DB_PATH = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Create Settings Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY DEFAULT 1,
            profile_name TEXT NOT NULL,
            profile_picture TEXT,
            background_picture TEXT
        )
    ''')
    
    # Create Links Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            order_num INTEGER DEFAULT 0
        )
    ''')

    # Seed Default Settings if not exists
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM settings')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO settings (id, profile_name, profile_picture, background_picture)
            VALUES (1, 'Camrta_potret_', '', '')
        ''')
    
    conn.commit()
    conn.close()

def get_settings():
    conn = get_db_connection()
    settings = conn.execute('SELECT * FROM settings WHERE id = 1').fetchone()
    conn.close()
    return settings

def update_settings(profile_name=None, profile_picture=None, background_picture=None):
    conn = get_db_connection()
    if profile_name is not None:
        conn.execute('UPDATE settings SET profile_name = ? WHERE id = 1', (profile_name,))
    if profile_picture is not None:
        conn.execute('UPDATE settings SET profile_picture = ? WHERE id = 1', (profile_picture,))
    if background_picture is not None:
        conn.execute('UPDATE settings SET background_picture = ? WHERE id = 1', (background_picture,))
    conn.commit()
    conn.close()

def get_links():
    conn = get_db_connection()
    links = conn.execute('SELECT * FROM links ORDER BY order_num ASC, id DESC').fetchall()
    conn.close()
    return links

def add_link(title, url):
    conn = get_db_connection()
    conn.execute('INSERT INTO links (title, url) VALUES (?, ?)', (title, url))
    conn.commit()
    conn.close()

def delete_link(link_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM links WHERE id = ?', (link_id,))
    conn.commit()
    conn.close()

def update_link(link_id, title, url):
    conn = get_db_connection()
    conn.execute('UPDATE links SET title = ?, url = ? WHERE id = ?', (title, url, link_id))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
