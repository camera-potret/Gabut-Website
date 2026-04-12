from flask import Flask, render_template, request, redirect, session, url_for, flash
import os
import base64
import uuid
from werkzeug.utils import secure_filename
import database
import requests

IMGBB_API_KEY = os.environ.get('IMGBB_API_KEY')

app = Flask(__name__)
app.secret_key = 'super_secret_key_make_sure_to_change_for_production'

# Ensure upload directory exists
UPLOAD_FOLDER = os.path.join('static', 'uploads')
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except OSError:
    UPLOAD_FOLDER = '/tmp/uploads'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Hardcoded Admin credentials
ADMIN_USER = 'koktolol'
ADMIN_PASS = 'bibintolol64'

# Initialize DB on start
with app.app_context():
    database.init_db()

@app.route('/static/uploads/<filename>')
def serve_uploads(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def index():
    settings = database.get_settings()
    links = database.get_links()
    return render_template('index.html', settings=settings, links=links)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_logged_in'):
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['admin_logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah!', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
        
    settings = database.get_settings()
    links = database.get_links()
    return render_template('dashboard.html', settings=settings, links=links)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
        
    profile_name = request.form.get('profile_name')
    
    # Handle Profile Picture
    profile_picture_name = None
    cropped_b64 = request.form.get('cropped_profile_b64')
    
    if cropped_b64:
        # Pindah ke database! Teks Data URI `cropped_b64` disimpan langsung di dalam cloud.
        profile_picture_name = cropped_b64
    else:
        profile_picture_file = request.files.get('profile_picture')
        if profile_picture_file and allowed_file(profile_picture_file.filename):
            file_ext = profile_picture_file.filename.rsplit('.', 1)[1].lower()
            b64_img = base64.b64encode(profile_picture_file.read()).decode('utf-8')
            profile_picture_name = f"data:image/{file_ext};base64,{b64_img}"
        
    # Handle Background Picture
    background_picture_file = request.files.get('background_picture')
    background_picture_name = None
    if background_picture_file and allowed_file(background_picture_file.filename):
        file_ext = background_picture_file.filename.rsplit('.', 1)[1].lower()
        b64_img = base64.b64encode(background_picture_file.read()).decode('utf-8')
        background_picture_name = f"data:image/{file_ext};base64,{b64_img}"
        
    tiktok_url = request.form.get('tiktok_url')
    instagram_url = request.form.get('instagram_url')
    facebook_url = request.form.get('facebook_url')
    
    # Update DB
    database.update_settings(
        profile_name=profile_name if profile_name else None,
        profile_picture=profile_picture_name,
        background_picture=background_picture_name,
        tiktok_url=tiktok_url,
        instagram_url=instagram_url,
        facebook_url=facebook_url
    )
    
    flash('Profil berhasil diperbarui!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/add_link', methods=['POST'])
def add_link():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
        
    title = request.form.get('title')
    url = request.form.get('url')
    
    if title and url:
        database.add_link(title, url)
        flash('Link berhasil ditambahkan!', 'success')
        
    return redirect(url_for('dashboard'))

@app.route('/delete_link/<string:link_id>')
def delete_link(link_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
        
    database.delete_link(link_id)
    flash('Link berhasil dihapus!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/reorder_links', methods=['POST'])
def reorder_links():
    if not session.get('admin_logged_in'):
        return {"status": "error", "message": "Unauthorized"}, 401
        
    data = request.get_json()
    order = data.get('order', [])
    
    database.update_links_order(order)
    
    return {"status": "success"}

if __name__ == '__main__':
    app.run(debug=True, port=5000)
