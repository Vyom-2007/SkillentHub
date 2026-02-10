document.addEventListener('DOMContentLoaded', function () {
    console.log('SkillentHub Loaded');

    // Poll for notifications
    pollNotifications();
    setInterval(pollNotifications, 60000); // Poll every minute
});

function pollNotifications() {
    fetch('/notifications/api/unread-count')
        .then(response => {
            if (response.ok) return response.json();
            throw new Error('Network response was not ok');
        })
        .then(data => {
            const badge = document.getElementById('nav-notif-badge');
            if (badge) {
                if (data.count > 0) {
                    badge.textContent = data.count > 99 ? '99+' : data.count;
                    badge.style.display = 'block';
                } else {
                    badge.style.display = 'none';
                }
            }
        })
        .catch(error => console.error('Error polling notifications:', error));
}
