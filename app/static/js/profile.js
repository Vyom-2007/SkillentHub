/**
 * Profile Management JavaScript
 * Handles image preview, dynamic education forms, validation, and bio counter
 */

function initProfileForm() {
    // Image preview
    const pictureInput = document.getElementById('profilePicture');
    if (pictureInput) {
        pictureInput.addEventListener('change', handleImagePreview);
    }

    // Skills toggle
    initSkillsToggle();

    // Bio counter
    const bioTextarea = document.getElementById('bio');
    if (bioTextarea) {
        bioTextarea.addEventListener('input', updateBioCounter);
        updateBioCounter();
    }

    // Add education button
    const addBtn = document.getElementById('addEducation');
    if (addBtn) {
        addBtn.addEventListener('click', function () { addEducationEntry(); });
    }

    // Phone validation
    const phoneInput = document.getElementById('phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', function () {
            this.value = this.value.replace(/\D/g, '').slice(0, 10);
        });
    }

    // Form validation
    const form = document.getElementById('profileForm');
    if (form) {
        form.addEventListener('submit', validateForm);
    }

    // Custom skills
    const addSkillBtn = document.getElementById('addSkillBtn');
    if (addSkillBtn) {
        addSkillBtn.addEventListener('click', addCustomSkill);
    }

    // Allow Enter key to add skill
    const skillInput = document.getElementById('customSkillInput');
    if (skillInput) {
        skillInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addCustomSkill();
            }
        });
    }
}

function addCustomSkill() {
    const input = document.getElementById('customSkillInput');
    const container = document.getElementById('skillsContainer');

    if (!input || !container) return;

    const skillName = input.value.trim();
    if (!skillName) return;

    // Check if duplicate
    const existingLabels = Array.from(container.querySelectorAll('label')).map(l => l.innerText.toLowerCase());
    if (existingLabels.includes(skillName.toLowerCase())) {
        alert('Skill already added!');
        return;
    }

    // Create new badge
    const badge = document.createElement('div');
    badge.className = 'skill-badge selected';

    // Add hidden input for custom skill name
    const hiddenInput = document.createElement('input');
    hiddenInput.type = 'hidden';
    hiddenInput.name = 'custom_skills[]';
    hiddenInput.value = skillName;

    // Use a checkbox just for visual consistency with existing CSS/JS (or just bypass)
    // Actually, existing JS toggle relies on checkbox. Let's add a dummy checked checkbox so it stays "selected"
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = true;
    checkbox.style.display = 'none';

    const label = document.createElement('label');
    label.innerText = skillName;
    label.style.cursor = 'pointer';

    // Delete button (x)
    const removeSpan = document.createElement('span');
    removeSpan.innerHTML = '<i class="bi bi-x ms-2"></i>';
    removeSpan.style.cursor = 'pointer';
    removeSpan.onclick = function (e) {
        e.stopPropagation(); // Prevent toggling
        badge.remove();
    };

    badge.appendChild(hiddenInput);
    badge.appendChild(checkbox);
    badge.appendChild(label);
    badge.appendChild(removeSpan);

    container.appendChild(badge);
    input.value = '';

    // Re-bind toggle logic? No, these are always selected custom skills. 
    // But if clicked, they might toggle off? 
    // Let's make them fixed as selected for now, or just allow toggling off (which effectively removes them?)
    // Simpler: If clicked, do nothing or remove? 
    // Let's attach the click listener to toggle "selected" class but keep the hidden input?
    // Actually, if unselected, they probably shouldn't be submitted.
    // Better: Allow them to be removed via the 'x'. Clicking otherwise does nothing or toggles?
    // Let's stick to the 'x' to remove.
}

function handleImagePreview(event) {
    const file = event.target.files[0];
    const preview = document.getElementById('picturePreview');

    if (!file) return;

    const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    if (!validTypes.includes(file.type)) {
        alert('Please select a JPG or PNG image.');
        event.target.value = '';
        return;
    }

    if (file.size > 5 * 1024 * 1024) {
        alert('File size exceeds 5MB limit.');
        event.target.value = '';
        return;
    }

    const reader = new FileReader();
    reader.onload = function (e) {
        preview.src = e.target.result;
        preview.style.display = '';  // Make the img visible
        // Hide the initials avatar div if present
        const initialsDiv = document.getElementById('picturePreviewDiv');
        if (initialsDiv) {
            initialsDiv.style.display = 'none';
        }
    };
    reader.readAsDataURL(file);
}

function initSkillsToggle() {
    document.querySelectorAll('.skill-badge').forEach(badge => {
        const checkbox = badge.querySelector('input[type="checkbox"]');
        const label = badge.querySelector('label');
        if (!checkbox) return;

        // Set initial visual state
        if (checkbox.checked) {
            badge.classList.add('selected');
        }

        // Prevent label from triggering checkbox (we'll handle it manually)
        if (label) {
            label.addEventListener('click', function (e) {
                e.preventDefault();
            });
        }

        // Handle click on the entire badge div
        badge.addEventListener('click', function (e) {
            // Toggle checkbox manually
            checkbox.checked = !checkbox.checked;
            badge.classList.toggle('selected', checkbox.checked);
        });
    });
}

function updateBioCounter() {
    const bio = document.getElementById('bio');
    const count = document.getElementById('bioCount');
    if (bio && count) {
        count.textContent = bio.value.length;
    }
}

let eduIndex = 0;

function addEducationEntry(prefilled = null) {
    const container = document.getElementById('educationContainer');
    if (!container) return;

    eduIndex++;

    const html = `
        <div class="education-entry" data-index="${eduIndex}">
            <button type="button" class="remove-btn" onclick="removeEducation(this)">
                <i class="bi bi-x-circle"></i>
            </button>
            <div class="row">
                <div class="col-md-6 mb-2">
                    <input type="text" class="form-control" name="edu_institution[]"
                           value="${prefilled?.institution_name || ''}" placeholder="Institution *" required>
                </div>
                <div class="col-md-6 mb-2">
                    <input type="text" class="form-control" name="edu_degree[]"
                           value="${prefilled?.degree || ''}" placeholder="Degree *" required>
                </div>
                <div class="col-md-4 mb-2">
                    <input type="text" class="form-control" name="edu_field[]"
                           value="${prefilled?.field_of_study || ''}" placeholder="Field of Study">
                </div>
                <div class="col-md-4 mb-2">
                    <input type="number" class="form-control" name="edu_start[]"
                           value="${prefilled?.start_year || ''}" placeholder="Start Year" min="1950" max="2030">
                </div>
                <div class="col-md-4 mb-2">
                    <input type="number" class="form-control" name="edu_end[]"
                           value="${prefilled?.end_year || ''}" placeholder="End Year" min="1950" max="2030">
                </div>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', html);
}

function removeEducation(button) {
    const entry = button.closest('.education-entry');
    const educationId = entry.dataset.id;

    if (educationId) {
        fetch(`/profile/education/delete/${educationId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        }).catch(console.error);
    }

    entry.remove();
}

function validateForm(event) {
    const form = event.target;
    let valid = true;
    const errors = [];

    const fullName = form.querySelector('[name="full_name"]');
    const headline = form.querySelector('[name="headline"]');
    const phone = form.querySelector('[name="phone"]');

    if (!fullName.value.trim()) {
        errors.push('Full name is required');
        valid = false;
    }

    if (!headline.value.trim()) {
        errors.push('Headline is required');
        valid = false;
    }

    if (phone && phone.value && phone.value.length !== 10) {
        errors.push('Phone must be 10 digits');
        valid = false;
    }

    if (!valid) {
        event.preventDefault();
        alert(errors.join('\n'));
    }

    return valid;
}

// Global exports
window.initProfileForm = initProfileForm;
window.addEducationEntry = addEducationEntry;
window.removeEducation = removeEducation;
window.updateBioCounter = updateBioCounter;
