/**
 * SkillentHub — Client-side Form Validation (ES6+)
 * Covers: register, login, and reset-password forms.
 * No jQuery — pure vanilla JS.
 */

document.addEventListener('DOMContentLoaded', () => {
    // ── Password Toggle ──────────────────────────────────────
    document.querySelectorAll('.password-toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.id === 'toggle-confirm' ? 'confirm_password' : 'password';
            const input = document.getElementById(targetId);
            if (!input) return;

            const icon = btn.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.replace('bi-eye', 'bi-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.replace('bi-eye-slash', 'bi-eye');
            }
        });
    });

    // ── Validation Helpers ───────────────────────────────────
    const EMAIL_REGEX = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;

    const setValid = (input) => {
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
    };
    const setInvalid = (input, msg) => {
        input.classList.remove('is-valid');
        input.classList.add('is-invalid');
        const fb = input.parentElement.querySelector('.invalid-feedback');
        if (fb) fb.textContent = msg;
    };
    const clearState = (input) => {
        input.classList.remove('is-valid', 'is-invalid');
    };

    // ── Password Rule Checker ────────────────────────────────
    const checkPasswordRules = (password) => {
        const rules = {
            length: password.length >= 8,
            upper: /[A-Z]/.test(password),
            number: /[0-9]/.test(password),
        };

        const ruleLength = document.getElementById('rule-length');
        const ruleUpper = document.getElementById('rule-upper');
        const ruleNumber = document.getElementById('rule-number');

        if (ruleLength) {
            ruleLength.classList.toggle('valid', rules.length);
            ruleLength.classList.toggle('invalid', !rules.length && password.length > 0);
        }
        if (ruleUpper) {
            ruleUpper.classList.toggle('valid', rules.upper);
            ruleUpper.classList.toggle('invalid', !rules.upper && password.length > 0);
        }
        if (ruleNumber) {
            ruleNumber.classList.toggle('valid', rules.number);
            ruleNumber.classList.toggle('invalid', !rules.number && password.length > 0);
        }

        return rules.length && rules.upper && rules.number;
    };

    // ── Register Form ────────────────────────────────────────
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        const nameInput = document.getElementById('full_name');
        const emailInput = document.getElementById('email');
        const passwordInput = document.getElementById('password');

        // Real-time validation
        nameInput.addEventListener('input', () => {
            if (nameInput.value.trim().length > 0) setValid(nameInput);
            else clearState(nameInput);
        });

        emailInput.addEventListener('input', () => {
            const val = emailInput.value.trim();
            if (val.length === 0) { clearState(emailInput); return; }
            if (EMAIL_REGEX.test(val)) setValid(emailInput);
            else setInvalid(emailInput, 'Please enter a valid email address.');
        });

        passwordInput.addEventListener('input', () => {
            const val = passwordInput.value;
            const valid = checkPasswordRules(val);
            if (val.length === 0) clearState(passwordInput);
            else if (valid) setValid(passwordInput);
            else setInvalid(passwordInput, 'Password does not meet requirements.');
        });

        // Submit
        registerForm.addEventListener('submit', (e) => {
            let hasError = false;

            if (!nameInput.value.trim()) {
                setInvalid(nameInput, 'Full name is required.');
                hasError = true;
            }
            if (!EMAIL_REGEX.test(emailInput.value.trim())) {
                setInvalid(emailInput, 'Please enter a valid email address.');
                hasError = true;
            }
            if (!checkPasswordRules(passwordInput.value)) {
                setInvalid(passwordInput, 'Password does not meet requirements.');
                hasError = true;
            }

            if (hasError) {
                e.preventDefault();
                return;
            }

            // Show loading state
            const btn = document.getElementById('submit-btn');
            if (btn) {
                btn.disabled = true;
                btn.querySelector('.btn-text').classList.add('d-none');
                btn.querySelector('.btn-loader').classList.remove('d-none');
            }
        });
    }

    // ── Login Form ───────────────────────────────────────────
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        const emailInput = document.getElementById('email');
        const passwordInput = document.getElementById('password');

        emailInput.addEventListener('input', () => {
            const val = emailInput.value.trim();
            if (val.length === 0) { clearState(emailInput); return; }
            if (EMAIL_REGEX.test(val)) setValid(emailInput);
            else setInvalid(emailInput, 'Please enter a valid email address.');
        });

        loginForm.addEventListener('submit', (e) => {
            let hasError = false;

            if (!EMAIL_REGEX.test(emailInput.value.trim())) {
                setInvalid(emailInput, 'Please enter a valid email address.');
                hasError = true;
            }
            if (!passwordInput.value) {
                setInvalid(passwordInput, 'Password is required.');
                hasError = true;
            }

            if (hasError) {
                e.preventDefault();
                return;
            }

            const btn = document.getElementById('submit-btn');
            if (btn) {
                btn.disabled = true;
                btn.querySelector('.btn-text').classList.add('d-none');
                btn.querySelector('.btn-loader').classList.remove('d-none');
            }
        });
    }

    // ── Reset Password Form ──────────────────────────────────
    const resetForm = document.getElementById('reset-form');
    if (resetForm) {
        const passwordInput = document.getElementById('password');
        const confirmInput = document.getElementById('confirm_password');

        passwordInput.addEventListener('input', () => {
            const val = passwordInput.value;
            const valid = checkPasswordRules(val);
            if (val.length === 0) clearState(passwordInput);
            else if (valid) setValid(passwordInput);
            else setInvalid(passwordInput, 'Password does not meet requirements.');

            // Re-check confirm match
            if (confirmInput.value.length > 0) {
                if (confirmInput.value === val) setValid(confirmInput);
                else setInvalid(confirmInput, 'Passwords do not match.');
            }
        });

        confirmInput.addEventListener('input', () => {
            if (confirmInput.value.length === 0) { clearState(confirmInput); return; }
            if (confirmInput.value === passwordInput.value) setValid(confirmInput);
            else setInvalid(confirmInput, 'Passwords do not match.');
        });

        resetForm.addEventListener('submit', (e) => {
            let hasError = false;

            if (!checkPasswordRules(passwordInput.value)) {
                setInvalid(passwordInput, 'Password does not meet requirements.');
                hasError = true;
            }
            if (confirmInput.value !== passwordInput.value) {
                setInvalid(confirmInput, 'Passwords do not match.');
                hasError = true;
            }

            if (hasError) {
                e.preventDefault();
                return;
            }

            const btn = document.getElementById('submit-btn');
            if (btn) {
                btn.disabled = true;
                btn.querySelector('.btn-text').classList.add('d-none');
                btn.querySelector('.btn-loader').classList.remove('d-none');
            }
        });
    }
});
