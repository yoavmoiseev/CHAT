from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import json
from datetime import datetime
from teacherbot import TeacherBot
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'school-auto-chat-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Хранилище зарегистрированных пользователей
USERS_FILE = 'users_db.json'
registered_users = {}

# Хранилище активных пользователей (онлайн)
users = {}
# ID хоста (админа) - первый подключившийся
admin_sid = None

# Функции для работы с базой пользователей
def load_users():
    """Загрузка зарегистрированных пользователей из файла"""
    global registered_users
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                registered_users = json.load(f)
        except:
            registered_users = {}
    else:
        registered_users = {}

def save_users():
    """Сохранение зарегистрированных пользователей в файл"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(registered_users, f, ensure_ascii=False, indent=2)

def hash_password(password):
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_user_color(username):
    """Генерация уникального цвета для пользователя на основе его имени"""
    colors = [
        '#667eea', '#764ba2', '#f093fb', '#4facfe',
        '#43e97b', '#fa709a', '#fee140', '#30cfd0',
        '#a8edea', '#fed6e3', '#ff9a9e', '#fad0c4',
        '#ffecd2', '#fcb69f', '#ff6e7f', '#bfe9ff',
        '#c471f5', '#fa71cd', '#96e6a1', '#d4fc79'
    ]
    # Используем хеш имени для выбора цвета
    hash_value = sum(ord(c) for c in username)
    return colors[hash_value % len(colors)]

# Инициализация TeacherBot
teacher_bot = TeacherBot('knowledge_base')

@app.route('/')
def index():
    """Главная страница чата"""
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """Favicon redirect"""
    return app.send_static_file('favicon.svg')

@socketio.on('connect')
def handle_connect():
    """Обработка подключения пользователя"""
    global admin_sid
    
    # Первый подключившийся становится админом
    if admin_sid is None:
        admin_sid = request.sid
        print(f'Admin connected: {request.sid}')
    
    print(f'User connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    """Обработка отключения пользователя"""
    global admin_sid
    
    sid = request.sid
    if sid in users:
        username = users[sid]['username']
        del users[sid]
        
        # Уведомление всех об отключении
        emit('user_left', {
            'username': username,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }, broadcast=True)
        
        # Обновление списка пользователей
        emit('users_update', {'users': list(users.values())}, broadcast=True)
    
    # Если админ отключился, выбираем нового
    if sid == admin_sid:
        admin_sid = list(users.keys())[0] if users else None
        if admin_sid:
            emit('admin_status', {'is_admin': True}, room=admin_sid)
    
    print(f'User disconnected: {sid}')

@socketio.on('register')
def handle_register(data):
    """Регистрация нового пользователя"""
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        emit('register_error', {'message': 'login_required'})
        return
    
    if len(username) < 3:
        emit('register_error', {'message': 'username_too_short'})
        return
    
    if len(password) < 4:
        emit('register_error', {'message': 'password_too_short'})
        return
    
    if username in registered_users:
        emit('register_error', {'message': 'username_taken'})
        return
    
    # Регистрация нового пользователя
    registered_users[username] = {
        'password': hash_password(password),
        'color': generate_user_color(username),
        'created_at': datetime.now().isoformat()
    }
    save_users()
    
    emit('register_success', {'message': 'registration_success'})
    print(f'New user registered: {username}')

@socketio.on('login')
def handle_login(data):
    """Вход пользователя"""
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        emit('login_error', {'message': 'login_required'})
        return
    
    if username not in registered_users:
        emit('login_error', {'message': 'user_not_found'})
        return
    
    if registered_users[username]['password'] != hash_password(password):
        emit('login_error', {'message': 'wrong_password'})
        return
    
    # Проверка, не залогинен ли уже этот пользователь
    for user_sid, user_data in users.items():
        if user_data['username'] == username:
            emit('login_error', {'message': 'already_logged_in'})
            return
    
    # Успешный вход
    handle_join({'username': username})

@socketio.on('join')
def handle_join(data):
    """Регистрация пользователя в чате (после логина)"""
    username = data.get('username', 'Anonymous')
    sid = request.sid
    
    # Проверка, что пользователь зарегистрирован
    if username not in registered_users:
        emit('join_error', {'message': 'user_not_registered'})
        return
    
    # Проверка на уникальность имени (не должно быть онлайн)
    existing_names = [user['username'] for user in users.values()]
    if username in existing_names:
        emit('join_error', {'message': 'already_online'})
        return
    
    # Сохранение пользователя
    is_admin = (sid == admin_sid)
    user_color = registered_users[username]['color']
    users[sid] = {
        'sid': sid,
        'username': username,
        'is_admin': is_admin,
        'color': user_color
    }
    
    # Подтверждение регистрации
    emit('join_success', {
        'username': username,
        'is_admin': is_admin,
        'color': user_color
    })
    
    # Уведомление всех о новом пользователе
    emit('user_joined', {
        'username': username,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    }, broadcast=True)
    
    # Отправка списка пользователей
    emit('users_update', {'users': list(users.values())}, broadcast=True)
    
    print(f'User joined: {username} (Admin: {is_admin})')

@socketio.on('public_message')
def handle_public_message(data):
    """Обработка публичного сообщения"""
    sid = request.sid
    if sid not in users:
        return
    
    message_data = {
        'username': users[sid]['username'],
        'message': data['message'],
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'is_admin': users[sid]['is_admin'],
        'color': users[sid]['color']
    }
    
    emit('public_message', message_data, broadcast=True)
    print(f"Public message from {users[sid]['username']}: {data['message']}")

@socketio.on('private_message')
def handle_private_message(data):
    """Обработка приватного сообщения"""
    sid = request.sid
    if sid not in users:
        return
    
    target_username = data['to']
    message = data['message']
    
    # Поиск получателя
    target_sid = None
    for user_sid, user_data in users.items():
        if user_data['username'] == target_username:
            target_sid = user_sid
            break
    
    if not target_sid:
        emit('error', {'message': f'Пользователь {target_username} не найден'})
        return
    
    message_data = {
        'from': users[sid]['username'],
        'to': target_username,
        'message': message,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    }
    
    # Отправка отправителю и получателю
    emit('private_message', message_data, room=sid)
    emit('private_message', message_data, room=target_sid)
    
    print(f"Private message from {users[sid]['username']} to {target_username}")

@socketio.on('teacherbot_query')
def handle_teacherbot_query(data):
    """Обработка запроса к TeacherBot"""
    sid = request.sid
    if sid not in users:
        return
    
    query = data['query']
    username = users[sid]['username']
    
    print(f"TeacherBot query from {username}: {query}")
    
    # Поиск ответа через TeacherBot
    response = teacher_bot.search(query)
    
    # Отправка ответа пользователю
    bot_message = {
        'username': 'TeacherBot',
        'message': response,
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'is_bot': True,
        'query': query,
        'to_user': username
    }
    
    emit('teacherbot_response', bot_message, room=sid)
    print(f"TeacherBot response sent to {username}")

if __name__ == '__main__':
    # Загрузка базы пользователей
    load_users()
    print(f'Loaded {len(registered_users)} registered users')
    
    # Создание папки для базы знаний, если её нет
    if not os.path.exists('knowledge_base'):
        os.makedirs('knowledge_base')
        print('Created knowledge_base folder - add your TXT and HTML files there!')
    
    # Запуск сервера
    print('=' * 50)
    print('School Auto Chat Server Starting...')
    print('=' * 50)
    print('Server will be available at:')
    print('  Local:   http://127.0.0.1:5000')
    print('  Network: http://<your-ip>:5000')
    print('=' * 50)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
