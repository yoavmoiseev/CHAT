"""
build_offline.py
================
Скрипт для создания полностью автономного (offline) пакета School Auto Chat.

Что делает:
  1. Скачивает Python 3.11 Embeddable для Windows (x64)
  2. Устанавливает pip внутри embeddable Python
  3. Устанавливает все зависимости приложения
  4. Копирует файлы приложения в папку ChatApp-Offline/
  5. Создаёт START_CHAT.bat — файл для запуска
  6. Упаковывает всё в ZIP-архив

Требования для запуска этого скрипта:
  - Python 3.8+ (системный, для сборки)
  - Интернет (только при сборке; финальный пакет работает без интернета)

Результат:
  ChatApp-Offline/         — готовая папка (скопируй на флешку)
  ChatApp-Offline.zip      — ZIP-архив для распространения
"""

import os
import sys
import shutil
import zipfile
import subprocess
import urllib.request
import urllib.error

# ──────────────────────────────────────────────────────────────────────────────
# Конфигурация
# ──────────────────────────────────────────────────────────────────────────────

PYTHON_VERSION   = "3.11.9"
PYTHON_EMBED_URL = (
    f"https://www.python.org/ftp/python/{PYTHON_VERSION}/"
    f"python-{PYTHON_VERSION}-embed-amd64.zip"
)
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

# Папка с исходниками (там, где лежит этот скрипт)
SRC_DIR  = os.path.dirname(os.path.abspath(__file__))
# Папка назначения
OUT_DIR  = os.path.join(SRC_DIR, "ChatApp-Offline")
# Папка Python внутри пакета
PY_DIR   = os.path.join(OUT_DIR, "python")

# Зависимости для установки (без eventlet и pyinstaller — они не нужны в runtime)
# Flask-SocketIO будет автоматически использовать threading-режим без eventlet
RUNTIME_PACKAGES = [
    "Flask==3.0.0",
    "Flask-SocketIO==5.3.5",
    "python-socketio==5.10.0",
    "python-engineio>=4.8.0",
]

# Файлы и папки приложения для копирования
APP_FILES = [
    "server.py",
    "start_server.py",
    "teacherbot.py",
    "launcher_offline.py",
    "users_db.json",
    "setup_config.json",
]

APP_DIRS = [
    "static",
    "templates",
    "knowledge_base",
]

# ──────────────────────────────────────────────────────────────────────────────
# Утилиты
# ──────────────────────────────────────────────────────────────────────────────

def step(n, text):
    print(f"\n[{n}] {text}...")

def ok(msg):
    print(f"    ✓ {msg}")

def fail(msg):
    print(f"    ✗ {msg}")
    sys.exit(1)

def warn(msg):
    print(f"    ⚠ {msg}")

def download(url, dest_path):
    """Скачать файл с прогрессом."""
    filename = os.path.basename(dest_path)
    print(f"    Скачиваем {filename} ...")
    try:
        def reporthook(count, block_size, total_size):
            if total_size > 0:
                pct = count * block_size * 100 // total_size
                print(f"\r    {pct}%", end="", flush=True)
        urllib.request.urlretrieve(url, dest_path, reporthook)
        print()  # newline after progress
        ok(f"{filename} скачан")
    except urllib.error.URLError as e:
        fail(f"Не удалось скачать {url}: {e}")

# ──────────────────────────────────────────────────────────────────────────────
# Шаги сборки
# ──────────────────────────────────────────────────────────────────────────────

def step1_prepare_output():
    step(1, "Подготовка выходной папки")
    if os.path.exists(OUT_DIR):
        print(f"    Удаляем старую папку {OUT_DIR} ...")
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)
    os.makedirs(PY_DIR)
    ok(f"Папка создана: {OUT_DIR}")


def step2_download_python():
    step(2, f"Скачивание Python {PYTHON_VERSION} Embeddable")
    zip_path = os.path.join(SRC_DIR, f"python-{PYTHON_VERSION}-embed-amd64.zip")
    if os.path.exists(zip_path):
        ok(f"Уже есть: {zip_path}")
    else:
        download(PYTHON_EMBED_URL, zip_path)
    return zip_path


def step3_extract_python(zip_path):
    step(3, "Распаковка Python в папку пакета")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(PY_DIR)
    ok(f"Python распакован в {PY_DIR}")


def step4_enable_site_packages():
    """Включить site-packages в embeddable Python (раскомментировать import site)."""
    step(4, "Включение site-packages в Python")

    pth_files = [f for f in os.listdir(PY_DIR) if f.endswith("._pth")]
    if not pth_files:
        fail("Файл ._pth не найден внутри Python embeddable!")

    pth_file = os.path.join(PY_DIR, pth_files[0])
    with open(pth_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Убираем комментарий с "import site"
    if "#import site" in content:
        content = content.replace("#import site", "import site")
    elif "# import site" in content:
        content = content.replace("# import site", "import site")
    elif "import site" not in content:
        content += "\nimport site\n"

    with open(pth_file, 'w', encoding='utf-8') as f:
        f.write(content)

    ok(f"site-packages включён ({pth_files[0]})")


def step5_install_pip():
    step(5, "Установка pip в Python")
    python_exe = os.path.join(PY_DIR, "python.exe")
    get_pip_path = os.path.join(SRC_DIR, "get-pip.py")

    if not os.path.exists(get_pip_path):
        download(GET_PIP_URL, get_pip_path)

    # capture_output=False — показываем вывод в консоль (без таймаута)
    result = subprocess.run(
        [python_exe, get_pip_path, "--no-warn-script-location", "--quiet"]
    )
    if result.returncode != 0:
        fail("Не удалось установить pip!")
    ok("pip установлен")


def step6_install_packages():
    step(6, "Установка зависимостей приложения")
    python_exe = os.path.join(PY_DIR, "python.exe")

    # Устанавливаем все пакеты за один вызов pip (быстрее и показываем вывод)
    print(f"    {', '.join(RUNTIME_PACKAGES)}")
    result = subprocess.run(
        [python_exe, "-m", "pip", "install", "--no-warn-script-location"]
        + RUNTIME_PACKAGES
    )
    if result.returncode != 0:
        fail("Ошибка при установке зависимостей!")
    ok("Все зависимости установлены")


def step7_copy_app_files():
    step(7, "Копирование файлов приложения")

    # Файлы
    for fname in APP_FILES:
        src = os.path.join(SRC_DIR, fname)
        dst = os.path.join(OUT_DIR, fname)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            ok(fname)
        else:
            warn(f"{fname} не найден, пропускаем")

    # Папки
    for dname in APP_DIRS:
        src = os.path.join(SRC_DIR, dname)
        dst = os.path.join(OUT_DIR, dname)
        if os.path.exists(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            ok(f"{dname}/")
        else:
            warn(f"Папка {dname}/ не найдена, пропускаем")

    # Создаём пустую папку для базы пользователей если users_db.json не существует
    users_db = os.path.join(OUT_DIR, "users_db.json")
    if not os.path.exists(users_db):
        with open(users_db, 'w', encoding='utf-8') as f:
            f.write("{}")
        ok("users_db.json (пустой)")


def step8_create_launcher_bat():
    step(8, "Создание файла запуска START_CHAT.bat")

    bat_content = r"""@echo off
title School Auto Chat
chcp 65001 >nul

echo.
echo  ================================================
echo   School Auto Chat  -  Offline Version
echo  ================================================
echo.
echo  Запуск сервера...
echo  Не закрывайте это окно пока идёт урок!
echo.

cd /d "%~dp0"

REM Проверяем что embedded Python есть
if not exist "python\python.exe" (
    echo ОШИБКА: Не найден python\python.exe
    echo Архив был неправильно распакован.
    pause
    exit /b 1
)

REM Запускаем launcher
python\python.exe launcher_offline.py

echo.
echo  Сервер остановлен.
pause
"""

    bat_path = os.path.join(OUT_DIR, "START_CHAT.bat")
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    ok("START_CHAT.bat")


def step9_create_readme():
    step(9, "Создание инструкции")

    readme = """School Auto Chat - Offline Version
====================================

КАК ЗАПУСТИТЬ:
--------------
1. Распакуйте ZIP-архив в любую папку (можно на флешку)
2. Дважды кликните на START_CHAT.bat
3. Не закрывайте появившееся чёрное окно!
4. Браузер откроется автоматически — это интерфейс учителя

КАК ПОДКЛЮЧИТЬ УЧЕНИКОВ:
-------------------------
В чёрном окне вы увидите строку:
   Ученики (по сети):  http://192.168.X.X:5002

Ученики открывают браузер и вводят этот адрес.
Все должны быть в одной локальной WiFi/Ethernet сети.

ПЕРВЫЙ ЗАПУСК (регистрация):
-----------------------------
Откройте http://127.0.0.1:PORT и нажмите "Регистрация"
Учитель регистрируется первым — он становится администратором
Затем ученики регистрируются сами

ЧТО ДЕЛАТЬ ЕСЛИ НЕ ЗАПУСКАЕТСЯ:
---------------------------------
- Убедитесь что папка распакована полностью
- Запустите START_CHAT.bat от имени администратора
- Проверьте что антивирус не блокирует python.exe

СИСТЕМНЫЕ ТРЕБОВАНИЯ:
---------------------
- Windows 7 / 8 / 10 / 11 (64-bit)
- 50 МБ свободного места
- Интернет НЕ НУЖЕН

Поддержка: https://github.com/yoavmoiseev/CHAT
"""

    readme_path = os.path.join(OUT_DIR, "ИНСТРУКЦИЯ.txt")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme)
    ok("ИНСТРУКЦИЯ.txt")


def step10_create_zip():
    step(10, "Создание ZIP-архива")
    zip_path = os.path.join(SRC_DIR, "ChatApp-Offline.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(OUT_DIR):
            # Пропускаем __pycache__
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, SRC_DIR)
                zf.write(abs_path, rel_path)

    size_mb = os.path.getsize(zip_path) / 1024 / 1024
    ok(f"ChatApp-Offline.zip ({size_mb:.1f} МБ)")
    return zip_path


def print_summary(zip_path):
    folder_size = sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, dn, fn in os.walk(OUT_DIR)
        for f in fn
    ) / 1024 / 1024

    print()
    print("=" * 60)
    print("  ✅ СБОРКА ЗАВЕРШЕНА!")
    print("=" * 60)
    print()
    print(f"  Папка:  {OUT_DIR}")
    print(f"          ({folder_size:.0f} МБ)")
    print()
    print(f"  Архив:  {zip_path}")
    print(f"          ({os.path.getsize(zip_path)/1024/1024:.1f} МБ)")
    print()
    print("  Как распространить:")
    print("  • Скопируйте ChatApp-Offline.zip на флешку")
    print("  • Или скиньте учителю в мессенджер")
    print("  • Распаковать и запустить START_CHAT.bat")
    print()
    print("  Работает на Windows 7/8/10/11 (64-bit)")
    print("  Без интернета, без установки Python!")
    print()


# ──────────────────────────────────────────────────────────────────────────────
# Точка входа
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print()
    print("=" * 60)
    print("  School Auto Chat - Offline Builder")
    print("=" * 60)
    print()
    print(f"  Исходники:  {SRC_DIR}")
    print(f"  Результат:  {OUT_DIR}")
    print(f"  Python:     {PYTHON_VERSION} Embeddable (x64)")
    print()

    step1_prepare_output()
    zip_path = step2_download_python()
    step3_extract_python(zip_path)
    step4_enable_site_packages()
    step5_install_pip()
    step6_install_packages()
    step7_copy_app_files()
    step8_create_launcher_bat()
    step9_create_readme()
    final_zip = step10_create_zip()
    print_summary(final_zip)


if __name__ == "__main__":
    main()
