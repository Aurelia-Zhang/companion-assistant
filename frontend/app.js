/**
 * AI Companion v1.2 - Session-based Frontend
 * Matches CLI flow: select/create session first
 */

const API_BASE = '';
const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('input');
const sendBtn = document.getElementById('send-btn');
const quickActionsEl = document.getElementById('quick-actions');
const statusIndicator = document.getElementById('status-indicator');

let currentSession = null;
let sessionList = [];

// ==================== UI Helpers ====================

function formatTime() {
    return new Date().toTimeString().slice(0, 8);
}

function clearMessages() {
    messagesEl.innerHTML = '';
}

function addMessage(sender, content, type = 'user') {
    const div = document.createElement('div');
    div.className = `message ${type}`;

    const senderDiv = document.createElement('div');
    senderDiv.className = 'sender';
    senderDiv.textContent = `[${sender} ${formatTime()}]`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'content';
    contentDiv.textContent = content;

    div.appendChild(senderDiv);
    div.appendChild(contentDiv);
    messagesEl.appendChild(div);
    scrollToBottom();
}

function addSystemMessage(content) {
    const div = document.createElement('div');
    div.className = 'message system';
    div.style.whiteSpace = 'pre-wrap';
    div.textContent = content;
    messagesEl.appendChild(div);
    scrollToBottom();
}

function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setStatus(status) {
    statusIndicator.textContent = status;
}

// ==================== Session Management ====================

function showMainMenu() {
    currentSession = null;
    quickActionsEl.style.display = 'none';
    clearMessages();

    let menu = `Commands:
  @agent      - new private chat
  @a @b       - new group chat
  /list       - show sessions
  /agents     - show agents`;

    addSystemMessage(menu);
    inputEl.placeholder = '@agent or /command';
}

async function showSessionList() {
    try {
        const response = await fetch(`${API_BASE}/api/chat/sessions`);
        if (!response.ok) {
            addSystemMessage('No sessions yet. Use @agent to start.');
            return;
        }
        sessionList = await response.json();

        if (sessionList.length === 0) {
            addSystemMessage('No sessions. Use @agent to start chat.');
            return;
        }

        let text = 'Sessions:\n';
        sessionList.forEach((s, i) => {
            text += `${i + 1}. [${s.type}] ${s.title}\n`;
        });
        text += '\nUse /join <number> to enter';
        addSystemMessage(text);
    } catch (error) {
        addSystemMessage('No sessions yet. Use @agent to start.');
    }
}

async function showAgents() {
    try {
        const response = await fetch(`${API_BASE}/api/chat/agents`);
        const agents = await response.json();  // returns array directly

        let text = 'Available agents:\n';
        for (const a of agents) {
            text += `  @${a.name} (${a.id})\n`;
        }
        addSystemMessage(text);
    } catch (error) {
        addSystemMessage('Error loading agents');
    }
}

function startChat(agents) {
    currentSession = {
        agents: agents,
        type: agents.length === 1 ? 'private' : 'group',
        session_id: null  // Will be set after first message
    };

    quickActionsEl.style.display = 'flex';
    clearMessages();

    const agentNames = agents.join(', ');
    if (agents.length === 1) {
        addSystemMessage(`Private chat with ${agentNames}\nType message or /quit to exit`);
    } else {
        addSystemMessage(`Group chat with ${agentNames}\nType message or /quit to exit`);
    }

    inputEl.placeholder = 'message...';
}

async function joinSession(sessionInfo) {
    // Load session history from API
    try {
        const response = await fetch(`${API_BASE}/api/chat/sessions/${sessionInfo.id}/history`);
        if (!response.ok) {
            addSystemMessage('Failed to load session');
            return;
        }
        const data = await response.json();

        // Set current session
        currentSession = {
            agents: sessionInfo.agents,
            type: sessionInfo.type,
            session_id: sessionInfo.id,
            title: sessionInfo.title
        };

        quickActionsEl.style.display = 'flex';
        clearMessages();

        addSystemMessage(`Joined: ${sessionInfo.title}\n/quit to exit, /rename <name> to rename`);

        // Display history
        for (const msg of data.messages || []) {
            if (msg.role === 'user') {
                addMessage('user', msg.content, 'user');
            } else {
                addMessage(msg.agent_id || 'assistant', msg.content, 'assistant');
            }
        }

        inputEl.placeholder = 'message...';
    } catch (error) {
        addSystemMessage('Failed to join session: ' + error.message);
    }
}

// ==================== Chat ====================

async function sendChatMessage(message) {
    addMessage('user', message, 'user');
    inputEl.value = '';
    setStatus('thinking...');

    try {
        const response = await fetch(`${API_BASE}/api/chat/send`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message,
                session_id: currentSession.session_id || null,
                agent_ids: currentSession.agents
            })
        });

        if (!response.ok) throw new Error('request failed');

        const data = await response.json();

        // 更新 session_id
        currentSession.session_id = data.session_id;

        for (const r of data.responses) {
            addMessage(r.agent_name || r.agent_id, r.content, 'assistant');
        }

        setStatus('online');
    } catch (error) {
        addMessage('error', error.message, 'error');
        setStatus('error');
    }
}

async function sendCommand(command) {
    try {
        const response = await fetch(`${API_BASE}/api/command/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command })
        });
        const data = await response.json();
        addSystemMessage(data.message);
    } catch (error) {
        addSystemMessage('Command failed: ' + error.message);
    }
}

// ==================== Input Handler ====================

function handleInput() {
    const input = inputEl.value.trim();
    if (!input) return;
    inputEl.value = '';

    // In main menu mode
    if (!currentSession) {
        if (input === '/list') {
            showSessionList();
        } else if (input === '/agents') {
            showAgents();
        } else if (input === '/push') {
            subscribeToPush();
        } else if (input === '/testpush') {
            testPush();
        } else if (input.startsWith('/join ')) {
            const num = parseInt(input.substring(6)) - 1;
            if (sessionList[num]) {
                joinSession(sessionList[num]);
            } else {
                addSystemMessage('Invalid session number. Use /list first.');
            }
        } else if (input.startsWith('@')) {
            const mentions = input.match(/@(\w+)/g);
            if (mentions) {
                const agents = mentions.map(m => m.substring(1));
                startChat(agents);
            } else {
                addSystemMessage('Usage: @agent_name');
            }
        } else if (input.startsWith('/')) {
            // Send all other / commands to backend
            sendCommand(input);
        } else {
            addSystemMessage('Use @agent to start chat, or /help for commands');
        }
        return;
    }

    // In chat mode
    if (input === '/quit') {
        showMainMenu();
        return;
    }

    if (input.startsWith('/rename ')) {
        const newTitle = input.substring(8).trim();
        if (!newTitle) {
            addSystemMessage('Usage: /rename <new title>');
            return;
        }
        if (currentSession && currentSession.session_id) {
            renameSession(currentSession.session_id, newTitle);
        } else {
            addSystemMessage('Cannot rename: no session ID yet. Send a message first.');
        }
        return;
    }

    if (input.startsWith('/')) {
        sendCommand(input);
        return;
    }

    sendChatMessage(input);
}

async function renameSession(sessionId, newTitle) {
    try {
        const response = await fetch(`${API_BASE}/api/chat/sessions/${sessionId}/rename`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: newTitle })
        });
        if (response.ok) {
            if (currentSession) {
                currentSession.title = newTitle;
            }
            addSystemMessage(`✅ Renamed to: ${newTitle}`);
        } else {
            addSystemMessage('Failed to rename session');
        }
    } catch (error) {
        addSystemMessage('Rename failed: ' + error.message);
    }
}

// ==================== Event Listeners ====================

sendBtn.addEventListener('click', handleInput);
inputEl.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleInput();
});

quickActionsEl.addEventListener('click', (e) => {
    if (e.target.classList.contains('quick-btn')) {
        const cmd = e.target.dataset.cmd;
        if (cmd === '/quit') {
            showMainMenu();
        } else {
            inputEl.value = cmd;
            handleInput();
        }
    }
});

// ==================== Push Notifications ====================

// VAPID 公钥 - 需要替换为实际的公钥
const VAPID_PUBLIC_KEY = window.VAPID_PUBLIC_KEY || '';

function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

async function subscribeToPush() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        addSystemMessage('❌ 此浏览器不支持推送通知');
        return;
    }

    try {
        // 请求通知权限
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
            addSystemMessage('❌ 推送通知权限被拒绝');
            return;
        }

        // 获取 VAPID 公钥
        let vapidKey = VAPID_PUBLIC_KEY;
        if (!vapidKey) {
            const response = await fetch(`${API_BASE}/api/push/vapid-key`);
            const data = await response.json();
            vapidKey = data.publicKey;
        }

        if (!vapidKey) {
            addSystemMessage('❌ VAPID 公钥未配置');
            return;
        }

        // 订阅
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(vapidKey)
        });

        // 发送订阅信息到后端
        await fetch(`${API_BASE}/api/push/subscribe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                endpoint: subscription.endpoint,
                keys: {
                    p256dh: btoa(String.fromCharCode.apply(null, new Uint8Array(subscription.getKey('p256dh')))),
                    auth: btoa(String.fromCharCode.apply(null, new Uint8Array(subscription.getKey('auth'))))
                }
            })
        });

        addSystemMessage('✅ 推送通知已订阅！');
    } catch (error) {
        addSystemMessage(`❌ 订阅失败: ${error.message}`);
    }
}

async function testPush() {
    try {
        const response = await fetch(`${API_BASE}/api/push/test`, { method: 'POST' });
        const data = await response.json();
        addSystemMessage(`📲 测试推送已发送 (${data.sent} 个订阅)`);
    } catch (error) {
        addSystemMessage('❌ 测试推送失败');
    }
}

// ==================== Init ====================

showMainMenu();

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch(() => { });
}

// 添加推送相关命令提示
const originalShowMainMenu = showMainMenu;
showMainMenu = function () {
    currentSession = null;
    quickActionsEl.style.display = 'none';
    clearMessages();

    let menu = `Commands:
  @agent      - new private chat
  @a @b       - new group chat
  /list       - show sessions
  /agents     - show agents
  /push       - subscribe to notifications
  /testpush   - test push notification`;

    addSystemMessage(menu);
    inputEl.placeholder = '@agent or /command';
};

// 扩展命令处理
const originalHandleInput = handleInput;
handleInput = function () {
    const input = inputEl.value.trim();

    if (!currentSession) {
        if (input === '/push') {
            inputEl.value = '';
            subscribeToPush();
            return;
        }
        if (input === '/testpush') {
            inputEl.value = '';
            testPush();
            return;
        }
    }

    originalHandleInput.call(this);
};

// 重新显示菜单
showMainMenu();
