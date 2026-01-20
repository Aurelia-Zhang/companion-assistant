// Service Worker - 支持离线缓存和推送通知
const CACHE_NAME = 'xiaoban-v5';
const ASSETS = [
    '/',
    '/index.html',
    '/style.css',
    '/app.js',
    '/manifest.json'
];

// 安装时缓存资源
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(ASSETS))
    );
});

// 请求时优先使用网络，失败则使用缓存
self.addEventListener('fetch', (event) => {
    // API 请求不缓存
    if (event.request.url.includes('/api/')) {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .catch(() => caches.match(event.request))
    );
});

// 处理推送通知
self.addEventListener('push', (event) => {
    let data = { title: 'AI 陪伴助手', body: '你有一条新消息' };

    try {
        data = event.data.json();
    } catch (e) {
        data.body = event.data.text();
    }

    const options = {
        body: data.body,
        icon: data.icon || '/icon-192.png',
        badge: data.badge || '/icon-192.png',
        vibrate: [200, 100, 200],
        data: {
            url: data.url || '/'
        }
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// 点击通知时打开应用
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    event.waitUntil(
        clients.matchAll({ type: 'window' }).then(windowClients => {
            // 如果已有窗口，激活它
            for (const client of windowClients) {
                if (client.url === '/' && 'focus' in client) {
                    return client.focus();
                }
            }
            // 否则打开新窗口
            if (clients.openWindow) {
                return clients.openWindow(event.notification.data.url || '/');
            }
        })
    );
});
