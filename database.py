import os
import sqlite3
from urllib.parse import urlparse, unquote

POSTGRES_URL = os.environ.get('POSTGRES_URL') or os.environ.get('DATABASE_URL')

def get_connection():
    if POSTGRES_URL:
        import pg8000.dbapi
        
        url_str = POSTGRES_URL
        if url_str.startswith('prisma://'):
            # Some prisma postgres strings have extra path queries, urlparse will handle them mostly, but scheme must be normalized
            url_str = url_str.replace('prisma://', 'postgres://', 1)
            
        parsed = urlparse(url_str)
        user = unquote(parsed.username) if parsed.username else 'postgres'
        password = unquote(parsed.password) if parsed.password else ''
        host = parsed.hostname or 'localhost'
        port = parsed.port or 5432
        dbname = parsed.path.lstrip('/') or 'postgres'
        
        # Construct ssl context if needed (pg8000 handles basic ssl upgrade automatically on AWS/Vercel)
        conn = pg8000.dbapi.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=dbname
        )
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
                bg_type TEXT DEFAULT 'image',
                bg_color_1 TEXT DEFAULT '#ffffff',
                bg_color_2 TEXT DEFAULT '#000000',
                bg_gradient_direction TEXT DEFAULT '135deg',
                bg_animation TEXT DEFAULT 'none',
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
                bg_type TEXT DEFAULT 'image',
                bg_color_1 TEXT DEFAULT '#ffffff',
                bg_color_2 TEXT DEFAULT '#000000',
                bg_gradient_direction TEXT DEFAULT '135deg',
                bg_animation TEXT DEFAULT 'none',
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

    # Update schema if columns missing (Migration)
    new_cols = {
        'bg_type': "TEXT DEFAULT 'image'",
        'bg_color_1': "TEXT DEFAULT '#ffffff'",
        'bg_color_2': "TEXT DEFAULT '#000000'",
        'bg_gradient_direction': "TEXT DEFAULT '135deg'",
        'bg_animation': "TEXT DEFAULT 'none'"
    }
    
    for col_name, col_def in new_cols.items():
        try:
            if db_type == 'postgres':
                cursor.execute(f"ALTER TABLE settings ADD COLUMN IF NOT EXISTS {col_name} {col_def.split(' ')[0]} DEFAULT {col_def.split(' DEFAULT ')[1]}")
            else:
                # SQLite doesn't support ADD COLUMN IF NOT EXISTS easily, so we check first
                cursor.execute(f"PRAGMA table_info(settings)")
                existing_cols = [row[1] for row in cursor.fetchall()]
                if col_name not in existing_cols:
                    cursor.execute(f"ALTER TABLE settings ADD COLUMN {col_name} {col_def}")
        except Exception as e:
            print(f"Error adding column {col_name}: {e}")

    # Seed Default Settings if not exists
    if db_type == 'postgres':
        cursor.execute("SELECT COUNT(*) FROM settings")
    else:
        cursor.execute("SELECT COUNT(*) as cnt FROM settings")
        
    row = cursor.fetchone()
    count = row[0] if row else 0
    
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
        cursor = conn.cursor()
    else:
        cursor = conn.cursor()
        
    cursor.execute(sql, params)
    
    columns = [col[0] for col in cursor.description]
    docs = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    
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

def update_settings(profile_name=None, profile_picture=None, background_picture=None, 
                    tiktok_url=None, instagram_url=None, facebook_url=None,
                    bg_type=None, bg_color_1=None, bg_color_2=None, 
                    bg_gradient_direction=None, bg_animation=None):
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
    if bg_type is not None:
        fields.append("bg_type = ?")
        params.append(bg_type)
    if bg_color_1 is not None:
        fields.append("bg_color_1 = ?")
        params.append(bg_color_1)
    if bg_color_2 is not None:
        fields.append("bg_color_2 = ?")
        params.append(bg_color_2)
    if bg_gradient_direction is not None:
        fields.append("bg_gradient_direction = ?")
        params.append(bg_gradient_direction)
    if bg_animation is not None:
        fields.append("bg_animation = ?")
        params.append(bg_animation)
        
    if fields:
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
