import sqlite3
import hashlib
import os
from datetime import datetime

# Create instance folder if not exists
if not os.path.exists('instance'):
    os.makedirs('instance')

DATABASE = 'instance/smartsathi.db'

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Initialize all database tables"""
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
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

def create_admin_user():
    """Create default admin user if not exists"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = 'admin@smartsathi.com'")
    admin = cursor.fetchone()
    
    if not admin:
        hashed_pwd = hash_password('admin123')
        cursor.execute('''
            INSERT INTO users (username, email, password, is_admin) 
            VALUES (?, ?, ?, ?)
        ''', ('Administrator', 'admin@smartsathi.com', hashed_pwd, 1))
        conn.commit()
        print("✅ Admin user created!")
        print("   Email: admin@smartsathi.com")
        print("   Password: admin123")
    else:
        print("ℹ️ Admin user already exists")
    
    conn.close()

def get_admin_user():
    """Get admin user details"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE is_admin = 1 LIMIT 1")
        admin = cursor.fetchone()
        conn.close()
        return admin
    except:
        return None

# ============ USER FUNCTIONS ============

def add_user(username, email, password, is_admin=0):
    """Add new user to database"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        hashed_pwd = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, email, password, is_admin) 
            VALUES (?, ?, ?, ?)
        ''', (username, email, hashed_pwd, is_admin))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def check_user(email, password):
    """Verify user credentials"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        hashed_pwd = hash_password(password)
        cursor.execute('''
            SELECT id, username, email, is_admin 
            FROM users 
            WHERE email = ? AND password = ?
        ''', (email, hashed_pwd))
        user = cursor.fetchone()
        conn.close()
        return user
    except:
        return None

def get_user_by_id(user_id):
    """Get user by ID"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, email, is_admin, created_at 
            FROM users 
            WHERE id = ?
        ''', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user
    except:
        return None

def get_all_users():
    """Get all users for admin panel"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, email, is_admin, created_at 
            FROM users 
            ORDER BY id DESC
        ''')
        users = cursor.fetchall()
        conn.close()
        return users
    except:
        return []

def delete_user(user_id):
    """Delete user by ID"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def update_user(user_id, username, email, is_admin):
    """Update user information"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET username = ?, email = ?, is_admin = ? 
            WHERE id = ?
        ''', (username, email, is_admin, user_id))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_user_count():
    """Get total number of users"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

# ============ FEEDBACK FUNCTIONS ============

def add_feedback(name, email, feedback, rating=0):
    """Add user feedback"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO feedback (name, email, feedback, rating) 
            VALUES (?, ?, ?, ?)
        ''', (name, email, feedback, rating))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_all_feedback():
    """Get all feedback for admin"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, email, feedback, rating, created_at 
            FROM feedback 
            ORDER BY id DESC
        ''')
        feedbacks = cursor.fetchall()
        conn.close()
        return feedbacks
    except:
        return []

def get_feedback_count():
    """Get total feedback count"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM feedback")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

# ============ VISITOR FUNCTIONS ============

def add_visitor(ip_address, page_visited):
    """Track visitor"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO visitors (ip_address, page_visited) 
            VALUES (?, ?)
        ''', (ip_address, page_visited))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_visitor_count():
    """Get total visitor count"""
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
    """Get today's visitor count"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT COUNT(*) FROM visitors 
            WHERE DATE(visited_at) = ?
        ''', (today,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0