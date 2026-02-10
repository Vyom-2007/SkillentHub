document.addEventListener('DOMContentLoaded', function () {
    const registerForm = document.getElementById('registerForm');

    if (registerForm) {
        const passwordInput = document.getElementById('password');
        const confirmInput = document.getElementById('confirm_password');
        const emailInput = document.getElementById('email');
        const submitBtn = document.getElementById('submitBtn');

        function validatePassword(password) {
            const hasMinLen = password.length >= 8;
            const hasUpper = /[A-Z]/.test(password);
            const hasNumber = /\d/.test(password);
            return hasMinLen && hasUpper && hasNumber;
        }

        function validateEmail(email) {
            return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
        }

        function validateForm() {
            let isValid = true;

            // Email
            if (!validateEmail(emailInput.value)) {
                emailInput.classList.add('is-invalid');
                isValid = false;
            } else {
                emailInput.classList.remove('is-invalid');
                emailInput.classList.add('is-valid');
            }

            // Password
            if (!validatePassword(passwordInput.value)) {
                passwordInput.classList.add('is-invalid');
                document.getElementById('passwordFeedback').textContent = 'Min 8 chars, 1 uppercase, 1 number.';
                isValid = false;
            } else {
                passwordInput.classList.remove('is-invalid');
                passwordInput.classList.add('is-valid');
            }

            // Confirm
            if (confirmInput.value !== passwordInput.value || confirmInput.value === '') {
                confirmInput.classList.add('is-invalid');
                isValid = false;
            } else {
                confirmInput.classList.remove('is-invalid');
                confirmInput.classList.add('is-valid');
            }

            submitBtn.disabled = !isValid;
            return isValid;
        }

        [emailInput, passwordInput, confirmInput].forEach(input => {
            input.addEventListener('input', validateForm);
        });

        // Initial state
        // submitBtn.disabled = true;
    }
});
