import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "predictiveengine.db")

def get_db():
    """Get database connection"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            engine_type TEXT NOT NULL,
            health_score INTEGER NOT NULL,
            risk_level TEXT NOT NULL,
            failure_prob REAL NOT NULL,
            safe_days INTEGER NOT NULL,
            rpm REAL NOT NULL,
            torque REAL NOT NULL,
            wear REAL NOT NULL,
            air_temp REAL NOT NULL,
            process_temp REAL NOT NULL,
            fail_prediction INTEGER NOT NULL,
            user_id INTEGER
        )
    ''')
    
    # Check if user_id column exists, if not, add it (migration for existing DB)
    cursor.execute("PRAGMA table_info(predictions)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'user_id' not in columns:
        cursor.execute("ALTER TABLE predictions ADD COLUMN user_id INTEGER")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    # Check if email column exists, if not, add it (migration for existing DB)
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'email' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
    
    conn.commit()
    conn.close()


def save_prediction(form_data, result, user_id=None):
    """Save prediction to database"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO predictions (
            created_at, engine_type, health_score, risk_level, 
            failure_prob, safe_days, rpm, torque, wear, 
            air_temp, process_temp, fail_prediction, user_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        result['time'],
        result['engine'],
        result['health'],
        result['risk'],
        result['prob'],
        result['days'],
        result['rpm'],
        result['torque'],
        result['wear'],
        float(form_data.get('air_temp', 298.5)),
        float(form_data.get('process_temp', 309)),
        result['fail'],
        user_id
    ))
    
    conn.commit()
    conn.close()


def get_predictions(user_id=None):
    """Get predictions from database (optionally filtered by user_id)"""
    conn = get_db()
    cursor = conn.cursor()
    
    if user_id is not None:
        cursor.execute('SELECT * FROM predictions WHERE user_id = ? ORDER BY id DESC', (user_id,))
    else:
        cursor.execute('SELECT * FROM predictions ORDER BY id DESC')
        
    rows = cursor.fetchall()
    conn.close()
    
    predictions = []
    for row in rows:
        predictions.append({
            'id': row['id'],
            'created_at': row['created_at'],
            'engine_type': row['engine_type'],
            'health_score': row['health_score'],
            'risk_level': row['risk_level'],
            'failure_prob': row['failure_prob'],
            'safe_days': row['safe_days'],
            'rpm': row['rpm'],
            'torque': row['torque'],
            'wear': row['wear'],
            'air_temp': row['air_temp'],
            'process_temp': row['process_temp'],
            'fail_prediction': row['fail_prediction']
        })
    
    return predictions


def get_stats(user_id=None):
    """Get database statistics (optionally filtered by user_id)"""
    conn = get_db()
    cursor = conn.cursor()
    
    if user_id is not None:
        cursor.execute('SELECT COUNT(*) as count FROM predictions WHERE user_id = ?', (user_id,))
        total = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM predictions WHERE risk_level = ? AND user_id = ?', ('safe', user_id))
        healthy = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM predictions WHERE risk_level = ? AND user_id = ?', ('danger', user_id))
        critical = cursor.fetchone()['count']
    else:
        cursor.execute('SELECT COUNT(*) as count FROM predictions')
        total = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM predictions WHERE risk_level = ?', ('safe',))
        healthy = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM predictions WHERE risk_level = ?', ('danger',))
        critical = cursor.fetchone()['count']
        
    conn.close()
    
    return {
        'total': total,
        'healthy': healthy,
        'critical': critical
    }


def create_user(username, email, password_hash):
    """Create a new user"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password, created_at)
            VALUES (?, ?, ?, ?)
        ''', (username, email, password_hash, datetime.now().strftime("%d %b %Y, %I:%M %p")))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()
    return success


def get_user_by_username(username):
    """Retrieve user record by username"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'id': row['id'],
            'username': row['username'],
            'email': row['email'],
            'password': row['password'],
            'created_at': row['created_at']
        }
    return None


def get_user_by_email(email):
    """Retrieve user record by email"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'id': row['id'],
            'username': row['username'],
            'email': row['email'],
            'password': row['password'],
            'created_at': row['created_at']
        }
    return None
