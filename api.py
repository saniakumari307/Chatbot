import sqlite3
import asyncio
import os
from flask import Flask, jsonify, request, session, redirect, url_for, flash, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
import datetime
import traceback
from db import init_db

app = Flask(__name__)
app.secret_key = 'change_this_secret_key'
CORS(app, origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.1.3:3000",
    "https://moonlit-begonia-0c230d.netlify.app"
], supports_credentials=True)
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.1.3:3000",
    "https://moonlit-begonia-0c230d.netlify.app"
])

DB_NAME = 'users.db'

# Ensure DB tables exist
init_db()

# --- Database helpers ---
def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT user_id, full_name, username, join_date, invite_link, photo_url, label FROM users')
    users = c.fetchall()
    conn.close()
    return users

def get_total_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    total = c.fetchone()[0]
    conn.close()
    return total

def get_messages_for_user(user_id, limit=100):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT sender, message, timestamp FROM messages WHERE user_id = ? ORDER BY id ASC LIMIT ?', (user_id, limit))
    messages = c.fetchall()
    conn.close()
    return messages

def save_message(user_id, sender, message):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO messages (user_id, sender, message, timestamp) VALUES (?, ?, ?, ?)',
              (user_id, sender, message, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def add_user(user_id, full_name, username, join_date, invite_link, photo_url=None, label=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id, full_name, username, join_date, invite_link, photo_url, label) VALUES (?, ?, ?, ?, ?, ?, ?)', (user_id, full_name, username, join_date, invite_link, photo_url, label))
    conn.commit()
    conn.close()

def get_active_users(minutes=60):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    since = (datetime.datetime.now() - datetime.timedelta(minutes=minutes)).strftime('%Y-%m-%d %H:%M:%S')
    c.execute('SELECT COUNT(DISTINCT user_id) FROM messages WHERE timestamp >= ?', (since,))
    count = c.fetchone()[0]
    conn.close()
    return count

def get_total_messages():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM messages')
    count = c.fetchone()[0]
    conn.close()
    return count

def get_new_joins_today():
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users WHERE join_date LIKE ?', (f'{today}%',))
    count = c.fetchone()[0]
    conn.close()
    return count

def get_user_online_status(user_id, minutes=5):
    """Check if user has been active in the last N minutes"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    since = (datetime.datetime.now() - datetime.timedelta(minutes=minutes)).strftime('%Y-%m-%d %H:%M:%S')
    c.execute('SELECT 1 FROM messages WHERE user_id = ? AND timestamp >= ? LIMIT 1', (user_id, since))
    is_online = c.fetchone() is not None
    conn.close()
    return is_online

@app.route('/user-status/<int:user_id>')
def user_status(user_id):
    """Get user online status and last activity"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Get last message timestamp
    c.execute('SELECT timestamp FROM messages WHERE user_id = ? ORDER BY id DESC LIMIT 1', (user_id,))
    last_message = c.fetchone()
    # Check if online (active in last 5 minutes)
    is_online = get_user_online_status(user_id, 5)
    # Get user info
    c.execute('SELECT full_name, username, photo_url FROM users WHERE user_id = ?', (user_id,))
    user_info = c.fetchone()
    conn.close()
    return jsonify({
        'user_id': user_id,
        'full_name': user_info[0] if user_info else '',
        'username': user_info[1] if user_info else '',
        'photo_url': user_info[2] if user_info else None,
        'is_online': is_online,
        'last_activity': last_message[0] if last_message else None
    })

# --- Flask API Endpoints ---
@app.route('/dashboard-users')
def dashboard_users():
    # Get page and page_size from query params, default page=1, page_size=10
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    offset = (page - 1) * page_size
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    total = c.fetchone()[0]
    c.execute('SELECT user_id, full_name, username, join_date, invite_link, photo_url, label FROM users ORDER BY join_date DESC LIMIT ? OFFSET ?', (page_size, offset))
    users = c.fetchall()
    conn.close()
    # Add online status for each user
    users_with_status = []
    for u in users:
        is_online = get_user_online_status(u[0], 5)
        users_with_status.append({
                'user_id': u[0],
                'full_name': u[1],
                'username': u[2],
                'join_date': u[3],
            'invite_link': u[4],
            'photo_url': u[5],
            'is_online': is_online,
            'label': u[6]
        })
    return jsonify({
        'users': users_with_status,
        'total': total,
        'page': page,
        'page_size': page_size
    })

@app.route('/dashboard-stats')
def dashboard_stats():
    # Total users in the database
    total_users = get_total_users()
    # Active users: users who sent messages in the last 60 minutes
    active_users = get_active_users()  # last 60 minutes
    # Total messages sent (all time)
    total_messages = get_total_messages()
    # New joins today
    new_joins_today = get_new_joins_today()
    return jsonify({
        'total_users': total_users,
        'active_users': active_users,
        'total_messages': total_messages,
        'new_joins_today': new_joins_today
    })

@app.route('/chat/<int:user_id>/messages')
def chat_messages(user_id):
    messages = get_messages_for_user(user_id)
    # messages is a list of (sender, message, timestamp)
    return jsonify([
        [sender, message, timestamp] for sender, message, timestamp in messages
    ])

@app.route('/user/<int:user_id>/label', methods=['POST'])
def set_user_label(user_id):
    label = request.json.get('label')
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE users SET label = ? WHERE user_id = ?', (label, user_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'user_id': user_id, 'label': label})

@socketio.on('join')
def on_join(data):
    room = data.get('room')
    join_room(room)

# Serve React build static files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'admin', 'build')
    if path != "" and os.path.exists(os.path.join(build_dir, path)):
        return send_from_directory(build_dir, path)
    else:
        return send_from_directory(build_dir, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    socketio.run(app, host="0.0.0.0", port=port, debug=False) 
