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
        const response = await fetch(`${API_BASE}/api/sessions`);
        if (!response.ok) {
            // API not exist, show placeholder
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
        thread_id: `session_${Date.now()}`
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

// ==================== Chat ====================

async function sendChatMessage(message) {
    addMessage('user', message, 'user');
    inputEl.value = '';
    setStatus('thinking...');

    try {
        const response = await fetch(`${API_BASE}/api/chat/multi`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message,
                thread_id: currentSession.thread_id
            })
        });

        if (!response.ok) throw new Error('request failed');

        const data = await response.json();

        for (const r of data.responses) {
            addMessage(r.agent_name, r.response, 'assistant');
        }

        setStatus('online');
    } catch (error) {
        addMessage('error', error.message, 'error');
        setStatus('error');
    }
}

async function sendCommand(command) {
    try {
        const response = await fetch(`${API_BASE}/api/status/record`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command })
        });
        const data = await response.json();
        addSystemMessage(data.message);
    } catch (error) {
        addSystemMessage('Command failed');
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
                // Would need API to load session
                addSystemMessage('Joining session... (not implemented yet)');
            } else {
                addSystemMessage('Invalid session number');
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
            addSystemMessage('Unknown command. Use /list, /agents, /push, or @agent');
        } else {
            addSystemMessage('Use @agent to start chat');
        }
        return;
    }

    // In chat mode
    if (input === '/quit') {
        showMainMenu();
        return;
    }

    if (input.startsWith('/')) {
        sendCommand(input);
        return;
    }

    sendChatMessage(input);
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
