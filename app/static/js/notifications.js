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

    // Dropdown Event Listeners
    const dropdown = document.getElementById('notificationsDropdown');
    if (dropdown) {
        dropdown.addEventListener('show.bs.dropdown', loadNotifications);
    }

    // Mark All Read Handler
    const markAllBtn = document.getElementById('markAllReadBtn');
    if (markAllBtn) {
        markAllBtn.addEventListener('click', markAllAsRead);
    }
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

async function loadNotifications() {
    const list = document.getElementById('notificationList');
    if (!list) return;

    // Show spinner if not already showing (and not just empty)
    // Actually, best to just render spinner on first load or refresh
    // But for now, let's just fetch. Use existing spinner if present.

    try {
        const response = await fetch('/api/notifications/recent');
        if (response.ok) {
            const data = await response.json();
            renderNotifications(data.notifications);
        } else {
            list.innerHTML = '<div class="text-center py-3 text-danger"><small>Failed to load</small></div>';
        }
    } catch (error) {
        console.error('Error loading notifications:', error);
        list.innerHTML = '<div class="text-center py-3 text-danger"><small>Error loading notifications</small></div>';
    }
}

function renderNotifications(notifications) {
    const list = document.getElementById('notificationList');
    if (!list) return;

    if (!notifications || notifications.length === 0) {
        list.innerHTML = '<div class="text-center py-3 text-muted"><small>No new notifications</small></div>';
        return;
    }

    let html = '';
    notifications.forEach(n => {
        const iconClass = n.icon || 'bi-bell';
        const unreadClass = !n.is_read ? 'unread' : '';
        const link = getNotificationLink(n);

        html += `
            <a href="${link}" class="text-decoration-none text-dark" onclick="markAsRead(${n.id})">
                <div class="notification-item ${unreadClass}">
                    <div class="icon">
                        <i class="bi ${iconClass} text-primary"></i>
                    </div>
                    <div class="content">
                        <p>${n.content}</p>
                        <div class="time">${n.time_ago}</div>
                    </div>
                </div>
            </a>
        `;
    });

    list.innerHTML = html;
}

function getNotificationLink(notification) {
    // Generate link based on type and related_id
    // Adjust routes as per your application
    const type = notification.type;
    const id = notification.related_id;

    if (type === 'connection_request') return '/network/requests';
    if (type === 'connection_accepted') return `/profile/${id}`; // id is user_id
    if (type === 'message') return '/messages';
    if (type === 'post_like' || type === 'post_comment') return `/posts/${id}`; // id is post_id
    if (type === 'application_update') return '/my-applications';
    if (type === 'team_invitation') return '/teams/invitations';

    return '/notifications'; // Fallback
}

async function markAsRead(notificationId) {
    try {
        await fetch(`/api/notifications/mark-read/${notificationId}`, { method: 'POST' });
        updateNotificationBadge(); // Refresh badge
    } catch (e) {
        console.error('Error marking read:', e);
    }
}

async function markAllAsRead(e) {
    e.preventDefault();
    e.stopPropagation();

    try {
        const response = await fetch('/api/notifications/mark-all-read', { method: 'POST' });
        if (response.ok) {
            updateNotificationBadge();
            loadNotifications(); // Reload list to remove unread styling
        }
    } catch (error) {
        console.error('Error marking all read:', error);
    }
}
