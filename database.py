import os

POSTGRES_URL = os.environ.get('POSTGRES_URL')

if POSTGRES_URL:
    import psycopg2
    from psycopg2.extras import RealDictCursor
else:
    import sqlite3

def get_connection():
    if POSTGRES_URL:
        conn = psycopg2.connect(POSTGRES_URL)
        return conn, 'postgres'
    else:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        return conn, 'sqlite'

def init_db():
    conn, db_type = get_connection()
    cursor = conn.cursor()
    
    if db_type == 'postgres':
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id SERIAL PRIMARY KEY,
                profile_name TEXT NOT NULL,
                profile_picture TEXT,
                background_picture TEXT,
                tiktok_url TEXT,
                instagram_url TEXT,
                facebook_url TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS links (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                order_num INTEGER DEFAULT 0
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY DEFAULT 1,
                profile_name TEXT NOT NULL,
                profile_picture TEXT,
                background_picture TEXT,
                tiktok_url TEXT,
                instagram_url TEXT,
                facebook_url TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                order_num INTEGER DEFAULT 0
            )
        ''')

    # Seed Default Settings if not exists
    cursor.execute("SELECT COUNT(*) as cnt FROM settings")
    row = cursor.fetchone()
    count = row['cnt'] if isinstance(row, dict) else row[0]
    
    if count == 0:
        if db_type == 'postgres':
            cursor.execute('''
                INSERT INTO settings (profile_name, profile_picture, background_picture, tiktok_url, instagram_url, facebook_url)
                VALUES ('Camrta_potret_', '', '', '', '', '')
            ''')
        else:
            cursor.execute('''
                INSERT INTO settings (id, profile_name, profile_picture, background_picture, tiktok_url, instagram_url, facebook_url)
                VALUES (1, 'Camrta_potret_', '', '', '', '', '')
            ''')
    
    conn.commit()
    conn.close()

def query_select(sql, params=()):
    conn, db_type = get_connection()
    if db_type == 'postgres':
        sql = sql.replace('?', '%s')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
    else:
        cursor = conn.cursor()
        
    cursor.execute(sql, params)
    docs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # ensure 'id' is a string for compatibility with mongo-based code if needed
    for doc in docs:
        if 'id' in doc:
            doc['id'] = str(doc['id'])
    return docs

def query_execute(sql, params=()):
    conn, db_type = get_connection()
    if db_type == 'postgres':
        sql = sql.replace('?', '%s')
        
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    conn.close()

def get_settings():
    docs = query_select("SELECT * FROM settings LIMIT 1")
    return docs[0] if docs else None

def update_settings(profile_name=None, profile_picture=None, background_picture=None, tiktok_url=None, instagram_url=None, facebook_url=None):
    fields = []
    params = []
    
    if profile_name is not None:
        fields.append("profile_name = ?")
        params.append(profile_name)
    if profile_picture is not None:
        fields.append("profile_picture = ?")
        params.append(profile_picture)
    if background_picture is not None:
        fields.append("background_picture = ?")
        params.append(background_picture)
    if tiktok_url is not None:
        fields.append("tiktok_url = ?")
        params.append(tiktok_url)
    if instagram_url is not None:
        fields.append("instagram_url = ?")
        params.append(instagram_url)
    if facebook_url is not None:
        fields.append("facebook_url = ?")
        params.append(facebook_url)
        
    if fields:
        # Assuming single row settings
        sql = "UPDATE settings SET " + ", ".join(fields)
        query_execute(sql, tuple(params))

def get_links():
    return query_select("SELECT * FROM links ORDER BY order_num ASC, id DESC")

def add_link(title, url):
    query_execute("INSERT INTO links (title, url, order_num) VALUES (?, ?, 0)", (title, url))

def delete_link(link_id):
    query_execute("DELETE FROM links WHERE id = ?", (int(link_id),))

def update_link(link_id, title, url):
    query_execute("UPDATE links SET title = ?, url = ? WHERE id = ?", (title, url, int(link_id)))

def update_links_order(order_list):
    for index, str_id in enumerate(order_list):
        query_execute("UPDATE links SET order_num = ? WHERE id = ?", (index, int(str_id)))

if __name__ == '__main__':
    init_db()
