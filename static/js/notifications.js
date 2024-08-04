// static/js/notifications.js
document.addEventListener('DOMContentLoaded', () => {
    if (Notification.permission === "default") {
        Notification.requestPermission();
    }
});

function notifyUser(title, message) {
    if (Notification.permission === "granted") {
        new Notification(title, { body: message });
    }
}

function checkNotifications() {
    // This function would typically fetch notification times from the server
    // or local storage and compare with the current time to trigger notifications.
}

setInterval(checkNotifications, 60000); // Check every minute
