/**
 * Global Notifications JavaScript
 * Handles real-time updates for the notification badge
 */

document.addEventListener('DOMContentLoaded', function () {
    // Initial check
    updateNotificationBadge();

    // Poll every 5 seconds
    const notificationInterval = setInterval(updateNotificationBadge, 5000);

    // Cleanup on page unload
    window.addEventListener('beforeunload', function () {
        clearInterval(notificationInterval);
    });
});

async function updateNotificationBadge() {
    const badge = document.getElementById('notificationBadge');
    if (!badge) return;

    try {
        const response = await fetch('/api/notifications/unread-count');

        if (response.status === 401) {
            // User session expired, stop polling silently
            return;
        }

        if (response.ok) {
            const data = await response.json();
            const count = data.count;

            // Update badge text
            badge.textContent = count > 99 ? '99+' : count;

            // Show/Hide badge based on count
            if (count > 0) {
                badge.classList.remove('d-none');
            } else {
                badge.classList.add('d-none');
            }
        }
    } catch (error) {
        // Silent failure for polling errors (network issues etc)
        console.warn('Failed to fetch notification count:', error);
    }
}
