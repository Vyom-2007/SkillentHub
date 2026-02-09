/**
 * Messages JavaScript
 * Handles sending, polling, and UI updates for direct messaging
 */

// ========== INITIALIZATION ==========

let targetUserId = null;
let lastMessageId = 0;
let currentUserId = null;
let pollingInterval = null;

document.addEventListener('DOMContentLoaded', function () {
    targetUserId = parseInt(document.getElementById('targetUserId')?.value) || null;
    lastMessageId = parseInt(document.getElementById('lastMessageId')?.value) || 0;
    currentUserId = parseInt(document.getElementById('currentUserId')?.value) || null;

    initMessageInput();
    initSearchFilter();
    scrollToBottom();

    // Start polling if in a chat
    if (targetUserId) {
        startPolling();
    }

    // Always poll for unread counts
    startGlobalPolling();
});

// ========== MESSAGE INPUT ==========

function initMessageInput() {
    const input = document.getElementById('messageInput');
    if (input) {
        input.addEventListener('keypress', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        input.focus();
    }
}

// ========== SEND MESSAGE ==========

function sendMessage() {
    const input = document.getElementById('messageInput');
    const content = input?.value.trim();

    if (!content || !targetUserId) return;

    // Disable input while sending
    input.disabled = true;

    fetch('/api/messages/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            receiver_id: targetUserId,
            content: content
        })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Add message to UI
                appendMessage(data.message, true);
                // Update last message ID
                lastMessageId = data.message.message_id;
                // Clear input
                input.value = '';
                // Scroll to bottom
                scrollToBottom();
            } else {
                alert(data.error || 'Failed to send message');
            }
        })
        .catch(err => {
            console.error('Error sending message:', err);
            alert('Failed to send message');
        })
        .finally(() => {
            input.disabled = false;
            input.focus();
        });
}

// ========== APPEND MESSAGE ==========

function appendMessage(message, isSent) {
    const container = document.getElementById('chatMessages');
    if (!container) return;

    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${isSent ? 'message-sent' : 'message-received'}`;
    bubble.dataset.messageId = message.message_id;

    const time = message.created_at ? formatTime(new Date(message.created_at)) : '';

    bubble.innerHTML = `
        ${escapeHtml(message.content)}
        <div class="message-time">${time}</div>
    `;

    container.appendChild(bubble);
}

// ========== POLLING ==========

function startPolling() {
    // Poll every 5 seconds for new messages in current chat
    pollingInterval = setInterval(pollNewMessages, 5000);
}

function pollNewMessages() {
    if (!targetUserId) return;

    fetch(`/api/messages/${targetUserId}/new?since=${lastMessageId}`)
        .then(res => res.json())
        .then(data => {
            if (data.success && data.messages.length > 0) {
                data.messages.forEach(msg => {
                    appendMessage(msg, msg.sender_id === currentUserId);
                    lastMessageId = Math.max(lastMessageId, msg.message_id);
                });
                scrollToBottom();

                // Mark as read
                markAsRead(targetUserId);
            }
        })
        .catch(console.error);
}

function startGlobalPolling() {
    // Poll for unread counts every 10 seconds
    setInterval(updateUnreadCounts, 10000);
}

function updateUnreadCounts() {
    fetch('/api/messages/unread')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Update sidebar badges
                for (const [senderId, count] of Object.entries(data.by_sender)) {
                    const badge = document.getElementById(`unread-${senderId}`);
                    if (badge) {
                        badge.textContent = count;
                        badge.style.display = count > 0 ? 'inline' : 'none';
                    }
                }
            }
        })
        .catch(console.error);
}

function markAsRead(userId) {
    fetch(`/api/messages/${userId}/read`, { method: 'POST' })
        .catch(console.error);
}

// ========== SEARCH FILTER ==========

function initSearchFilter() {
    const search = document.getElementById('searchConversations');
    if (search) {
        search.addEventListener('input', function () {
            const query = this.value.toLowerCase();
            document.querySelectorAll('.conversation-item').forEach(item => {
                const name = item.dataset.name || '';
                item.style.display = name.includes(query) ? 'flex' : 'none';
            });
        });
    }
}

// ========== UTILITIES ==========

function scrollToBottom() {
    const container = document.getElementById('chatMessages');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

function formatTime(date) {
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();

    if (isToday) {
        return date.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
    }

    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    const isYesterday = date.toDateString() === yesterday.toDateString();

    if (isYesterday) {
        return 'Yesterday';
    }

    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Cleanup on page leave
window.addEventListener('beforeunload', function () {
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
});

// Global exports
window.sendMessage = sendMessage;
