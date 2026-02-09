/**
 * Teams JavaScript
 * Handles team-related AJAX operations
 */

// ========== TEAM CREATION ==========

function createTeam(teamName, itemType, itemId) {
    return fetch('/api/teams/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            team_name: teamName,
            item_type: itemType,
            item_id: itemId
        })
    })
        .then(res => res.json());
}

// ========== INVITATIONS ==========

function inviteToTeam(teamId, userId) {
    return fetch(`/api/teams/${teamId}/invite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
    })
        .then(res => res.json());
}

function acceptTeamInvitation(invitationId) {
    return fetch(`/api/teams/invitations/${invitationId}/accept`, {
        method: 'POST'
    })
        .then(res => res.json());
}

function rejectTeamInvitation(invitationId) {
    return fetch(`/api/teams/invitations/${invitationId}/reject`, {
        method: 'POST'
    })
        .then(res => res.json());
}

// ========== MEMBER MANAGEMENT ==========

function removeMemberFromTeam(teamId, userId) {
    return fetch(`/api/teams/${teamId}/members/${userId}`, {
        method: 'POST'
    })
        .then(res => res.json());
}

function leaveTeam(teamId) {
    return fetch(`/api/teams/${teamId}/leave`, {
        method: 'POST'
    })
        .then(res => res.json());
}

// ========== REGISTRATION ==========

function registerTeamForEvent(teamId) {
    return fetch(`/api/teams/${teamId}/register`, {
        method: 'POST'
    })
        .then(res => res.json());
}

// ========== UTILITIES ==========

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} alert-dismissible fade show`;
    toast.style.cssText = 'min-width: 250px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);';
    toast.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;

    container.appendChild(toast);
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

// Export functions
window.createTeam = createTeam;
window.inviteToTeam = inviteToTeam;
window.acceptTeamInvitation = acceptTeamInvitation;
window.rejectTeamInvitation = rejectTeamInvitation;
window.removeMemberFromTeam = removeMemberFromTeam;
window.leaveTeam = leaveTeam;
window.registerTeamForEvent = registerTeamForEvent;
