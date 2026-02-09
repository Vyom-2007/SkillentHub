/**
 * Notifications JavaScript
 * Handles polling for unread count and dropdown interactions
 */

// ========== POLLING ==========

let pollInterval = null;

function startNotificationPolling() {
    // Initial fetch
    fetchUnreadCount();
    fetchRecentNotifications();

    // Poll every 5 seconds for count only (lightweight)
    pollInterval = setInterval(fetchUnreadCount, 5000);
}

function stopNotificationPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

function fetchUnreadCount() {
    fetch('/api/notifications/unread-count')
        .then(res => res.json())
        .then(data => {
            updateBadge(data.count);
        })
        .catch(() => { });
}

function updateBadge(count) {
    const badge = document.getElementById('notificationBadge');
    if (!badge) return;

    if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.classList.remove('d-none');
    } else {
        badge.classList.add('d-none');
    }
}

// ========== DROPDOWN ==========

function fetchRecentNotifications() {
    fetch('/api/notifications/recent')
        .then(res => res.json())
        .then(data => {
            renderNotificationDropdown(data.notifications);
        })
        .catch(() => {
            const list = document.getElementById('notificationList');
            if (list) {
                list.innerHTML = '<div class="text-center py-3 text-muted">Failed to load</div>';
            }
        });
}

function renderNotificationDropdown(notifications) {
    const list = document.getElementById('notificationList');
    if (!list) return;

    if (notifications.length === 0) {
        list.innerHTML = `
            <div class="text-center py-4 text-muted">
                <i class="bi bi-bell-slash"></i>
                <p class="small mb-0 mt-2">No notifications</p>
            </div>
        `;
        return;
    }

    list.innerHTML = notifications.map(n => `
        <div class="notification-item ${n.is_read ? '' : 'unread'}" 
             data-id="${n.id}" onclick="handleNotificationClick(${n.id}, '${n.type}', ${n.related_id || 'null'})">
            <div class="icon">
                <i class="${n.icon}"></i>
            </div>
            <div class="content">
                <p>${escapeHtml(n.content)}</p>
                <div class="time">${n.time_ago}</div>
            </div>
        </div>
    `).join('');
}

function handleNotificationClick(id, type, relatedId) {
    // Mark as read
    fetch(`/api/notifications/mark-read/${id}`, { method: 'POST' });

    // Navigate based on type
    let url = '/notifications';
    if (type === 'new_message' && relatedId) {
        url = `/messages?user=${relatedId}`;
    } else if (type === 'post_like' || type === 'post_comment') {
        url = '/feed';
    } else if (type === 'application_update') {
        url = '/applications';
    }

    window.location.href = url;
}

function markAllNotificationsRead() {
    fetch('/api/notifications/mark-all-read', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                updateBadge(0);
                // Clear the dropdown and show empty state
                const list = document.getElementById('notificationList');
                if (list) {
                    list.innerHTML = `
                        <div class="text-center py-4 text-muted">
                            <i class="bi bi-bell-slash"></i>
                            <p class="small mb-0 mt-2">No notifications</p>
                        </div>
                    `;
                }
            }
        });
}

// ========== UTILITIES ==========

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========== INITIALIZATION ==========

document.addEventListener('DOMContentLoaded', function () {
    // Start polling if user is logged in (check for badge element)
    if (document.getElementById('notificationBadge')) {
        startNotificationPolling();

        // Fetch recent when dropdown is opened
        const dropdown = document.getElementById('notificationsDropdown');
        if (dropdown) {
            dropdown.addEventListener('show.bs.dropdown', fetchRecentNotifications);
        }

        // Mark all read button
        const markAllBtn = document.getElementById('markAllReadBtn');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                markAllNotificationsRead();
            });
        }
    }
});

// Global exports
window.fetchUnreadCount = fetchUnreadCount;
window.handleNotificationClick = handleNotificationClick;
