from flask import Flask, request, jsonify, send_from_directory
import json
import os
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__, static_folder='.')
DATA_FILE = 'data.json'
DATABASE_URL = os.environ.get('DATABASE_URL')

def use_db():
    return bool(DATABASE_URL)

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id SERIAL PRIMARY KEY,
            admin_name TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            comment TEXT DEFAULT '',
            date TEXT NOT NULL
        )
    """)
    cur.execute("SELECT COUNT(*) FROM admins")
    if cur.fetchone()[0] == 0:
        for name in ['N5', '7MO', 'ABDULLAH', 'SUZ', 'TIQ']:
            cur.execute("INSERT INTO admins (name) VALUES (%s) ON CONFLICT DO NOTHING", (name,))
    cur.close()
    conn.close()

if use_db():
    init_db()

# --- Data helpers ---

def load_admins():
    if use_db():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT name FROM admins ORDER BY id")
        rows = [r[0] for r in cur.fetchall()]
        cur.close()
        conn.close()
        return rows
    if not os.path.exists(DATA_FILE):
        return ['N5', '7MO', 'ABDULLAH', 'SUZ', 'TIQ']
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f).get('admins', [])

def save_admins(admins):
    if use_db():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM admins")
        for name in admins:
            cur.execute("INSERT INTO admins (name) VALUES (%s)", (name,))
        cur.close()
        conn.close()
        return

def load_ratings():
    if use_db():
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, admin_name AS admin, rating, comment, date FROM ratings ORDER BY id DESC")
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return rows
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f).get('ratings', [])

def add_rating_db(admin, rating, comment, date):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO ratings (admin_name, rating, comment, date) VALUES (%s, %s, %s, %s) RETURNING id",
        (admin, rating, comment, date)
    )
    new_id = cur.fetchone()[0]
    cur.close()
    conn.close()
    return new_id

def delete_rating_db(rating_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM ratings WHERE id = %s", (rating_id,))
    deleted = cur.rowcount
    cur.close()
    conn.close()
    return deleted

def add_admin_db(name):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO admins (name) VALUES (%s)", (name,))
    cur.close()
    conn.close()

def delete_admin_db(name):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM admins WHERE name = %s", (name,))
    cur.execute("DELETE FROM ratings WHERE admin_name = %s", (name,))
    cur.close()
    conn.close()

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, OPTIONS'
    return response

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

# --- Admins ---

@app.route('/api/admins', methods=['GET'])
def get_admins():
    return jsonify(load_admins())

@app.route('/api/admins', methods=['POST'])
def add_admin():
    name = request.json.get('name', '').strip()
    if not name:
        return jsonify({'error': 'الاسم مطلوب'}), 400
    admins = load_admins()
    if name in admins:
        return jsonify({'error': 'الإداري موجود مسبقاً'}), 400
    if use_db():
        add_admin_db(name)
    else:
        admins.append(name)
        save_admins(admins)
    return jsonify({'message': 'تمت الإضافة', 'admins': load_admins()})

@app.route('/api/admins/<name>', methods=['DELETE'])
def delete_admin(name):
    admins = load_admins()
    if name not in admins:
        return jsonify({'error': 'الإداري غير موجود'}), 404
    if use_db():
        delete_admin_db(name)
    else:
        admins.remove(name)
        save_admins(admins)
        data = {'admins': admins, 'ratings': []}
        data['ratings'] = [r for r in load_ratings() if r['admin'] != name]
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'message': 'تم الحذف', 'admins': load_admins()})

# --- Ratings ---

@app.route('/api/ratings', methods=['GET'])
def get_ratings():
    ratings = load_ratings()
    admin = request.args.get('admin')
    if admin:
        return jsonify([r for r in ratings if r['admin'] == admin])
    return jsonify(ratings)

@app.route('/api/ratings', methods=['POST'])
def add_rating():
    body = request.json
    admin = body.get('admin', '').strip()
    rating = body.get('rating')
    comment = body.get('comment', '').strip()
    if not admin or not rating:
        return jsonify({'error': 'الإداري والتقييم مطلوبان'}), 400
    admins = load_admins()
    if admin not in admins:
        return jsonify({'error': 'الإداري غير موجود'}), 404
    date = datetime.now().strftime('%Y/%m/%d')
    if use_db():
        new_id = add_rating_db(admin, int(rating), comment, date)
    else:
        data = {'admins': admins, 'ratings': load_ratings()}
        new_id = int(datetime.now().timestamp() * 1000000)
        data['ratings'].append({
            'id': new_id,
            'admin': admin,
            'rating': int(rating),
            'comment': comment,
            'date': date
        })
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'message': 'تم إضافة التقييم', 'rating': {'id': new_id}})

@app.route('/api/ratings/<int:rating_id>', methods=['DELETE'])
def delete_rating(rating_id):
    if use_db():
        deleted = delete_rating_db(rating_id)
        if not deleted:
            return jsonify({'error': 'التقييم غير موجود'}), 404
    else:
        data = {'admins': load_admins(), 'ratings': load_ratings()}
        before = len(data['ratings'])
        data['ratings'] = [r for r in data['ratings'] if r['id'] != rating_id]
        if len(data['ratings']) == before:
            return jsonify({'error': 'التقييم غير موجود'}), 404
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'message': 'تم الحذف'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
