# 📦 Создание EXE файла для School Auto Chat

Эта инструкция поможет вам создать автономный EXE файл, который можно запускать без установки Python.

## Шаг 1: Установка PyInstaller

```bash
pip install pyinstaller
```

## Шаг 2: Создание EXE файла

### Вариант 1: Простая команда (рекомендуется)

```bash
pyinstaller --onefile --add-data "templates;templates" --add-data "static;static" --add-data "knowledge_base;knowledge_base" --icon=icon.ico --name SchoolAutoChat server.py
```

### Вариант 2: С подробными параметрами

```bash
pyinstaller ^
  --onefile ^
  --windowed ^
  --add-data "templates;templates" ^
  --add-data "static;static" ^
  --add-data "knowledge_base;knowledge_base" ^
  --hidden-import=flask ^
  --hidden-import=flask_socketio ^
  --hidden-import=eventlet ^
  --hidden-import=socketio ^
  --name "SchoolAutoChat" ^
  --clean ^
  server.py
```

## Шаг 3: Найти готовый EXE

После выполнения команды:
- В папке `dist/` будет файл `SchoolAutoChat.exe`
- Это полностью автономное приложение!

## Шаг 4: Распространение

### Что включить в архив для распространения:

```
SchoolAutoChat/
├── SchoolAutoChat.exe     (главный файл)
├── knowledge_base/        (папка с учебными материалами)
│   ├── basics.txt
│   └── math.html
└── README.txt             (инструкция для пользователей)
```

### Простая инструкция для конечного пользователя:

1. Запустите `SchoolAutoChat.exe`
2. Откройте браузер
3. Перейдите на `http://127.0.0.1:5000`
4. Для подключения других - используйте ваш IP адрес

## Параметры PyInstaller:

- `--onefile` - создать один EXE файл вместо папки с множеством файлов
- `--add-data` - включить дополнительные файлы (templates, static, knowledge_base)
- `--windowed` - не показывать консоль (опционально)
- `--icon` - добавить иконку (если есть файл icon.ico)
- `--name` - имя итогового EXE файла
- `--clean` - очистить кеш перед сборкой

## Тестирование EXE:

```bash
cd dist
SchoolAutoChat.exe
```

Откройте браузер на `http://127.0.0.1:5000`

## Создание spec файла (продвинутый способ):

Если нужна более гибкая конфигурация:

```bash
pyi-makespec --onefile server.py
```

Отредактируйте `server.spec`, затем:

```bash
pyinstaller server.spec
```

## Пример server.spec:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['server.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('knowledge_base', 'knowledge_base'),
    ],
    hiddenimports=['flask', 'flask_socketio', 'eventlet', 'socketio'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SchoolAutoChat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

## Советы:

1. **Размер файла:** EXE может быть 30-50 MB - это нормально, так как включает Python runtime
2. **Антивирус:** Некоторые антивирусы могут блокировать EXE - добавьте в исключения
3. **Обновление базы знаний:** Даже после создания EXE, папку `knowledge_base` можно редактировать
4. **Первый запуск:** Может быть медленным (10-30 сек), последующие запуски быстрее

## Устранение проблем:

**Ошибка: "Failed to execute script"**
- Проверьте, что все зависимости установлены
- Используйте `--debug` для подробных логов

**Ошибка: "Template not found"**
- Убедитесь, что путь к templates правильный: `--add-data "templates;templates"`

**EXE не запускается:**
- Запустите через командную строку, чтобы увидеть ошибки
- Проверьте наличие всех файлов

---

✅ **После создания EXE файла у вас будет полностью автономное приложение, которое можно распространять без установки Python!**
