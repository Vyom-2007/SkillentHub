/**
 * SkillentHub Authentication JavaScript
 * Handles form validation, OTP input management, and countdown timers
 */

/**
 * Validate email format using regex
 * @param {HTMLInputElement} input - Email input element
 * @returns {boolean} True if valid
 */
function validateEmail(input) {
    const email = input.value.trim();
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

    if (!email || !emailRegex.test(email)) {
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
        return false;
    }

    input.classList.remove('is-invalid');
    input.classList.add('is-valid');
    return true;
}

/**
 * Validate password complexity
 * Requirements: Min 8 chars, at least 1 uppercase, at least 1 number
 * @param {HTMLInputElement} input - Password input element
 * @returns {boolean} True if valid
 */
function validatePassword(input) {
    const password = input.value;
    const minLength = password.length >= 8;
    const hasUppercase = /[A-Z]/.test(password);
    const hasNumber = /[0-9]/.test(password);

    if (!minLength || !hasUppercase || !hasNumber) {
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
        return false;
    }

    input.classList.remove('is-invalid');
    input.classList.add('is-valid');
    return true;
}

/**
 * Validate name (Full Name or Company Name)
 * @param {HTMLInputElement} input - Name input element
 * @param {number} minLength - Minimum length (default 2)
 * @returns {boolean} True if valid
 */
function validateName(input, minLength = 2) {
    const value = input.value.trim();
    if (value.length < minLength) {
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
        return false;
    }
    input.classList.remove('is-invalid');
    input.classList.add('is-valid');
    return true;
}

/**
 * Validate confirm password
 * @param {HTMLInputElement} passwordInput - Original password input
 * @param {HTMLInputElement} confirmInput - Confirm password input
 * @returns {boolean} True if matching
 */
function validateConfirmPassword(passwordInput, confirmInput) {
    const password = passwordInput.value;
    const confirm = confirmInput.value;

    if (confirm && password !== confirm) {
        confirmInput.classList.add('is-invalid');
        confirmInput.classList.remove('is-valid');
        return false;
    }
    confirmInput.classList.remove('is-invalid');
    if (confirm) confirmInput.classList.add('is-valid'); // Only mark valid if not empty
    return true;
}

/**
 * Initialize OTP input boxes with auto-focus, backspace, and paste handling
 * @param {NodeList} inputs - NodeList of OTP input elements
 */
function initOTPInputs(inputs) {
    inputs.forEach((input, index) => {
        // Handle input - auto focus next
        input.addEventListener('input', function (e) {
            const value = this.value;

            // Only allow digits
            this.value = value.replace(/[^0-9]/g, '');

            if (this.value.length === 1) {
                this.classList.add('filled');
                this.classList.remove('is-invalid');

                // Move to next input
                if (index < inputs.length - 1) {
                    inputs[index + 1].focus();
                }
            }
        });

        // Handle keydown for backspace and navigation
        input.addEventListener('keydown', function (e) {
            // Backspace - move to previous input
            if (e.key === 'Backspace') {
                if (this.value === '' && index > 0) {
                    inputs[index - 1].focus();
                    inputs[index - 1].value = '';
                    inputs[index - 1].classList.remove('filled');
                } else {
                    this.classList.remove('filled');
                }
            }

            // Arrow keys navigation
            if (e.key === 'ArrowLeft' && index > 0) {
                e.preventDefault();
                inputs[index - 1].focus();
            }
            if (e.key === 'ArrowRight' && index < inputs.length - 1) {
                e.preventDefault();
                inputs[index + 1].focus();
            }
        });

        // Handle paste - fill all boxes
        input.addEventListener('paste', function (e) {
            e.preventDefault();
            const pastedData = (e.clipboardData || window.clipboardData).getData('text');
            const digits = pastedData.replace(/[^0-9]/g, '').slice(0, 6);

            if (digits.length > 0) {
                // Fill all inputs with pasted digits
                digits.split('').forEach((digit, i) => {
                    if (inputs[i]) {
                        inputs[i].value = digit;
                        inputs[i].classList.add('filled');
                        inputs[i].classList.remove('is-invalid');
                    }
                });

                // Focus on the next empty input or last input
                const nextEmptyIndex = digits.length < inputs.length ? digits.length : inputs.length - 1;
                inputs[nextEmptyIndex].focus();
            }
        });

        // Select all on focus
        input.addEventListener('focus', function () {
            this.select();
        });
    });
}

/**
 * Collect OTP value from all input boxes
 * @param {NodeList} inputs - NodeList of OTP input elements
 * @returns {string} Combined OTP string
 */
function collectOTP(inputs) {
    let otp = '';
    inputs.forEach(input => {
        otp += input.value;
    });
    return otp;
}

/**
 * Start the OTP expiry countdown timer
 * @param {number} seconds - Initial seconds remaining
 */
function startOTPTimer(seconds) {
    const timerText = document.getElementById('timerText');
    const timerBadge = document.getElementById('timerBadge');
    const verifyBtn = document.getElementById('verifyBtn');

    if (!timerText || !timerBadge) return;

    let remaining = seconds;

    function updateTimer() {
        const minutes = Math.floor(remaining / 60);
        const secs = remaining % 60;
        timerText.textContent = `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

        // Add warning class when less than 60 seconds
        if (remaining <= 60 && remaining > 0) {
            timerBadge.classList.add('warning');
            timerBadge.classList.remove('expired');
        }

        // Expired
        if (remaining <= 0) {
            timerBadge.classList.add('expired');
            timerBadge.classList.remove('warning');
            timerText.textContent = 'Expired';

            if (verifyBtn) {
                verifyBtn.disabled = true;
                verifyBtn.innerHTML = '<i class="bi bi-x-circle me-2"></i>OTP Expired';
            }

            return;
        }

        remaining--;
        setTimeout(updateTimer, 1000);
    }

    updateTimer();
}

/**
 * Start the resend OTP cooldown timer
 * @param {number} seconds - Cooldown duration in seconds
 */
function startResendCooldown(seconds) {
    const resendBtn = document.getElementById('resendBtn');
    const resendCooldown = document.getElementById('resendCooldown');

    if (!resendBtn || !resendCooldown) return;

    let remaining = seconds;

    function updateCooldown() {
        if (remaining <= 0) {
            // Enable resend button
            resendBtn.disabled = false;
            resendBtn.classList.remove('disabled');
            resendCooldown.textContent = '';
            return;
        }

        resendCooldown.textContent = `(${remaining}s)`;
        remaining--;
        setTimeout(updateCooldown, 1000);
    }

    updateCooldown();
}

/**
 * Format time in mm:ss format
 * @param {number} seconds - Total seconds
 * @returns {string} Formatted time string
 */
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

/**
 * Show validation error on an input
 * @param {HTMLInputElement} input - Input element
 * @param {string} message - Error message
 */
function showError(input, message) {
    input.classList.add('is-invalid');
    const feedback = input.nextElementSibling;
    if (feedback && feedback.classList.contains('invalid-feedback')) {
        feedback.textContent = message;
    }
}

/**
 * Clear validation error from an input
 * @param {HTMLInputElement} input - Input element
 */
function clearError(input) {
    input.classList.remove('is-invalid');
    input.classList.remove('is-valid');
}

// Export functions for use in templates
if (typeof window !== 'undefined') {
    window.validateEmail = validateEmail;
    window.validatePassword = validatePassword;
    window.validateName = validateName;
    window.validateConfirmPassword = validateConfirmPassword;
    window.initOTPInputs = initOTPInputs;
    window.collectOTP = collectOTP;
    window.startOTPTimer = startOTPTimer;
    window.startResendCooldown = startResendCooldown;
    window.formatTime = formatTime;
    window.showError = showError;
    window.clearError = clearError;
}
