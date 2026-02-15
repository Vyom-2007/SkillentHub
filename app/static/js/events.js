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
        const teamNameInput = document.getElementById('teamNameInput');

        // Collect members
        const members = [];
        let missingDetails = false;

        if (teamNameInput) {
            if (!teamNameInput.value.trim()) {
                alert('Team Name is required.');
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-person-plus me-2"></i>Register Now';
                return;
            }

            let rowIndex = 0;
            document.querySelectorAll('.member-row').forEach(row => {
                rowIndex++;
                const nameInput = row.querySelector('.member-name');
                const emailInput = row.querySelector('.member-email');

                // Get values
                const nameVal = nameInput ? nameInput.value.trim() : '';
                const emailVal = emailInput ? emailInput.value.trim() : '';

                // Skip empty rows
                if (!nameVal && !emailVal) {
                    return;
                }

                // Enforce both fields
                if (nameVal && !emailVal) {
                    alert(`Please enter an Email for member #${rowIndex} (${nameVal}).`);
                    missingDetails = true;
                    return;
                }
                if (!nameVal && emailVal) {
                    alert(`Please enter a Name for member #${rowIndex} (${emailVal}).`);
                    missingDetails = true;
                    return;
                }

                members.push({
                    name: nameVal,
                    email: emailVal
                });
            });

            if (missingDetails) {
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-check me-1"></i>Confirm';
                return;
            }

            if (members.length === 0) {
                alert('At least one team member is required for team registration.');
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-person-plus me-2"></i>Register Now';
                return;
            }

            body = {
                team_name: teamNameInput.value,
                members: members
            };
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
