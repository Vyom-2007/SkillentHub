/**
 * Recruiter Forms Validation and Logic
 */

document.addEventListener('DOMContentLoaded', function () {
    'use strict'

    // 1. Bootstrap Validation
    const forms = document.querySelectorAll('.needs-validation')
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault()
                event.stopPropagation()
            }
            form.classList.add('was-validated')
        }, false)
    })

    // 2. Character Counter
    const descInput = document.getElementById('descInput');
    const descCount = document.getElementById('descCount');

    if (descInput && descCount) {
        descInput.addEventListener('input', function () {
            const currentLength = this.value.length;
            descCount.textContent = currentLength;

            if (currentLength >= 5000) {
                descCount.classList.add('text-danger');
            } else {
                descCount.classList.remove('text-danger');
            }
        });
    }

    // 3. Date Validation (Deadline > Today)
    const deadlineInput = document.getElementById('deadlineInput');
    if (deadlineInput) {
        // Set min date to today
        const today = new Date().toISOString().split('T')[0];
        deadlineInput.setAttribute('min', today);

        deadlineInput.addEventListener('change', function () {
            const selectedDate = new Date(this.value);
            const now = new Date();
            now.setHours(0, 0, 0, 0); // Compare dates only

            if (selectedDate < now) {
                this.setCustomValidity('Deadline cannot be in the past.');
            } else {
                this.setCustomValidity('');
            }
        });
    }

    // 4. Start Date < End Date
    const startDateInput = document.getElementById('startDateInput');
    const endDateInput = document.getElementById('endDateInput');

    if (startDateInput && endDateInput) {
        // Validation logic
        function validateDates() {
            if (startDateInput.value && endDateInput.value) {
                const start = new Date(startDateInput.value);
                const end = new Date(endDateInput.value);

                if (end <= start) {
                    endDateInput.setCustomValidity('End date must be after start date.');
                } else {
                    endDateInput.setCustomValidity('');
                }
            }
        }

        startDateInput.addEventListener('change', validateDates);
        endDateInput.addEventListener('change', validateDates);
    }
});
