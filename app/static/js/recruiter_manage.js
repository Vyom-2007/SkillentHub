/**
 * Recruiter Management JS
 * Handles Status Toggling and other dynamic interactions.
 */

document.addEventListener('DOMContentLoaded', function () {

    // Toggle Opportunity Status (Active/Inactive)
    const toggles = document.querySelectorAll('.toggle-status');

    toggles.forEach(toggle => {
        toggle.addEventListener('change', function () {
            const itemId = this.dataset.id;
            const itemType = this.dataset.type;
            const isChecked = this.checked;

            // Optimistic UI update (already happened by default)

            // Send API Request
            fetch(`/recruiter/opportunities/${itemType}/${itemId}/toggle`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('Status updated');
                        // Optional: Show toast
                    } else {
                        console.error('Update failed');
                        alert('Failed to update status: ' + data.message);
                        this.checked = !isChecked; // Revert
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred');
                    this.checked = !isChecked; // Revert
                });
        });
    });

    // Confirmation for Status Update to 'Shortlisted' or 'Accepted'
    const statusForm = document.querySelector('form[action*="update_application_status"]');
    if (statusForm) {
        const select = statusForm.querySelector('select[name="status"]');
        statusForm.addEventListener('submit', function (e) {
            const val = select.value;
            if (val === 'shortlisted' || val === 'accepted') {
                if (!confirm(`Switching status to "${val}" will send an email notification to the candidate. Continue?`)) {
                    e.preventDefault();
                }
            }
        });
    }

});
