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
