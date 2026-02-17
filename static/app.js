// WebSocket соединение
let socket;
function createStubSocket(){
    console.warn('Socket.IO client unavailable — using stub socket (no real-time features).');
    const noop = ()=>{};
    return {
        on: noop,
        emit: noop,
        off: noop
    };
}

if (typeof io === 'undefined') {
    // show visible warning to user
    document.addEventListener('DOMContentLoaded', ()=>{
        const warn = document.createElement('div');
        warn.style.position = 'fixed';
        warn.style.left = '0';
        warn.style.right = '0';
        warn.style.top = '0';
        warn.style.background = '#ffebeb';
        warn.style.color = '#900';
        warn.style.padding = '8px 12px';
        warn.style.zIndex = '4000';
        warn.style.textAlign = 'center';
        warn.textContent = 'Warning: real-time connection (socket.io) failed to load. Check network or place socket.io.min.js in /static/.';
        document.body.appendChild(warn);
    });
    socket = createStubSocket();
} else {
    socket = io();
}

// Состояние приложения
let currentUsername = '';
let currentUserColor = '';
let isAdmin = false;
let selectedUser = null;
let currentLang = 'he'; // Default Hebrew
let translations = {};

// Элементы DOM - Authentication
const authScreen = document.getElementById('auth-screen');
const registerForm = document.getElementById('register-form');
const loginForm = document.getElementById('login-form');
const registerUsername = document.getElementById('register-username');
const registerPassword = document.getElementById('register-password');
const loginUsername = document.getElementById('login-username');
const loginPassword = document.getElementById('login-password');
const registerBtn = document.getElementById('register-btn');
const loginBtn = document.getElementById('login-btn');
const switchToLogin = document.getElementById('switch-to-login');
const switchToRegister = document.getElementById('switch-to-register');
const registerError = document.getElementById('register-error');
const loginError = document.getElementById('login-error');
const registerSuccess = document.getElementById('register-success');

// Элементы DOM - Chat
const chatScreen = document.getElementById('chat-screen');
const currentUsernameDisplay = document.getElementById('current-username');
const adminBadge = document.getElementById('admin-badge');
const onlineCount = document.getElementById('online-count');
const usersList = document.getElementById('users-list');

const publicMessages = document.getElementById('public-messages');
const publicInput = document.getElementById('public-input');
const publicSendBtn = document.getElementById('public-send-btn');

const teacherbotMessages = document.getElementById('teacherbot-messages');
const teacherbotInput = document.getElementById('teacherbot-input');
const teacherbotSendBtn = document.getElementById('teacherbot-send-btn');

const contextMenu = document.getElementById('context-menu');
const privateModal = document.getElementById('private-modal');
const privateRecipient = document.getElementById('private-recipient');
const privateMessageInput = document.getElementById('private-message-input');
const sendPrivateBtn = document.getElementById('send-private-btn');

// Вкладки
const tabButtons = document.querySelectorAll('.tab-btn');
const chatContents = document.querySelectorAll('.chat-content');

// Language buttons
const langButtons = document.querySelectorAll('.lang-btn');

// === INITIALIZATION ===
async function initApp() {
    await loadTranslations();
    setLanguage('he'); // Default to Hebrew
    setupEventListeners();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

// === TRANSLATIONS ===
async function loadTranslations() {
    try {
        const response = await fetch('/static/translations.json');
        translations = await response.json();
    } catch (error) {
        console.error('Failed to load translations:', error);
        translations = { en: {}, ru: {}, he: {} };
    }
}

function setLanguage(lang) {
    currentLang = lang;
    
    // Update active button
    langButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.lang === lang);
    });
    
    // Set direction
    const html = document.documentElement;
    html.setAttribute('lang', lang);
    html.setAttribute('dir', lang === 'he' ? 'rtl' : 'ltr');
    
    // Update all translated elements
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.dataset.i18n;
        el.textContent = t(key);
    });
    
    // Update placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.dataset.i18nPlaceholder;
        el.placeholder = t(key);
    });
}

function t(key) {
    const keys = key.split('.');
    let value = translations[currentLang];
    
    for (const k of keys) {
        if (value && value[k]) {
            value = value[k];
        } else {
            return key; // Return key if translation not found
        }
    }
    
    return value || key;
}

// === EVENT LISTENERS ===
function setupEventListeners() {
    // Language switching
    langButtons.forEach(btn => {
        btn.addEventListener('click', () => setLanguage(btn.dataset.lang));
    });
    
    // Authentication
    if (registerBtn) registerBtn.addEventListener('click', handleRegister);
    if (loginBtn) loginBtn.addEventListener('click', handleLogin);
    if (switchToLogin) switchToLogin.addEventListener('click', showLoginForm);
    if (switchToRegister) switchToRegister.addEventListener('click', showRegisterForm);
    
    if (registerPassword) {
        registerPassword.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleRegister();
        });
    }
    
    if (loginPassword) {
        loginPassword.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleLogin();
        });
    }
    
    // Chat
    if (publicSendBtn) publicSendBtn.addEventListener('click', sendPublicMessage);
    if (publicInput) {
        publicInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendPublicMessage();
        });
    }
    
    if (teacherbotSendBtn) teacherbotSendBtn.addEventListener('click', sendTeacherBotQuery);
    if (teacherbotInput) {
        teacherbotInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendTeacherBotQuery();
        });
    }
    
    // Private messages
    if (sendPrivateBtn) sendPrivateBtn.addEventListener('click', sendPrivateMessage);
    document.querySelectorAll('.close-btn').forEach(btn => {
        btn.addEventListener('click', closePrivateModal);
    });
    
    if (privateModal) {
        privateModal.addEventListener('click', (e) => {
            if (e.target === privateModal) closePrivateModal();
        });
    }
    
    document.addEventListener('click', () => {
        if (contextMenu) contextMenu.style.display = 'none';
    });
    
    const privateMessageBtn = document.getElementById('private-message-btn');
    if (privateMessageBtn) {
        privateMessageBtn.addEventListener('click', () => {
            if (contextMenu) contextMenu.style.display = 'none';
            if (selectedUser) openPrivateMessageModal(selectedUser);
        });
    }
    
    // Tabs
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tab = button.dataset.tab;
            
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            chatContents.forEach(content => content.classList.remove('active'));
            
            if (tab === 'public') {
                document.getElementById('public-chat').classList.add('active');
                publicInput.focus();
            } else if (tab === 'teacherbot') {
                document.getElementById('teacherbot-chat').classList.add('active');
                teacherbotInput.focus();
            }
        });
    });
}

// === AUTHENTICATION ===
function showRegisterForm() {
    registerForm.classList.add('active');
    loginForm.classList.remove('active');
    registerError.textContent = '';
    registerSuccess.textContent = '';
    loginError.textContent = '';
}

function showLoginForm() {
    loginForm.classList.add('active');
    registerForm.classList.remove('active');
    registerError.textContent = '';
    registerSuccess.textContent = '';
    loginError.textContent = '';
}

function handleRegister() {
    const username = registerUsername.value.trim();
    const password = registerPassword.value.trim();
    
    if (!username || !password) {
        showError(registerError, t('errors.login_required'));
        return;
    }
    
    socket.emit('register', { username, password });
}

function handleLogin() {
    const username = loginUsername.value.trim();
    const password = loginPassword.value.trim();
    
    if (!username || !password) {
        showError(loginError, t('errors.login_required'));
        return;
    }
    
    socket.emit('login', { username, password });
}

function showError(element, message) {
    if (!element) return;
    element.textContent = message;
    setTimeout(() => {
        if (element) element.textContent = '';
    }, 4000);
}

function showSuccess(element, message) {
    if (!element) return;
    element.textContent = message;
    setTimeout(() => {
        if (element) element.textContent = '';
    }, 3000);
}
// === SOCKET EVENTS ===
socket.on('register_success', (data) => {
    showSuccess(registerSuccess, t('success.registration_success'));
    registerUsername.value = '';
    registerPassword.value = '';
    setTimeout(() => showLoginForm(), 2000);
});

socket.on('register_error', (data) => {
    showError(registerError, t(`errors.${data.message}`));
});

socket.on('login_error', (data) => {
    showError(loginError, t(`errors.${data.message}`));
});

socket.on('join_success', (data) => {
    currentUsername = data.username;
    currentUserColor = data.color;
    isAdmin = data.is_admin;
    
    // Переключение экранов
    authScreen.classList.remove('active');
    chatScreen.classList.add('active');
    
    // Обновление UI
    currentUsernameDisplay.textContent = currentUsername;
    currentUsernameDisplay.style.color = currentUserColor;
    if (isAdmin) {
        adminBadge.style.display = 'inline-block';
    }
    
    console.log(`Joined as ${currentUsername} (Admin: ${isAdmin})`);
});

socket.on('join_error', (data) => {
    showError(loginError, t(`errors.${data.message}`));
});

socket.on('user_joined', (data) => {
    addSystemMessage(`${data.username} ${t('joined_chat')}`, data.timestamp);
});

socket.on('user_left', (data) => {
    addSystemMessage(`${data.username} ${t('left_chat')}`, data.timestamp);
});

socket.on('users_update', (data) => {
    updateUsersList(data.users);
});

socket.on('public_message', (data) => {
    addPublicMessage(data);
});

socket.on('private_message', (data) => {
    addPrivateMessage(data);
});

socket.on('teacherbot_response', (data) => {
    addTeacherBotResponse(data);
});

socket.on('admin_status', (data) => {
    if (data.is_admin) {
        isAdmin = true;
        adminBadge.style.display = 'inline-block';
    }
});

socket.on('error', (data) => {
    alert(data.message);
});

socket.on('blocked', (data) => {
    if (data.username === currentUsername) {
        alert('You have been blocked by the admin and cannot send messages.');
    }
});

socket.on('unblocked', (data) => {
    if (data.username === currentUsername) {
        alert('You have been unblocked by the admin.');
    }
});

socket.on('user_blocked', (data) => {
    addSystemMessage(`${data.username} has been blocked by admin`, new Date().toLocaleTimeString());
});

socket.on('user_unblocked', (data) => {
    addSystemMessage(`${data.username} has been unblocked by admin`, new Date().toLocaleTimeString());
});

socket.on('remove_messages', (data) => {
    if (!data || !data.username) return;
    removeMessagesByUsername(data.username);
});

socket.on('user_deleted_broadcast', (data) => {
    addSystemMessage(`${data.username} was deleted by admin`, new Date().toLocaleTimeString());
});

socket.on('user_deleted', (data) => {
    // If this client was deleted, show info and return to auth
    if (data.username === currentUsername) {
        alert('Your account was deleted by admin.');
        window.location.reload();
    }
});

function removeMessagesByUsername(username) {
    document.querySelectorAll('.message').forEach(m => {
        const unameEl = m.querySelector('.message-username');
        if (!unameEl) return;
        // Exact match or contains
        if (unameEl.textContent && (unameEl.textContent === username || unameEl.textContent.indexOf(username) !== -1)) {
            m.remove();
        }
    });
}

// === ПУБЛИЧНЫЕ СООБЩЕНИЯ ===
function sendPublicMessage() {
    const message = publicInput.value.trim();
    if (!message) return;
    
    socket.emit('public_message', { message });
    publicInput.value = '';
}

function addPublicMessage(data) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    
    if (data.username === currentUsername) {
        messageDiv.classList.add('own');
    }
    
    if (data.is_admin) {
        messageDiv.classList.add('admin');
    }
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = data.username[0].toUpperCase();
    avatar.style.background = data.color || '#667eea';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const header = document.createElement('div');
    header.className = 'message-header';
    
    const username = document.createElement('span');
    username.className = 'message-username user-color';
    username.textContent = data.username;
    username.style.color = data.color || '#667eea';
    
    const time = document.createElement('span');
    time.className = 'message-time';
    time.textContent = data.timestamp;
    
    header.appendChild(username);
    header.appendChild(time);
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = data.message;
    
    content.appendChild(header);
    content.appendChild(bubble);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    publicMessages.appendChild(messageDiv);
    publicMessages.scrollTop = publicMessages.scrollHeight;
}

function addSystemMessage(message, timestamp) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = `${message} • ${timestamp}`;
    
    messageDiv.appendChild(bubble);
    publicMessages.appendChild(messageDiv);
    publicMessages.scrollTop = publicMessages.scrollHeight;
}

// === TEACHERBOT ===
function sendTeacherBotQuery() {
    const query = teacherbotInput.value.trim();
    if (!query) return;
    
    // Показываем вопрос пользователя
    addUserQueryToBot(query);
    
    // Отправляем запрос
    socket.emit('teacherbot_query', { query });
    teacherbotInput.value = '';
}

function addUserQueryToBot(query) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message own';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = currentUsername[0].toUpperCase();
    avatar.style.background = currentUserColor;
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = query;
    
    content.appendChild(bubble);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    teacherbotMessages.appendChild(messageDiv);
    teacherbotMessages.scrollTop = teacherbotMessages.scrollHeight;
    teacherbotInput.focus();
}

function addTeacherBotResponse(data) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '🤖';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const header = document.createElement('div');
    header.className = 'message-header';
    
    const username = document.createElement('span');
    username.className = 'message-username';
    username.textContent = 'TeacherBot';
    
    const time = document.createElement('span');
    time.className = 'message-time';
    time.textContent = data.timestamp;
    
    header.appendChild(username);
    header.appendChild(time);
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = data.message;
    
    content.appendChild(header);
    content.appendChild(bubble);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    teacherbotMessages.appendChild(messageDiv);
    teacherbotMessages.scrollTop = teacherbotMessages.scrollHeight;
    teacherbotInput.focus();
}

// === ПРИВАТНЫЕ СООБЩЕНИЯ ===
function updateUsersList(users) {
    usersList.innerHTML = '';
    onlineCount.textContent = users.length;
    
    users.forEach(user => {
        if (user.username === currentUsername) return; // Не показываем себя
        
        const userItem = document.createElement('div');
        userItem.className = 'user-item';
        userItem.dataset.username = user.username;
        
        const avatar = document.createElement('div');
        avatar.className = 'user-avatar';
        avatar.textContent = user.username[0].toUpperCase();
        avatar.style.background = user.color || '#667eea';
        
        const name = document.createElement('div');
        name.className = 'user-name';
        name.textContent = user.username;
        name.style.color = user.color || '#667eea';
        if (user.blocked) {
            const blockedMark = document.createElement('span');
            blockedMark.className = 'user-blocked';
            blockedMark.textContent = ' (blocked)';
            name.appendChild(blockedMark);
            userItem.classList.add('blocked');
        }
        
        userItem.appendChild(avatar);
        userItem.appendChild(name);
        
        if (user.is_admin) {
            const adminIcon = document.createElement('span');
            adminIcon.className = 'admin-indicator';
            adminIcon.textContent = '👑';
            userItem.appendChild(adminIcon);
        }
        
        // Правый клик для приватного сообщения
        userItem.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            showContextMenu(e.pageX, e.pageY, user.username, user);
        });
        
        // Двойной клик для приватного сообщения
        userItem.addEventListener('dblclick', () => {
            openPrivateMessageModal(user.username);
        });
        
        usersList.appendChild(userItem);
    });
}

function showContextMenu(x, y, username) {
    selectedUser = username;
    // Build dynamic context menu
    contextMenu.innerHTML = '';

    // Private message button
    const pmBtn = document.createElement('button');
    pmBtn.id = 'private-message-btn';
    pmBtn.textContent = t('private_message') || 'Private Message';
    pmBtn.addEventListener('click', () => {
        contextMenu.style.display = 'none';
        openPrivateMessageModal(selectedUser);
    });
    contextMenu.appendChild(pmBtn);

    // Admin controls
    if (isAdmin) {
        const hr = document.createElement('hr');
        contextMenu.appendChild(hr);

        const blockBtn = document.createElement('button');
        blockBtn.id = 'admin-block-btn';
        blockBtn.textContent = 'Block';
        blockBtn.addEventListener('click', () => {
            contextMenu.style.display = 'none';
            if (confirm('Block user ' + selectedUser + '?')) {
                socket.emit('block_user', { username: selectedUser });
            }
        });
        contextMenu.appendChild(blockBtn);

        const unblockBtn = document.createElement('button');
        unblockBtn.id = 'admin-unblock-btn';
        unblockBtn.textContent = 'Unblock';
        unblockBtn.addEventListener('click', () => {
            contextMenu.style.display = 'none';
            socket.emit('unblock_user', { username: selectedUser });
        });
        contextMenu.appendChild(unblockBtn);

        const deleteBtn = document.createElement('button');
        deleteBtn.id = 'admin-delete-btn';
        deleteBtn.textContent = 'Delete';
        deleteBtn.addEventListener('click', () => {
            contextMenu.style.display = 'none';
            if (confirm('Delete user ' + selectedUser + ' and optionally remove their messages?')) {
                socket.emit('delete_user', { username: selectedUser });
            }
        });
        contextMenu.appendChild(deleteBtn);
    }

    contextMenu.style.display = 'block';
    contextMenu.style.left = x + 'px';
    contextMenu.style.top = y + 'px';
}

function openPrivateMessageModal(username) {
    selectedUser = username;
    privateRecipient.textContent = username;
    privateMessageInput.value = '';
    privateModal.style.display = 'flex';
    privateMessageInput.focus();
}

function sendPrivateMessage() {
    const message = privateMessageInput.value.trim();
    if (!message || !selectedUser) return;
    
    socket.emit('private_message', {
        to: selectedUser,
        message: message
    });
    
    closePrivateModal();
}

function closePrivateModal() {
    privateModal.style.display = 'none';
    selectedUser = null;
}

function addPrivateMessage(data) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message private';
    
    const isOwn = data.from === currentUsername;
    if (isOwn) {
        messageDiv.classList.add('own');
    }
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = isOwn ? data.to[0].toUpperCase() : data.from[0].toUpperCase();
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const header = document.createElement('div');
    header.className = 'message-header';
    
    const username = document.createElement('span');
    username.className = 'message-username';
    
    const dir = document.documentElement.getAttribute('dir');
    if (dir === 'rtl') {
        username.textContent = isOwn ? `${data.to} ← ${t('you')}` : `${t('you')} ← ${data.from}`;
    } else {
        username.textContent = isOwn ? `${t('you')} → ${data.to}` : `${data.from} → ${t('you')}`;
    }
    
    const time = document.createElement('span');
    time.className = 'message-time';
    time.textContent = data.timestamp;
    
    header.appendChild(username);
    header.appendChild(time);
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = data.message;
    
    content.appendChild(header);
    content.appendChild(bubble);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    publicMessages.appendChild(messageDiv);
    publicMessages.scrollTop = publicMessages.scrollHeight;
}

// === УТИЛИТЫ ===
console.log('School Auto Chat - Client Ready (Multilingual Support)');
