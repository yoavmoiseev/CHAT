from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import sys
import json
import socket
from datetime import datetime
from teacherbot import TeacherBot
import hashlib
import socket as _socket

app = Flask(__name__)
app.config['SECRET_KEY'] = 'school-auto-chat-secret-key'
# Determine async mode: prefer env override, then try eventlet/gevent, fallback to threading
env_mode = os.environ.get('SOCKETIO_ASYNC_MODE', '').lower()
detected_mode = None
if env_mode:
    detected_mode = env_mode
else:
    try:
        import eventlet  # type: ignore
        detected_mode = 'eventlet'
    except Exception:
        try:
            import gevent  # type: ignore
            detected_mode = 'gevent'
        except Exception:
            detected_mode = 'threading'

# Try initializing with the detected async mode; fall back to threading on failure
try:
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode=detected_mode)
except ValueError:
    try:
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    except Exception as ex:
        # final fallback: default initialization (may still fail)
        socketio = SocketIO(app, cors_allowed_origins="*")

# Хранилище зарегистрированных пользователей
USERS_FILE = 'users_db.json'
registered_users = {}

# Хранилище активных пользователей (онлайн)
users = {}
# ID хоста (админа) - первый подключившийся
admin_sid = None

# Соберём локальные адреса сервера (loopback + hostname addresses)
try:
    _LOCAL_IPS = set(['127.0.0.1', '::1'])
    hostname = _socket.gethostname()
    # gethostbyname_ex возвращает (hostname, aliaslist, ipaddrlist)
    try:
        _, _, addrs = _socket.gethostbyname_ex(hostname)
        for a in addrs:
            _LOCAL_IPS.add(a)
    except Exception:
        pass
except Exception:
    _LOCAL_IPS = set(['127.0.0.1', '::1'])

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
    
    # Если клиент подключается с локального хоста сервера — назначаем его админом.
    client_ip = request.remote_addr
    client_is_local = client_ip in _LOCAL_IPS

    if client_is_local:
        prev_admin = admin_sid
        admin_sid = request.sid
        print(f'Admin connected (local): {request.sid} from {client_ip}')
        # уведомим нового админа (и снимем флаг у предыдущего, если он был)
        try:
            if prev_admin and prev_admin != admin_sid:
                socketio.emit('admin_status', {'is_admin': False}, room=prev_admin)
        except Exception:
            pass
        try:
            socketio.emit('admin_status', {'is_admin': True}, room=admin_sid)
        except Exception:
            pass
    else:
        # Если админ ещё не назначен, первый не-локальный подключившийся
        # всё ещё может стать админом (сохранённая логика)
        if admin_sid is None:
            admin_sid = request.sid
            print(f'Admin connected: {request.sid} (non-local)')
    
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
        'blocked': registered_users.get(username, {}).get('blocked', False),
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
    username = users[sid]['username']
    # Проверка блокировки
    if registered_users.get(username, {}).get('blocked', False) or users[sid].get('blocked'):
        emit('error', {'message': f'user_blocked'} , room=sid)
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
    username = users[sid]['username']
    if registered_users.get(username, {}).get('blocked', False) or users[sid].get('blocked'):
        emit('error', {'message': f'user_blocked'} , room=sid)
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
    username = users[sid]['username']
    if registered_users.get(username, {}).get('blocked', False) or users[sid].get('blocked'):
        emit('error', {'message': f'user_blocked'} , room=sid)
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


# --- Admin actions: block/unblock/delete users ---
@socketio.on('block_user')
def handle_block_user(data):
    sid = request.sid
    if sid != admin_sid:
        emit('error', {'message': 'not_authorized'})
        return
    target = data.get('username')
    if not target or target not in registered_users:
        emit('error', {'message': 'user_not_found'})
        return
    registered_users[target]['blocked'] = True
    save_users()
    # update online user if present
    target_sid = None
    for s, u in users.items():
        if u['username'] == target:
            users[s]['blocked'] = True
            target_sid = s
            try:
                emit('blocked', {'username': target}, room=target_sid)
            except Exception:
                pass
            break
    emit('users_update', {'users': list(users.values())}, broadcast=True)
    emit('user_blocked', {'username': target}, broadcast=True)

@socketio.on('unblock_user')
def handle_unblock_user(data):
    sid = request.sid
    if sid != admin_sid:
        emit('error', {'message': 'not_authorized'})
        return
    target = data.get('username')
    if not target or target not in registered_users:
        emit('error', {'message': 'user_not_found'})
        return
    registered_users[target]['blocked'] = False
    save_users()
    for s, u in users.items():
        if u['username'] == target:
            users[s]['blocked'] = False
            try:
                emit('unblocked', {'username': target}, room=s)
            except Exception:
                pass
            break
    emit('users_update', {'users': list(users.values())}, broadcast=True)
    emit('user_unblocked', {'username': target}, broadcast=True)

@socketio.on('delete_user')
def handle_delete_user(data):
    sid = request.sid
    if sid != admin_sid:
        emit('error', {'message': 'not_authorized'})
        return
    target = data.get('username')
    if not target or target not in registered_users:
        emit('error', {'message': 'user_not_found'})
        return
    # remove from registered users
    try:
        del registered_users[target]
        save_users()
    except Exception:
        pass
    # disconnect if online and remove from users
    target_sid = None
    for s, u in list(users.items()):
        if u['username'] == target:
            target_sid = s
            try:
                emit('user_deleted', {'username': target}, room=s)
                socketio.disconnect(s)
            except Exception:
                pass
            if s in users:
                del users[s]
    # notify clients to remove messages from this user
    emit('remove_messages', {'username': target}, broadcast=True)
    emit('users_update', {'users': list(users.values())}, broadcast=True)
    emit('user_deleted_broadcast', {'username': target}, broadcast=True)

if __name__ == '__main__':
    # Загрузка базы пользователей
    load_users()
    print(f'Loaded {len(registered_users)} registered users')

    # Создание папки для базы знаний, если её нет
    if not os.path.exists('knowledge_base'):
        os.makedirs('knowledge_base')
        print('Created knowledge_base folder - add your TXT and HTML files there!')

    # Определение порта: сначала аргумент командной строки, затем переменная окружения, иначе стандартный
    port = None
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except Exception:
            port = None

    if not port:
        port_env = os.environ.get('PORT')
        if port_env and port_env.isdigit():
            port = int(port_env)

    if not port:
        port = 5002

    # Запуск сервера
    print('=' * 50)
    print('School Auto Chat Server Starting...')
    print('=' * 50)
    print('Server will be available at:')
    print(f'  Local:   http://127.0.0.1:{port}')
    print(f'  Network: http://<your-ip>:{port}')
    print('=' * 50)

    # Bind to localhost by default for portable/offline builds to avoid firewall prompts
    host = os.environ.get('HOST', '127.0.0.1')
    socketio.run(app, host=host, port=port, debug=True)
