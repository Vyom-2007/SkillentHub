/**
 * SkillentHub — Profile JS (ES6+)
 * Features:
 *   - Profile picture upload + preview
 *   - Skill tag input (add / remove)
 *   - Dynamic education rows (add / remove)
 *   - Phone validation
 *   - Connect button AJAX
 */

document.addEventListener('DOMContentLoaded', () => {
    // ── Profile Picture Upload & Preview ─────────────────────
    const picInput = document.getElementById('profile_picture');
    const picBtn = document.getElementById('upload-pic-btn');
    const avatarPreview = document.getElementById('avatar-preview');

    if (picBtn && picInput) {
        picBtn.addEventListener('click', () => picInput.click());
        if (avatarPreview) {
            avatarPreview.addEventListener('click', () => picInput.click());
        }

        picInput.addEventListener('change', () => {
            const file = picInput.files[0];
            if (!file) return;

            // Validate type
            if (!['image/jpeg', 'image/png'].includes(file.type)) {
                alert('Only JPG and PNG images are allowed.');
                picInput.value = '';
                return;
            }
            // Validate size
            if (file.size > 5 * 1024 * 1024) {
                alert('Image must be under 5 MB.');
                picInput.value = '';
                return;
            }

            // Preview
            const reader = new FileReader();
            reader.onload = (e) => {
                avatarPreview.style.backgroundImage = `url(${e.target.result})`;
                avatarPreview.style.backgroundSize = 'cover';
                avatarPreview.innerHTML = ''; // Remove placeholder icon/text
            };
            reader.readAsDataURL(file);
        });
    }

    // ── Skill Tag Management ─────────────────────────────────
    const skillInput = document.getElementById('skill-input');
    const proficiencySelect = document.getElementById('skill-proficiency');
    const addSkillBtn = document.getElementById('add-skill-btn');
    const skillTagsContainer = document.getElementById('skill-tags');
    const skillsJsonInput = document.getElementById('skills-json');

    let skills = [];

    // Load existing skills (from edit page)
    if (skillsJsonInput && skillsJsonInput.value) {
        try {
            const existing = JSON.parse(skillsJsonInput.value);
            if (Array.isArray(existing)) {
                existing.forEach(s => {
                    // Handle both formats: {name, proficiency} and {skill_name, proficiency_level}
                    const name = s.name || s.skill_name || '';
                    const prof = s.proficiency || s.proficiency_level || 'beginner';
                    if (name) {
                        skills.push({ name, proficiency: prof });
                    }
                });
            }
        } catch (e) { /* ignore parse errors */ }
    }

    const renderSkillTags = () => {
        if (!skillTagsContainer) return;
        skillTagsContainer.innerHTML = '';
        skills.forEach((skill, index) => {
            const tag = document.createElement('span');
            tag.className = `skill-tag ${skill.proficiency}`;
            tag.innerHTML = `
                ${skill.name}
                <span class="remove-skill" data-index="${index}" title="Remove">
                    <i class="bi bi-x-lg"></i>
                </span>
            `;
            skillTagsContainer.appendChild(tag);
        });

        // Update hidden JSON
        if (skillsJsonInput) {
            skillsJsonInput.value = JSON.stringify(skills);
        }
    };

    const addSkill = () => {
        if (!skillInput) return;
        const name = skillInput.value.trim();
        if (!name) return;

        // Check duplicate (case-insensitive)
        if (skills.some(s => s.name.toLowerCase() === name.toLowerCase())) {
            skillInput.value = '';
            return;
        }

        const proficiency = proficiencySelect ? proficiencySelect.value : 'intermediate';
        skills.push({ name, proficiency });
        renderSkillTags();
        skillInput.value = '';
        skillInput.focus();
    };

    if (addSkillBtn) addSkillBtn.addEventListener('click', addSkill);
    if (skillInput) {
        skillInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                addSkill();
            }
        });
    }

    // Remove skill (delegated)
    if (skillTagsContainer) {
        skillTagsContainer.addEventListener('click', (e) => {
            const removeBtn = e.target.closest('.remove-skill');
            if (removeBtn) {
                const index = parseInt(removeBtn.dataset.index, 10);
                skills.splice(index, 1);
                renderSkillTags();
            }
        });
    }

    // Render initial skill tags
    renderSkillTags();

    // ── Dynamic Education Rows ───────────────────────────────
    const eduContainer = document.getElementById('education-container');
    const addEduBtn = document.getElementById('add-education-btn');

    if (addEduBtn && eduContainer) {
        addEduBtn.addEventListener('click', () => {
            const index = eduContainer.children.length;
            const row = document.createElement('div');
            row.className = 'education-row';
            row.dataset.index = index;
            row.innerHTML = `
                <div class="row g-3">
                    <div class="col-md-6">
                        <div class="form-floating">
                            <input type="text" class="form-control" name="institution[]" placeholder="Institution">
                            <label>Institution</label>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="form-floating">
                            <input type="text" class="form-control" name="degree[]" placeholder="Degree">
                            <label>Degree</label>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="form-floating">
                            <input type="text" class="form-control" name="field_of_study[]" placeholder="Field">
                            <label>Field of Study</label>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="form-floating">
                            <input type="date" class="form-control" name="start_date[]" placeholder=" ">
                            <label>Start Date</label>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="form-floating">
                            <input type="date" class="form-control" name="end_date[]" placeholder=" ">
                            <label>End Date</label>
                        </div>
                    </div>
                    <div class="col-12">
                        <div class="form-floating">
                            <textarea class="form-control" name="edu_description[]"
                                      placeholder="Description" style="height:70px"></textarea>
                            <label>Description (optional)</label>
                        </div>
                    </div>
                </div>
                <button type="button" class="btn btn-sm btn-outline-danger remove-edu-btn mt-2">
                    <i class="bi bi-trash me-1"></i>Remove
                </button>
            `;
            eduContainer.appendChild(row);
            row.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });

        // Remove education row (delegated)
        eduContainer.addEventListener('click', (e) => {
            const removeBtn = e.target.closest('.remove-edu-btn');
            if (removeBtn) {
                const row = removeBtn.closest('.education-row');
                row.style.opacity = '0';
                row.style.transform = 'translateX(-20px)';
                row.style.transition = 'all 0.3s ease';
                setTimeout(() => row.remove(), 300);
            }
        });
    }

    // ── Phone Validation ─────────────────────────────────────
    const phoneInput = document.getElementById('phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', () => {
            // Only allow digits
            phoneInput.value = phoneInput.value.replace(/\D/g, '').slice(0, 10);

            if (phoneInput.value.length > 0 && phoneInput.value.length !== 10) {
                phoneInput.classList.add('is-invalid');
            } else {
                phoneInput.classList.remove('is-invalid');
            }
        });
    }

    // ── Form Submit — Loading State ──────────────────────────
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', (e) => {
            // Validate phone if provided
            if (phoneInput && phoneInput.value.length > 0 && phoneInput.value.length !== 10) {
                e.preventDefault();
                phoneInput.classList.add('is-invalid');
                phoneInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
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

    // ── Connect Button AJAX ──────────────────────────────────
    const connectBtn = document.getElementById('connect-btn');
    if (connectBtn) {
        connectBtn.addEventListener('click', async () => {
            const targetUserId = connectBtn.dataset.userId;
            connectBtn.disabled = true;
            connectBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Sending...';

            try {
                const response = await fetch('/api/connections/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: parseInt(targetUserId) }),
                });

                if (response.ok) {
                    connectBtn.innerHTML = '<i class="bi bi-clock me-1"></i>Request Sent';
                    connectBtn.classList.replace('btn-primary', 'btn-secondary');
                } else {
                    connectBtn.innerHTML = '<i class="bi bi-person-plus me-1"></i>Connect';
                    connectBtn.disabled = false;
                }
            } catch (err) {
                connectBtn.innerHTML = '<i class="bi bi-person-plus me-1"></i>Connect';
                connectBtn.disabled = false;
            }
        });
    }
});
