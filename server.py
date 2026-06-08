from flask import Flask, request, jsonify, send_from_directory
import json
import os
from datetime import datetime

app = Flask(__name__, static_folder='.')
DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {'admins': ['N5', '7MO', 'ABDULLAH', 'SUZ', 'TIQ'], 'ratings': []}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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
    data = load_data()
    return jsonify(data['admins'])

@app.route('/api/admins', methods=['POST'])
def add_admin():
    data = load_data()
    name = request.json.get('name', '').strip()
    if not name:
        return jsonify({'error': 'الاسم مطلوب'}), 400
    if name in data['admins']:
        return jsonify({'error': 'الإداري موجود مسبقاً'}), 400
    data['admins'].append(name)
    save_data(data)
    return jsonify({'message': 'تمت الإضافة', 'admins': data['admins']})

@app.route('/api/admins/<name>', methods=['DELETE'])
def delete_admin(name):
    data = load_data()
    if name not in data['admins']:
        return jsonify({'error': 'الإداري غير موجود'}), 404
    data['admins'].remove(name)
    data['ratings'] = [r for r in data['ratings'] if r['admin'] != name]
    save_data(data)
    return jsonify({'message': 'تم الحذف', 'admins': data['admins']})

# --- Ratings ---

@app.route('/api/ratings', methods=['GET'])
def get_ratings():
    data = load_data()
    admin = request.args.get('admin')
    if admin:
        filtered = [r for r in data['ratings'] if r['admin'] == admin]
        return jsonify(filtered)
    return jsonify(data['ratings'])

@app.route('/api/ratings', methods=['POST'])
def add_rating():
    data = load_data()
    body = request.json
    admin = body.get('admin', '').strip()
    rating = body.get('rating')
    comment = body.get('comment', '').strip()
    if not admin or not rating:
        return jsonify({'error': 'الإداري والتقييم مطلوبان'}), 400
    if admin not in data['admins']:
        return jsonify({'error': 'الإداري غير موجود'}), 404
    new_rating = {
        'id': int(datetime.now().timestamp() * 1000),
        'admin': admin,
        'rating': int(rating),
        'comment': comment,
        'date': datetime.now().strftime('%Y/%m/%d')
    }
    data['ratings'].append(new_rating)
    save_data(data)
    return jsonify({'message': 'تم إضافة التقييم', 'rating': new_rating})

@app.route('/api/ratings/<int:rating_id>', methods=['DELETE'])
def delete_rating(rating_id):
    data = load_data()
    before = len(data['ratings'])
    data['ratings'] = [r for r in data['ratings'] if r['id'] != rating_id]
    if len(data['ratings']) == before:
        return jsonify({'error': 'التقييم غير موجود'}), 404
    save_data(data)
    return jsonify({'message': 'تم الحذف'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
