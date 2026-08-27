self.addEventListener('push', function(event) {
  let payload = {
    title: 'Guntur Municipal Corporation',
    body: 'New municipal alert available.',
  };

  if (event.data) {
    try {
      payload = Object.assign(payload, event.data.json());
    } catch (error) {
      payload.body = event.data.text();
    }
  }

  event.waitUntil(
    self.registration.showNotification(payload.title, {
      body: payload.body,
      icon: '/static/img/guntur-municipal-corporation-logo.jpg',
      badge: '/static/img/guntur-municipal-corporation-logo.jpg',
      data: payload.url || '/',
    })
  );
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  event.waitUntil(clients.openWindow(event.notification.data || '/'));
});
