/**
 * Connections JavaScript
 * Handles connection request actions via AJAX
 */

// ========== SEND REQUEST ==========

function sendRequest(userId) {
    const btn = event.target.closest('button');
    const originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

    fetch('/api/connections/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                btn.className = 'btn btn-sm btn-pending';
                btn.disabled = true;
                btn.innerHTML = '<i class="bi bi-clock me-1"></i>Request Sent';
                showToast('Connection request sent!', 'success');
            } else {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
                showToast(data.error || 'Failed to send request', 'error');
            }
        })
        .catch(err => {
            console.error('Error:', err);
            btn.disabled = false;
            btn.innerHTML = originalHtml;
            showToast('Network error', 'error');
        });
}

// ========== ACCEPT REQUEST ==========

function acceptRequest(connectionId) {
    const btn = event.target.closest('button');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

    fetch(`/api/connections/accept/${connectionId}`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Update UI - either in request list or user card
                const requestCard = document.getElementById(`request-${connectionId}`);
                if (requestCard) {
                    requestCard.innerHTML = `
                    <div class="text-center w-100 text-success">
                        <i class="bi bi-check-circle me-2"></i>Connected!
                    </div>
                `;
                    setTimeout(() => requestCard.remove(), 2000);
                }

                // Update button in user card grid
                const userCard = btn.closest('.user-card');
                if (userCard) {
                    const container = userCard.querySelector('.connection-btn-container');
                    if (container) {
                        const userId = container.dataset.userId;
                        container.innerHTML = `
                        <a href="/messages?user=${userId}" class="btn btn-sm btn-outline-primary">
                            <i class="bi bi-chat me-1"></i>Message
                        </a>
                    `;
                    }
                }

                updateRequestCount(-1);
                showToast('Connection accepted!', 'success');
            } else {
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-check me-1"></i>Accept';
                showToast(data.error || 'Failed to accept', 'error');
            }
        })
        .catch(err => {
            console.error('Error:', err);
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-check me-1"></i>Accept';
            showToast('Network error', 'error');
        });
}

// ========== REJECT REQUEST ==========

function rejectRequest(connectionId) {
    const btn = event.target.closest('button');
    btn.disabled = true;

    fetch(`/api/connections/reject/${connectionId}`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const requestCard = document.getElementById(`request-${connectionId}`);
                if (requestCard) {
                    requestCard.innerHTML = `
                    <div class="text-center w-100 text-muted">
                        <i class="bi bi-x-circle me-2"></i>Request declined
                    </div>
                `;
                    setTimeout(() => requestCard.remove(), 2000);
                }

                // Update button in user card grid
                const userCard = btn.closest('.user-card');
                if (userCard) {
                    const container = userCard.querySelector('.connection-btn-container');
                    if (container) {
                        const userId = container.dataset.userId;
                        container.innerHTML = `
                        <button class="btn btn-sm btn-connect" onclick="sendRequest(${userId})">
                            <i class="bi bi-person-plus me-1"></i>Connect
                        </button>
                    `;
                    }
                }

                updateRequestCount(-1);
                showToast('Request declined', 'info');
            } else {
                btn.disabled = false;
                showToast(data.error || 'Failed to reject', 'error');
            }
        })
        .catch(err => {
            console.error('Error:', err);
            btn.disabled = false;
            showToast('Network error', 'error');
        });
}

// ========== HELPERS ==========

function updateRequestCount(delta) {
    const badge = document.querySelector('#networkTabs .nav-link[href="#requests"] .badge');
    if (badge) {
        const current = parseInt(badge.textContent) || 0;
        const newCount = Math.max(0, current + delta);
        if (newCount === 0) {
            badge.remove();
        } else {
            badge.textContent = newCount;
        }
    }
}

function showToast(message, type = 'info') {
    // Simple toast implementation
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} alert-dismissible fade show`;
    toast.style.cssText = 'min-width: 250px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999;';
    document.body.appendChild(container);
    return container;
}

// Export global functions
window.sendRequest = sendRequest;
window.acceptRequest = acceptRequest;
window.rejectRequest = rejectRequest;
