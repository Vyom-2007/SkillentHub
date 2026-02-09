/**
 * Settings JavaScript
 * Handles password validation, strength check, and toggle UI
 */

// ========== PASSWORD TOGGLE ==========

function togglePassword(inputId, iconEl) {
    const input = document.getElementById(inputId);
    if (input.type === 'password') {
        input.type = 'text';
        iconEl.classList.remove('bi-eye');
        iconEl.classList.add('bi-eye-slash');
    } else {
        input.type = 'password';
        iconEl.classList.remove('bi-eye-slash');
        iconEl.classList.add('bi-eye');
    }
}

// ========== PASSWORD STRENGTH ==========

function checkPasswordStrength() {
    const password = document.getElementById('newPassword').value;
    const strengthBar = document.getElementById('passwordStrength');

    let strength = 0;

    // Length check
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;

    // Uppercase check
    if (/[A-Z]/.test(password)) strength++;

    // Number check
    if (/[0-9]/.test(password)) strength++;

    // Special character check
    if (/[^A-Za-z0-9]/.test(password)) strength++;

    // Update UI
    strengthBar.className = 'password-strength';
    if (password.length === 0) {
        strengthBar.style.width = '0';
    } else if (strength <= 2) {
        strengthBar.classList.add('strength-weak');
    } else if (strength <= 4) {
        strengthBar.classList.add('strength-medium');
    } else {
        strengthBar.classList.add('strength-strong');
    }

    // Also check match
    checkPasswordMatch();
}

function checkPasswordMatch() {
    const newPass = document.getElementById('newPassword').value;
    const confirmPass = document.getElementById('confirmPassword').value;
    const matchMsg = document.getElementById('passwordMatchMsg');
    const submitBtn = document.getElementById('changePasswordBtn');

    if (confirmPass.length === 0) {
        matchMsg.textContent = '';
        return;
    }

    if (newPass === confirmPass) {
        matchMsg.textContent = '✓ Passwords match';
        matchMsg.className = 'small mt-1 text-success';
        submitBtn.disabled = false;
    } else {
        matchMsg.textContent = '✗ Passwords do not match';
        matchMsg.className = 'small mt-1 text-danger';
        submitBtn.disabled = true;
    }
}

// ========== FORM VALIDATION ==========

function validatePasswordForm(e) {
    const newPass = document.getElementById('newPassword').value;
    const confirmPass = document.getElementById('confirmPassword').value;

    // Check match
    if (newPass !== confirmPass) {
        e.preventDefault();
        alert('Passwords do not match');
        return false;
    }

    // Check complexity
    if (newPass.length < 8) {
        e.preventDefault();
        alert('Password must be at least 8 characters');
        return false;
    }

    if (!/[A-Z]/.test(newPass)) {
        e.preventDefault();
        alert('Password must contain at least one uppercase letter');
        return false;
    }

    if (!/[0-9]/.test(newPass)) {
        e.preventDefault();
        alert('Password must contain at least one number');
        return false;
    }

    return true;
}

// ========== INITIALIZATION ==========

document.addEventListener('DOMContentLoaded', function () {
    // Password form validation
    const passwordForm = document.getElementById('passwordForm');
    if (passwordForm) {
        passwordForm.addEventListener('submit', validatePasswordForm);
    }
});

// Export for inline handlers
window.togglePassword = togglePassword;
window.checkPasswordStrength = checkPasswordStrength;
window.checkPasswordMatch = checkPasswordMatch;
