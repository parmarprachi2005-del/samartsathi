from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from database import *
import sqlite3
import os
import socket
import json
import uuid
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from functools import wraps

# ============ INITIALIZE APP ============
app = Flask(__name__)
app.secret_key = 'smartsathi_super_secret_key_2025'

# ============ UPLOAD CONFIGURATION ============
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'txt'}

# Create folders if not exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('instance', exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============ DATABASE SETUP ============
DATABASE = 'instance/smartsathi.db'

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Feedback table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            feedback TEXT,
            rating INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Visitors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT,
            page_visited TEXT,
            visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Uploads table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            original_name TEXT,
            file_type TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Referrals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            refer_code TEXT UNIQUE,
            referred_users TEXT DEFAULT '[]',
            points INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User activities for points
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            activity TEXT,
            points INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User badges
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            badge_name TEXT,
            badge_icon TEXT,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized!")

def create_admin_user():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = 'admin@smartsathi.com'")
    if not cursor.fetchone():
        import hashlib
        hashed = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, email, password, is_admin) VALUES (?, ?, ?, ?)",
                      ('Administrator', 'admin@smartsathi.com', hashed, 1))
        conn.commit()
        print("✅ Admin created! (admin@smartsathi.com / admin123)")
    conn.close()

# Initialize database
init_db()
create_admin_user()

# ============ HELPER FUNCTIONS ============

def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, email, password, is_admin=0):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, email, password, is_admin) VALUES (?, ?, ?, ?)",
                      (username, email, hash_password(password), is_admin))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def check_user(email, password):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, is_admin FROM users WHERE email = ? AND password = ?",
                      (email, hash_password(password)))
        user = cursor.fetchone()
        conn.close()
        return user
    except:
        return None

def get_user_by_id(user_id):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, is_admin FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user
    except:
        return None

def get_all_users():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, is_admin, created_at FROM users ORDER BY id DESC")
        users = cursor.fetchall()
        conn.close()
        return users
    except:
        return []

def delete_user(user_id):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_user_count():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def add_feedback(name, email, feedback, rating=0):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO feedback (name, email, feedback, rating) VALUES (?, ?, ?, ?)",
                      (name, email, feedback, rating))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_all_feedback():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, feedback, rating, created_at FROM feedback ORDER BY id DESC")
        feedbacks = cursor.fetchall()
        conn.close()
        return feedbacks
    except:
        return []

def get_feedback_count():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM feedback")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def add_visitor(ip_address, page_visited):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO visitors (ip_address, page_visited) VALUES (?, ?)",
                      (ip_address, page_visited))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_visitor_count():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM visitors")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def get_today_visitor_count():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM visitors WHERE DATE(visited_at) = ?", (today,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

# ============ TRACK VISITOR ============

@app.before_request
def track_visitor():
    if request.endpoint and request.endpoint != 'static':
        if request.endpoint not in ['login', 'signup', 'get_url', 'generate_qr', 'static', 'get_visitor_count', 'api.submit_feedback', 'logout', 'api.add_points', 'api.claim_referral']:
            if not request.endpoint.startswith('admin'):
                add_visitor(request.remote_addr, request.endpoint)

# ============ MAIN ROUTES ============

@app.route('/')
def index():
    return render_template('index.html', logged_in='user_id' in session)

@app.route('/get_url')
def get_url():
    return jsonify({"url": f"http://{get_local_ip()}:5000"})

@app.route('/generate_qr')
def generate_qr():
    return render_template('qr_download.html', url=f"http://{get_local_ip()}:5000")

@app.route('/get_visitor_count')
def get_visitor_count_api():
    return jsonify({"count": get_visitor_count()})

# ============ LOGIN / SIGNUP ============

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = check_user(email, password)
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['email'] = user[2]
            session['is_admin'] = user[3] if len(user) > 3 else 0
            if session.get('is_admin'):
                flash(f'Welcome Admin {user[1]}! 🛡️', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash(f'Welcome back, {user[1]}! 🎉', 'success')
                return redirect(url_for('index'))
        else:
            flash('Invalid email or password! ❌', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if add_user(username, email, password, is_admin=0):
            flash('Account created successfully! Please login. ✅', 'success')
            return redirect(url_for('login'))
        else:
            flash('Email already exists! ⚠️', 'error')
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully! 👋', 'info')
    return redirect(url_for('index'))

# ============ DASHBOARD ============

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login first! 🔐', 'warning')
        return redirect(url_for('login'))
    user = get_user_by_id(session['user_id'])
    if user:
        username = user[1]
    else:
        username = session.get('username', 'User')
    return render_template('dashboard.html', username=username)

# ============ ADMIN PANEL ============

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Admin access required! 🔒', 'error')
        return redirect(url_for('login'))
    stats = {
        'total_users': get_user_count(),
        'total_feedback': get_feedback_count(),
        'total_visitors': get_visitor_count(),
        'today_visitors': get_today_visitor_count(),
        'total_products': 21,
        'total_services': 21
    }
    return render_template('admin_dashboard.html', username=session['username'], stats=stats)

@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Admin access required! 🔒', 'error')
        return redirect(url_for('login'))
    users = get_all_users()
    return render_template('admin_users.html', users=users)

@app.route('/admin/user/delete/<int:user_id>')
def admin_delete_user(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Admin access required! 🔒', 'error')
        return redirect(url_for('login'))
    if user_id == session['user_id']:
        flash('You cannot delete yourself! ⚠️', 'error')
    else:
        delete_user(user_id)
        flash('User deleted! ✅', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/feedback')
def admin_feedback():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Admin access required! 🔒', 'error')
        return redirect(url_for('login'))
    feedbacks = get_all_feedback()
    return render_template('admin_feedback.html', feedbacks=feedbacks)

@app.route('/api/submit_feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    if add_feedback(data.get('name', 'Anonymous'), data.get('email', ''), data.get('feedback', ''), data.get('rating', 0)):
        return jsonify({"success": True})
    return jsonify({"success": False})

# ============ SERVICE PAGES ============

@app.route('/shopping')
def shopping(): return render_template('shopping.html', logged_in='user_id' in session)

@app.route('/food')
def food(): return render_template('food.html', logged_in='user_id' in session)

@app.route('/study')
def study(): return render_template('study.html', logged_in='user_id' in session)

@app.route('/farming')
def farming(): return render_template('farming.html', logged_in='user_id' in session)

@app.route('/medicine')
def medicine(): return render_template('medicine.html', logged_in='user_id' in session)

@app.route('/skincare')
def skincare(): return render_template('skincare.html', logged_in='user_id' in session)

@app.route('/entertainment')
def entertainment(): return render_template('entertainment.html', logged_in='user_id' in session)

@app.route('/music')
def music(): return render_template('music.html', logged_in='user_id' in session)

@app.route('/gaming')
def gaming(): return render_template('gaming.html', logged_in='user_id' in session)

@app.route('/travel')
def travel(): return render_template('travel.html', logged_in='user_id' in session)

@app.route('/hotels')
def hotels(): return render_template('hotels.html', logged_in='user_id' in session)

@app.route('/finance')
def finance(): return render_template('finance.html', logged_in='user_id' in session)

@app.route('/news')
def news(): return render_template('news.html', logged_in='user_id' in session)

@app.route('/sports')
def sports(): return render_template('sports.html', logged_in='user_id' in session)

@app.route('/jobs')
def jobs(): return render_template('jobs.html', logged_in='user_id' in session)

@app.route('/fitness')
def fitness(): return render_template('fitness.html', logged_in='user_id' in session)

@app.route('/tools')
def tools(): return render_template('tools.html', logged_in='user_id' in session)

@app.route('/photo')
def photo(): return render_template('photo.html', logged_in='user_id' in session)

@app.route('/social')
def social(): return render_template('social.html', logged_in='user_id' in session)

@app.route('/delivery')
def delivery(): return render_template('delivery.html', logged_in='user_id' in session)

@app.route('/books')
def books(): return render_template('books.html', logged_in='user_id' in session)

# ============ NEW FEATURE ROUTES ============

# 1. File Upload
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = str(uuid.uuid4())[:8] + '_' + filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            user_id = session.get('user_id', 0)
            cursor.execute(
                "INSERT INTO uploads (user_id, filename, original_name, file_type) VALUES (?, ?, ?, ?)",
                (user_id, unique_filename, filename, file.filename.rsplit('.', 1)[1].lower())
            )
            conn.commit()
            conn.close()
            
            flash(f'✅ File "{filename}" uploaded successfully!', 'success')
            
            # Add points for upload
            if user_id:
                add_points_to_user(user_id, 'Uploaded file', 10)
        else:
            flash('❌ File type not allowed!', 'error')
        
        return redirect(url_for('upload_file'))
    
    return render_template('upload.html', logged_in='user_id' in session)

# 2. PDF Generator
@app.route('/pdf_generator')
def pdf_generator():
    return render_template('pdf_generator.html', logged_in='user_id' in session)

# 3. Referral System
@app.route('/referral')
def referral():
    user_id = session.get('user_id')
    refer_code = None
    referral_points = 0
    referral_count = 0
    
    if user_id:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM referrals WHERE user_id = ?", (user_id,))
        ref = cursor.fetchone()
        
        if not ref:
            refer_code = str(user_id) + str(int(datetime.now().timestamp()))[-6:]
            cursor.execute(
                "INSERT INTO referrals (user_id, refer_code, points) VALUES (?, ?, ?)",
                (user_id, refer_code, 0)
            )
            conn.commit()
        else:
            refer_code = ref[2]
            referral_points = ref[4]
            referred_users = json.loads(ref[3]) if ref[3] else []
            referral_count = len(referred_users)
        
        conn.close()
    
    return render_template('referral.html', refer_code=refer_code, points=referral_points, count=referral_count, logged_in='user_id' in session)

@app.route('/api/claim_referral', methods=['POST'])
def claim_referral():
    data = request.json
    refer_code = data.get('refer_code')
    new_user_id = session.get('user_id')
    
    if not new_user_id:
        return jsonify({"success": False, "message": "Please login first"})
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM referrals WHERE refer_code = ?", (refer_code,))
    ref = cursor.fetchone()
    
    if ref:
        referrer_id = ref[1]
        if referrer_id == new_user_id:
            conn.close()
            return jsonify({"success": False, "message": "Cannot refer yourself!"})
        
        referred_users = json.loads(ref[3]) if ref[3] else []
        if new_user_id in referred_users:
            conn.close()
            return jsonify({"success": False, "message": "Already referred!"})
        
        referred_users.append(new_user_id)
        new_points = ref[4] + 50
        
        cursor.execute(
            "UPDATE referrals SET referred_users = ?, points = ? WHERE id = ?",
            (json.dumps(referred_users), new_points, ref[0])
        )
        
        cursor.execute("SELECT * FROM referrals WHERE user_id = ?", (new_user_id,))
        new_ref = cursor.fetchone()
        if new_ref:
            cursor.execute(
                "UPDATE referrals SET points = points + 25 WHERE user_id = ?",
                (new_user_id,)
            )
        
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Referral claimed! +50 points for you, +25 for your friend!"})
    
    conn.close()
    return jsonify({"success": False, "message": "Invalid referral code"})

# 4. Gamification
@app.route('/gamification')
def gamification():
    user_id = session.get('user_id')
    user_points = 0
    badges = []
    
    if user_id:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT SUM(points) FROM user_activities WHERE user_id = ?", (user_id,))
        total = cursor.fetchone()[0]
        user_points = total if total else 0
        
        cursor.execute("SELECT badge_name, badge_icon, earned_at FROM user_badges WHERE user_id = ?", (user_id,))
        badges = cursor.fetchall()
        
        conn.close()
    
    return render_template('gamification.html', points=user_points, badges=badges, logged_in='user_id' in session)

def add_points_to_user(user_id, activity, points):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_activities (user_id, activity, points) VALUES (?, ?, ?)",
        (user_id, activity, points)
    )
    
    cursor.execute("SELECT SUM(points) FROM user_activities WHERE user_id = ?", (user_id,))
    total_points = cursor.fetchone()[0] or 0
    
    badges_to_add = []
    if total_points >= 100:
        badges_to_add.append(("🎯 Explorer", "Started your journey"))
    if total_points >= 500:
        badges_to_add.append(("⭐ Star User", "500+ points earned"))
    if total_points >= 1000:
        badges_to_add.append(("👑 Legend", "1000+ points earned"))
    
    for badge_name, badge_desc in badges_to_add:
        cursor.execute("SELECT * FROM user_badges WHERE user_id = ? AND badge_name = ?", (user_id, badge_name))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO user_badges (user_id, badge_name, badge_icon) VALUES (?, ?, ?)",
                (user_id, badge_name, badge_desc)
            )
    
    conn.commit()
    conn.close()

@app.route('/api/add_points', methods=['POST'])
def add_points_api():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Login required"})
    
    data = request.json
    activity = data.get('activity', 'Unknown')
    points = data.get('points', 0)
    
    add_points_to_user(user_id, activity, points)
    
    return jsonify({"success": True, "points": points})

# 5. Location-based Features
@app.route('/location')
def location():
    return render_template('location.html', logged_in='user_id' in session)

@app.route('/api/nearby_places')
def nearby_places():
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    type = request.args.get('type', 'hotels')
    
    places = {
        'hotels': [
            {"name": "Grand Hotel", "distance": "0.5 km", "rating": 4.5, "price": "₹2000/night"},
            {"name": "Sunset Resort", "distance": "1.2 km", "rating": 4.2, "price": "₹3500/night"},
            {"name": "Budget Inn", "distance": "0.8 km", "rating": 3.8, "price": "₹1200/night"}
        ],
        'restaurants': [
            {"name": "Spice Garden", "distance": "0.3 km", "rating": 4.7, "price": "₹500/meal"},
            {"name": "Food Paradise", "distance": "0.6 km", "rating": 4.3, "price": "₹350/meal"},
            {"name": "Street Food Hub", "distance": "0.4 km", "rating": 4.1, "price": "₹150/meal"}
        ],
        'shops': [
            {"name": "City Mall", "distance": "1.0 km", "rating": 4.4, "price": "Shopping Mall"},
            {"name": "Local Market", "distance": "0.7 km", "rating": 4.0, "price": "Market"},
            {"name": "Electronics Hub", "distance": "1.5 km", "rating": 4.6, "price": "Electronics"}
        ],
        'farming': [
            {"name": "Krishi Mandi", "distance": "2.0 km", "rating": 4.2, "price": "Fertilizer available"},
            {"name": "Seed Bank", "distance": "1.8 km", "rating": 4.5, "price": "High quality seeds"},
            {"name": "Agri Clinic", "distance": "3.0 km", "rating": 4.3, "price": "Expert advice available"}
        ]
    }
    
    return jsonify(places.get(type, places['hotels']))

# 6. QR Code Tool
@app.route('/qr_tool')
def qr_tool():
    return render_template('qr_tool.html', logged_in='user_id' in session)

# 7. Price Compare Tool
@app.route('/price_compare')
def price_compare():
    return render_template('price_compare.html', logged_in='user_id' in session)

# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# ============ RUN SERVER ============

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 SmartSathi Server Started!")
    print("="*60)
    print(f"📍 Local Access:    http://127.0.0.1:5000")
    print(f"📱 Network Access:  http://{get_local_ip()}:5000")
    print("="*60)
    print(f"👑 Admin Login:     admin@smartsathi.com / admin123")
    print(f"📁 New Features:    Upload, PDF, Referral, Rewards, Location, QR, Price Compare")
    print("="*60)
    app.run(debug=True, host='0.0.0.0', port=5000)