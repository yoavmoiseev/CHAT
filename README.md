# 🎓 School Auto Chat

Offline classroom chat with a built-in TeacherBot for searching educational materials.

## 🌟 Features

* ✅ **Registration and login system** – each user has their own username and password
* ✅ **Real-time messaging** – instant communication via WebSocket
* 💬 **Public chat** – communicate with the entire class
* 🔒 **Private messages** – direct messages between students
* 🤖 **TeacherBot** – smart bot for searching information in study materials
* 👑 **Administrator role** – the teacher (who started the server) becomes admin
* 🎨 **Unique colors** – each user gets their own username color
* 🌐 **Multilingual support** – full support for Hebrew (RTL), Russian, and English
* 📱 **Responsive design** – works on computers and smartphones
* 🌐 **Fully offline** – no internet required, works on a local network

## 🚀 Quick Start

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the server

```bash
python server.py
```

The server will start on port 5000. You will see:

```
School Auto Chat Server Starting...
==================================================
Server will be available at:
  Local:   http://127.0.0.1:5000
  Network: http://<your-ip>:5000
==================================================
```

### Connecting students

1. Find the server computer's IP address:

   * Windows: `ipconfig` in command prompt (look for "IPv4 Address")
   * Linux/Mac: `ifconfig` or `ip addr`

2. Students open a browser and go to:

   ```
   http://<server-ip>:5000
   ```

   Example: `http://192.168.1.10:5000`

3. Enter their name and start chatting!

## 🔐 Registration and Login

### First time – Registration

1. On first visit, you will see the registration screen
2. Choose interface language (עברית / Русский / English)
3. Enter username (minimum 3 characters)
4. Enter password (minimum 4 characters)
5. Click "Register"

### Subsequent logins

1. Open the chat
2. Click "Already have an account? Login"
3. Enter your username and password
4. Click "Login"

**Important:** Each user can be online only once. You cannot log in from the same account simultaneously on multiple devices.

## 🌐 Language Switching

In the top-right corner there are language buttons:

* **עברית** – Hebrew (right-to-left text)
* **Русский** – Russian
* **English** – English

The interface language changes instantly!

## 🎨 User Colors

Each registered user automatically gets a unique color:

* Assigned during registration
* Used for avatar and username
* Helps visually distinguish users

## 🤖 TeacherBot Knowledge Base

TeacherBot searches for information in the `knowledge_base/` folder.

### Adding materials

1. Create TXT or HTML files with educational content
2. Place them in the `knowledge_base/` folder
3. You can create subfolders for organization

### File formats

**Text files (.txt):**

```
TERM

Definition of the term with detailed explanation.
You can use multiple paragraphs.

---

ANOTHER TERM

Another definition...
```

**HTML files (.html):**

```html
<h1>Topic Title</h1>
<p>Definition text...</p>
```

### Example TeacherBot queries

* "What is an IP address?"
* "integral"
* "quadratic formula"
* "derivative"
* "Pythagorean theorem"

TeacherBot automatically:

* Finds relevant information in files
* Shows context around the found term
* Suggests similar terms in case of typos

## 🎮 Usage

### Public chat

* Type messages in the input field
* Press Enter or click send
* All participants will see your message

### Private messages

* **Double-click** on a username
* Or **right-click** → "Private message"
* Write and send your message

### TeacherBot

* Switch to the "🤖 TeacherBot" tab
* Ask a question (e.g., "What is an integral?")
* Get an answer from the knowledge base

### Administrator role

* The first connected user (teacher) becomes admin automatically
* Admin is marked with 👑
* If the admin disconnects, the next user becomes admin

## 📦 Creating an EXE file

For a standalone application:

Project structure:

```
CH/
├── server.py              # Main Flask server
├── teacherbot.py          # TeacherBot search module
├── requirements.txt       # Python dependencies
├── users_db.json          # User database (auto-created)
├── templates/
│   └── index.html        # Chat HTML page (multilingual)
├── static/
│   ├── style.css         # Styles (RTL supported)
│   ├── app.js            # Client logic (multilingual + auth)
│   └── translations.json # Translations
└── knowledge_base/       # Knowledge base (TXT/HTML files)
    ├── basics.txt
    ├── math.html
    ├── hebrew_basics.txt
    └── hebrew_math.html
```

### Technologies

* **Backend:** Flask-SocketIO, WebSocket
* **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
* **UI:** Modern gradient design, responsive layout
* **Search:** Full-text search with autocorrection

## 🔧 Configuration

### Changing the port

In `server.py`, modify the port value.

For production, change:

```python
debug=True
```

to:

```python
debug=False
```

## 💡 Tips

### For teachers:

* Start the server before the lesson
* Prepare materials in `knowledge_base/`
* Write the IP address on the board

### For students:

* Register once with a unique username
* Use your real name for identification
* Choose a comfortable interface language
* Your color is visible to everyone
* Private messages are visible only to you and the recipient
* TeacherBot works in all languages

## 🐛 Troubleshooting

**Server does not start:**

* Check dependencies: `pip install -r requirements.txt`
* Ensure port 5000 is not in use

**Students cannot connect:**

* Make sure everyone is on the same local network
* Check firewall settings (port 5000 must be open)
* Verify the correct IP address

**Cannot log in:**

* Make sure you are registered
* Check password (minimum 4 characters)
* Ensure you're not logged in on another device

**Hebrew issues:**

* Ensure files are saved in UTF-8 encoding
* RTL direction is automatic
* Refresh the page if text appears incorrectly

**TeacherBot cannot find information:**

* Ensure files are in `knowledge_base/`
* Check UTF-8 encoding
* Restart the server
* TeacherBot searches in all languages

## 📝 License

MIT License – free for educational use!

## 🤝 Support

If you encounter issues:

* Check server console for errors
* Ensure all files are present
* Review terminal logs

---

**Built for education. Fully offline! 🎓**

