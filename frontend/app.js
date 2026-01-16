/**
 * 小伴 - AI 陪伴助手
 * 前端 JavaScript
 */

const API_BASE = ''; // 同源，无需设置

// DOM 元素
const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('input');
const sendBtn = document.getElementById('send-btn');
const quickActionsEl = document.getElementById('quick-actions');
const statusIndicator = document.getElementById('status-indicator');

// 当前对话 ID
let threadId = 'main_chat';

// ==================== 消息显示 ====================

function addMessage(content, type = 'user') {
    const div = document.createElement('div');
    div.className = `message ${type}`;

    if (type === 'assistant') {
        div.innerHTML = `<div class="sender">小伴:</div>${escapeHtml(content)}`;
    } else if (type === 'command') {
        div.innerHTML = content; // 命令结果可能包含格式
    } else {
        div.textContent = content;
    }

    messagesEl.appendChild(div);
    scrollToBottom();
    return div;
}

function addTypingIndicator() {
    const div = document.createElement('div');
    div.className = 'message assistant';
    div.id = 'typing';
    div.innerHTML = `<div class="sender">小伴:</div><div class="typing"><span></span><span></span><span></span></div>`;
    messagesEl.appendChild(div);
    scrollToBottom();
}

function removeTypingIndicator() {
    const typing = document.getElementById('typing');
    if (typing) typing.remove();
}

function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== API 调用 ====================

function addAgentMessage(emoji, name, content) {
    const div = document.createElement('div');
    div.className = 'message assistant';
    div.innerHTML = `<div class="sender">${emoji} ${name}:</div>${escapeHtml(content)}`;
    messagesEl.appendChild(div);
    scrollToBottom();
    return div;
}

async function sendMessage(message) {
    // 显示用户消息
    addMessage(message, 'user');
    inputEl.value = '';

    // 显示加载状态
    addTypingIndicator();
    setStatus('thinking');

    try {
        // 使用多 Agent API
        const response = await fetch(`${API_BASE}/api/chat/multi`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, thread_id: threadId })
        });

        removeTypingIndicator();

        if (!response.ok) {
            throw new Error('请求失败');
        }

        const data = await response.json();

        // 显示所有 Agent 的回复
        for (const r of data.responses) {
            addAgentMessage(r.emoji, r.agent_name, r.response);
        }

        if (data.extracted_count > 0) {
            addMessage(`💡 [已自动记录 ${data.extracted_count} 条信息]`, 'system');
        }

        setStatus('online');
    } catch (error) {
        removeTypingIndicator();
        addMessage(`错误: ${error.message}`, 'error');
        setStatus('error');
    }
}

async function sendCommand(command) {
    addMessage(command, 'user');

    try {
        const response = await fetch(`${API_BASE}/api/status/record`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command })
        });

        const data = await response.json();
        addMessage(data.message, 'command');
    } catch (error) {
        addMessage(`错误: ${error.message}`, 'error');
    }
}

async function getStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/status/today`);
        const data = await response.json();

        if (data.statuses.length === 0) {
            addMessage('📭 今日暂无记录', 'command');
            return;
        }

        let html = '📊 <strong>今日状态</strong><br>─────────────<br>';
        for (const s of data.statuses) {
            const sourceTag = s.source === 'ai' ? ' [AI]' : '';
            const detail = s.detail ? ` - ${s.detail}` : '';
            html += `${s.time} ${s.type}${detail}${sourceTag}<br>`;
        }
        html += '─────────────';

        addMessage(html, 'command');
    } catch (error) {
        addMessage(`错误: ${error.message}`, 'error');
    }
}

// ==================== 状态指示器 ====================

function setStatus(status) {
    const colors = {
        online: '#7ee787',
        thinking: '#d29922',
        error: '#f85149'
    };
    statusIndicator.style.color = colors[status] || colors.online;
}

// ==================== 事件处理 ====================

function handleSend() {
    const message = inputEl.value.trim();
    if (!message) return;

    if (message.startsWith('/')) {
        if (message === '/status') {
            addMessage(message, 'user');
            getStatus();
        } else {
            sendCommand(message);
        }
    } else {
        sendMessage(message);
    }
}

// 发送按钮
sendBtn.addEventListener('click', handleSend);

// 回车发送
inputEl.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleSend();
    }
});

// 快捷按钮
quickActionsEl.addEventListener('click', (e) => {
    if (e.target.classList.contains('quick-btn')) {
        const cmd = e.target.dataset.cmd;
        if (cmd === '/status') {
            addMessage(cmd, 'user');
            getStatus();
        } else {
            sendCommand(cmd);
        }
    }
});

// ==================== PWA 注册 ====================

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js')
        .then(() => console.log('Service Worker 已注册'))
        .catch(err => console.log('Service Worker 注册失败', err));
}
