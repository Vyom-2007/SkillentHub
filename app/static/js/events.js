/**
 * Events JavaScript
 * Handles countdowns, registration confirmation, and event interactions
 */

// ========== INITIALIZATION ==========

document.addEventListener('DOMContentLoaded', function () {
    initCountdowns();
    // Update countdowns every second
    setInterval(updateCountdowns, 1000);
});

// ========== COUNTDOWN TIMERS ==========

function initCountdowns() {
    updateCountdowns();
}

function updateCountdowns() {
    document.querySelectorAll('[data-countdown]').forEach(el => {
        const targetDate = new Date(el.dataset.countdown);
        const now = new Date();
        const diff = targetDate - now;

        if (diff <= 0) {
            el.innerHTML = '<span class="text-success">🟢 Started!</span>';
            return;
        }

        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);

        let countdownText = '';
        if (days > 0) {
            countdownText = `${days}d ${hours}h ${minutes}m`;
        } else if (hours > 0) {
            countdownText = `${hours}h ${minutes}m ${seconds}s`;
        } else {
            countdownText = `${minutes}m ${seconds}s`;
        }

        el.innerHTML = `<i class="bi bi-clock me-1"></i>${countdownText}`;
    });
}

// ========== REGISTRATION ==========

function registerEvent(eventType, eventId) {
    const btn = document.getElementById('confirmRegisterBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Registering...';

    let url = '';
    let body = {};

    if (eventType === 'competition') {
        url = `/competitions/${eventId}/register`;
    } else {
        url = `/hackathons/${eventId}/register`;
        const teamName = document.getElementById('teamNameInput')?.value;
        if (teamName) {
            body = { team_name: teamName };
        }
    }

    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: Object.keys(body).length > 0 ? JSON.stringify(body) : undefined
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('registerModal'));
                if (modal) modal.hide();

                // Show success and reload
                alert('🎉 Registration successful!');
                window.location.reload();
            } else {
                alert(data.error || 'Registration failed. Please try again.');
            }
        })
        .catch(err => {
            console.error('Registration error:', err);
            alert('Registration failed. Please try again.');
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-check me-1"></i>Confirm';
        });
}

// Global exports
window.registerEvent = registerEvent;
