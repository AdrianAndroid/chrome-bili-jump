/* 极简 Service Worker：只用于满足安装条件，不做任何缓存或改写。
   所有请求都交回浏览器默认处理（fetch 监听器不调用 respondWith）。 */
self.addEventListener("install", function () {
  self.skipWaiting();
});

self.addEventListener("activate", function (event) {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", function () {
  // 故意留空：不改写、不缓存、不拦截任何请求。
});
