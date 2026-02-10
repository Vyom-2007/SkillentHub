/**
 * SkillentHub — OTP Input Handler (ES6+)
 * Features:
 *   - Auto-focus between 6 digit inputs
 *   - Paste handling (6-digit code)
 *   - 5-minute countdown timer
 *   - Resend button with 60-second cooldown
 *   - Verify API call via Fetch
 */

document.addEventListener('DOMContentLoaded', () => {
    const inputs = document.querySelectorAll('.otp-input');
    const verifyBtn = document.getElementById('verify-btn');
    const resendBtn = document.getElementById('resend-btn');
    const statusEl = document.getElementById('otp-status');
    const countdownEl = document.getElementById('countdown');
    const emailField = document.getElementById('otp-email');
    const email = emailField ? emailField.value : '';

    // ── Auto-focus & Navigation ──────────────────────────────
    inputs.forEach((input, index) => {
        // Only allow digits
        input.addEventListener('input', (e) => {
            const val = e.target.value.replace(/\D/g, '');
            e.target.value = val.slice(0, 1);

            if (val && index < inputs.length - 1) {
                inputs[index + 1].focus();
            }

            // Toggle filled class
            e.target.classList.toggle('filled', val.length === 1);
            e.target.classList.remove('error');
        });

        // Backspace → move to previous
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && !input.value && index > 0) {
                inputs[index - 1].focus();
                inputs[index - 1].value = '';
                inputs[index - 1].classList.remove('filled');
            }
            // Arrow keys
            if (e.key === 'ArrowLeft' && index > 0) inputs[index - 1].focus();
            if (e.key === 'ArrowRight' && index < inputs.length - 1) inputs[index + 1].focus();
        });

        // Select all text on focus for easy overwrite
        input.addEventListener('focus', () => input.select());
    });

    // ── Paste Handling ───────────────────────────────────────
    inputs[0].addEventListener('paste', (e) => {
        e.preventDefault();
        const pasted = (e.clipboardData.getData('text') || '').replace(/\D/g, '').slice(0, 6);
        pasted.split('').forEach((char, i) => {
            if (inputs[i]) {
                inputs[i].value = char;
                inputs[i].classList.add('filled');
                inputs[i].classList.remove('error');
            }
        });
        if (pasted.length > 0) {
            const focusIndex = Math.min(pasted.length, inputs.length - 1);
            inputs[focusIndex].focus();
        }
    });

    // ── Get OTP Value ────────────────────────────────────────
    const getOTP = () => {
        return Array.from(inputs).map(i => i.value).join('');
    };

    // ── 5-Minute Countdown Timer ─────────────────────────────
    let totalSeconds = 5 * 60;
    let timerInterval = null;

    const startTimer = () => {
        totalSeconds = 5 * 60;
        updateTimerDisplay();

        if (timerInterval) clearInterval(timerInterval);
        timerInterval = setInterval(() => {
            totalSeconds--;
            updateTimerDisplay();
            if (totalSeconds <= 0) {
                clearInterval(timerInterval);
                setStatus('OTP has expired. Please request a new one.', 'error');
                if (verifyBtn) verifyBtn.disabled = true;
            }
        }, 1000);
    };

    const updateTimerDisplay = () => {
        const mins = Math.floor(totalSeconds / 60);
        const secs = totalSeconds % 60;
        if (countdownEl) {
            countdownEl.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
        }
    };

    // ── Resend Button (disabled for first 60s) ───────────────
    let resendCooldown = 60;
    let resendInterval = null;

    const startResendCooldown = () => {
        resendCooldown = 60;
        if (resendBtn) resendBtn.disabled = true;
        if (resendBtn) resendBtn.innerHTML = `<i class="bi bi-arrow-repeat me-1"></i>Resend in ${resendCooldown}s`;

        if (resendInterval) clearInterval(resendInterval);
        resendInterval = setInterval(() => {
            resendCooldown--;
            if (resendBtn) resendBtn.innerHTML = `<i class="bi bi-arrow-repeat me-1"></i>Resend in ${resendCooldown}s`;
            if (resendCooldown <= 0) {
                clearInterval(resendInterval);
                if (resendBtn) {
                    resendBtn.disabled = false;
                    resendBtn.innerHTML = `<i class="bi bi-arrow-repeat me-1"></i>Resend Code`;
                }
            }
        }, 1000);
    };

    // ── Status Message ───────────────────────────────────────
    const setStatus = (msg, type) => {
        if (!statusEl) return;
        statusEl.textContent = msg;
        statusEl.className = 'otp-status ' + (type || '');
    };

    // ── Verify OTP ───────────────────────────────────────────
    const verifyOTP = async () => {
        const otp = getOTP();
        if (otp.length !== 6) {
            setStatus('Please enter all 6 digits.', 'error');
            inputs.forEach(i => { if (!i.value) i.classList.add('error'); });
            return;
        }

        // Loading state
        verifyBtn.disabled = true;
        verifyBtn.querySelector('.btn-text').classList.add('d-none');
        verifyBtn.querySelector('.btn-loader').classList.remove('d-none');
        setStatus('', '');

        try {
            const response = await fetch('/api/auth/forgot-password/verify-otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, otp }),
            });

            const data = await response.json();

            if (data.success) {
                setStatus('✓ ' + data.message, 'success');
                inputs.forEach(i => { i.disabled = true; i.classList.add('filled'); });
                if (timerInterval) clearInterval(timerInterval);

                // Redirect to reset password page after brief delay
                setTimeout(() => {
                    window.location.href = `/api/auth/reset-password?email=${encodeURIComponent(email)}`;
                }, 1200);
            } else {
                setStatus(data.message, 'error');
                inputs.forEach(i => i.classList.add('error'));
                // Remove error class after animation
                setTimeout(() => inputs.forEach(i => i.classList.remove('error')), 500);
                verifyBtn.disabled = false;
            }
        } catch (err) {
            setStatus('Network error. Please try again.', 'error');
            verifyBtn.disabled = false;
        }

        verifyBtn.querySelector('.btn-text').classList.remove('d-none');
        verifyBtn.querySelector('.btn-loader').classList.add('d-none');
    };

    // ── Resend OTP ───────────────────────────────────────────
    const resendOTP = async () => {
        resendBtn.disabled = true;
        setStatus('Sending new code...', '');

        try {
            const formData = new FormData();
            formData.append('email', email);

            const response = await fetch('/api/auth/forgot-password/send-otp', {
                method: 'POST',
                body: formData,
            });

            // Regardless of redirect, show resent message
            setStatus('A new code has been sent to your email.', 'success');
            inputs.forEach(i => { i.value = ''; i.classList.remove('filled', 'error'); i.disabled = false; });
            inputs[0].focus();

            // Reset timers
            startTimer();
            startResendCooldown();
            verifyBtn.disabled = false;
        } catch (err) {
            setStatus('Failed to resend code. Please try again.', 'error');
            resendBtn.disabled = false;
        }
    };

    // ── Event Listeners ──────────────────────────────────────
    if (verifyBtn) verifyBtn.addEventListener('click', verifyOTP);
    if (resendBtn) resendBtn.addEventListener('click', resendOTP);

    // Allow Enter key to verify
    inputs.forEach(input => {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') verifyOTP();
        });
    });

    // ── Initialize ───────────────────────────────────────────
    startTimer();
    startResendCooldown();
    if (inputs[0]) inputs[0].focus();
});
