"""
School Auto Chat - Offline Launcher
====================================
Запускает сервер чата и открывает браузер.
Работает с embedded Python (без интернета).
"""

import os
import sys
import socket
import webbrowser
import threading
import time
import subprocess
import io

# Fix Windows console encoding so Russian/Unicode prints correctly
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

# --------------------------------------------------------------------------
# Определяем BASE_DIR — папка со всеми файлами приложения
# --------------------------------------------------------------------------
if getattr(sys, 'frozen', False):
    # PyInstaller EXE
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

# --------------------------------------------------------------------------
# Утилиты
# --------------------------------------------------------------------------

def get_local_ip():
    """Получить локальный IP адрес компьютера в сети."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.1.1", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        pass
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if not ip.startswith("127."):
            return ip
    except Exception:
        pass
    return "127.0.0.1"


def is_port_free(port):
    """Проверить, свободен ли порт."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(('0.0.0.0', port))
        s.close()
        return True
    except Exception:
        return False


def choose_port():
    """Выбрать первый свободный порт из списка."""
    for p in [5002, 5003, 5001, 8000, 8888, 5000]:
        if is_port_free(p):
            return p
    # ОС сама выберет свободный порт
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def open_browser(url, delay=3.0):
    """Открыть браузер через несколько секунд после старта."""
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception:
        pass


# --------------------------------------------------------------------------
# Главная функция
# --------------------------------------------------------------------------

def main():
    ip = get_local_ip()
    port = choose_port()
    local_url   = f"http://127.0.0.1:{port}"
    network_url = f"http://{ip}:{port}"

    print()
    print("=" * 60)
    print("       School Auto Chat  —  Offline Version")
    print("=" * 60)
    print()
    print(f"  Учитель (локально):  {local_url}")
    print(f"  Ученики (по сети):   {network_url}")
    print()
    print("  Ученики открывают браузер и вводят Network URL.")
    print("  Для остановки нажмите Ctrl+C в этом окне.")
    print()
    print("=" * 60)
    print()

    # Открыть браузер на машине учителя через 3 секунды
    threading.Thread(
        target=open_browser,
        args=(local_url, 3.0),
        daemon=True
    ).start()

    # Запустить server.py с выбранным портом
    server_py = os.path.join(BASE_DIR, 'server.py')
    python_exe = sys.executable

    # Передаём порт через переменную окружения и argv
    # FLASK_DEBUG=0 — отключаем reloader (он не нужен в offline-режиме)
    env = os.environ.copy()
    env['PORT'] = str(port)
    env['FLASK_DEBUG'] = '0'

    # os.execv заменяет текущий процесс — не возвращает управление
    try:
        os.execve(python_exe, [python_exe, server_py, str(port)], env)
    except AttributeError:
        # Windows иногда не имеет os.execve, используем subprocess
        proc = subprocess.Popen(
            [python_exe, server_py, str(port)],
            env=env,
            cwd=BASE_DIR
        )
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            proc.wait()


if __name__ == '__main__':
    main()
