/**
 * Opportunities JavaScript
 * Handles filtering, search, and application form
 */

// ========== INITIALIZATION ==========

let currentType = 'all';
let searchTimeout = null;

document.addEventListener('DOMContentLoaded', function () {
    currentType = document.getElementById('currentType')?.value || 'all';

    initFilters();
    initSearch();
    initApplyForm();
    initCoverLetterCounter();
});

// ========== FILTER HANDLING ==========

function initFilters() {
    // Type tabs
    document.querySelectorAll('.type-tab').forEach(tab => {
        tab.addEventListener('click', function () {
            document.querySelectorAll('.type-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            currentType = this.dataset.type;

            // Show/hide job type filter
            const jobTypeSection = document.getElementById('jobTypeSection');
            if (jobTypeSection) {
                jobTypeSection.style.display = currentType === 'internship' ? 'none' : 'block';
            }

            performSearch();
        });
    });

    // Other filters
    ['locationFilter', 'workModeFilter', 'jobTypeFilter', 'dateFilter', 'experienceFilter'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('change', performSearch);
        }
    });

    // Skill filters
    document.querySelectorAll('.skill-filter').forEach(el => {
        el.addEventListener('change', performSearch);
    });
}

// ========== SEARCH ==========

function initSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(performSearch, 300);
        });
    }
}

function performSearch() {
    const params = new URLSearchParams();

    params.append('type', currentType);

    const q = document.getElementById('searchInput')?.value.trim();
    if (q) params.append('q', q);

    const location = document.getElementById('locationFilter')?.value;
    if (location) params.append('location', location);

    const workMode = document.getElementById('workModeFilter')?.value;
    if (workMode) params.append('work_mode', workMode);

    const jobType = document.getElementById('jobTypeFilter')?.value;
    if (jobType && currentType !== 'internship') params.append('job_type', jobType);

    const datePosted = document.getElementById('dateFilter')?.value;
    if (datePosted) params.append('date_posted', datePosted);

    const experience = document.getElementById('experienceFilter')?.value;
    if (experience) params.append('experience', experience);

    // Skills
    document.querySelectorAll('.skill-filter:checked').forEach(el => {
        params.append('skills[]', el.value);
    });

    showLoading(true);

    fetch(`/api/opportunities/search?${params.toString()}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                renderOpportunities(data.opportunities);
            }
        })
        .catch(console.error)
        .finally(() => showLoading(false));
}

function renderOpportunities(opportunities) {
    const container = document.getElementById('opportunitiesContainer');
    if (!container) return;

    if (opportunities.length === 0) {
        container.innerHTML = `
            <div class="no-results">
                <i class="bi bi-briefcase display-1"></i>
                <p class="mt-3">No opportunities found matching your criteria.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = opportunities.map(item => {
        let matchBadge = '';
        if (item.match_score !== undefined && item.match_score !== null) {
            let color = 'secondary';
            if (item.match_score >= 80) color = 'success';
            else if (item.match_score >= 50) color = 'warning text-dark';
            matchBadge = `<div class="mb-1"><span class="badge bg-${color}">Match: ${item.match_score}%</span></div>`;
        }

        return `
        <div class="opp-card">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <span class="opp-badge ${item.type === 'job' ? 'badge-job' : 'badge-internship'}">
                        ${item.type.charAt(0).toUpperCase() + item.type.slice(1)}
                    </span>
                    <span class="opp-badge ${item.work_mode === 'remote' ? 'badge-remote' : item.work_mode === 'hybrid' ? 'badge-hybrid' : 'badge-onsite'}">
                        ${(item.work_mode || 'on-site').replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                </div>
                <div class="text-end">
                    ${matchBadge}
                    <small class="text-muted">${formatDate(item.posted_at)}</small>
                </div>
            </div>
            <h5 class="opp-title mt-2">${escapeHtml(item.title)}</h5>
            <p class="opp-company mb-1">${escapeHtml(item.company_name || 'Company')}</p>
            <p class="opp-meta">
                <i class="bi bi-geo-alt me-1"></i>${escapeHtml(item.location)}
                ${item.salary_range ? `<span class="ms-3"><i class="bi bi-currency-rupee me-1"></i>${escapeHtml(item.salary_range)}</span>` : ''}
                ${item.stipend ? `<span class="ms-3"><i class="bi bi-currency-rupee me-1"></i>${escapeHtml(item.stipend)}</span>` : ''}
                ${item.duration ? `<span class="ms-3"><i class="bi bi-clock me-1"></i>${escapeHtml(item.duration)}</span>` : ''}
            </p>
            ${item.skills_required ? `
                <div class="mt-2">
                    ${item.skills_required.split(',').slice(0, 5).map(s => `<span class="skill-tag">${escapeHtml(s.trim())}</span>`).join('')}
                </div>
            ` : ''}
            <div class="mt-3">
                <a href="/${item.type === 'job' ? 'jobs' : 'internships'}/${item.id}" class="btn btn-primary btn-sm">View Details</a>
            </div>
        </div>
    `}).join('');
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('locationFilter').value = '';
    document.getElementById('workModeFilter').value = '';
    document.getElementById('jobTypeFilter').value = '';
    document.getElementById('dateFilter').value = '';
    const expFilter = document.getElementById('experienceFilter');
    if (expFilter) expFilter.value = '';

    document.querySelectorAll('.skill-filter').forEach(el => el.checked = false);

    currentType = 'all';
    document.querySelectorAll('.type-tab').forEach(t => t.classList.remove('active'));
    document.querySelector('.type-tab[data-type="all"]')?.classList.add('active');

    performSearch();
}

// ========== APPLY FORM ==========

function initApplyForm() {
    const form = document.getElementById('applyForm');
    if (!form) return;

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const resumeInput = document.getElementById('resumeInput');
        const file = resumeInput?.files[0];

        // Client-side validation
        if (file) {
            if (!file.name.toLowerCase().endsWith('.pdf')) {
                alert('Please upload a PDF file only.');
                return;
            }
            if (file.size > 10 * 1024 * 1024) {
                alert('File size exceeds 10MB limit.');
                return;
            }
        }

        const submitBtn = document.getElementById('submitBtn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting...';

        const formData = new FormData(form);

        fetch('/applications/apply', {
            method: 'POST',
            body: formData
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert('Application submitted successfully!');
                    window.location.reload();
                } else {
                    alert(data.error || 'Failed to submit application');
                }
            })
            .catch(err => {
                console.error(err);
                alert('Failed to submit application');
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="bi bi-send me-2"></i>Submit Application';
            });
    });
}

function initCoverLetterCounter() {
    const textarea = document.querySelector('textarea[name="cover_letter"]');
    const counter = document.getElementById('coverLetterCount');

    if (textarea && counter) {
        textarea.addEventListener('input', function () {
            counter.textContent = this.value.length;
        });
    }
}

// ========== UTILITIES ==========

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = show ? 'flex' : 'none';
    }
}

function formatDate(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Global exports
window.clearFilters = clearFilters;
window.toggleSave = toggleSave;

async function toggleSave(btn, type, id) {
    const icon = btn.querySelector('i');
    const isSaved = icon.classList.contains('bi-bookmark-fill');
    const action = isSaved ? 'unsave' : 'save';

    try {
        const response = await fetch(`/opportunities/${action}/${type}/${id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success) {
            if (isSaved) {
                icon.classList.remove('bi-bookmark-fill', 'text-primary');
                icon.classList.add('bi-bookmark');
                btn.title = 'Save';
            } else {
                icon.classList.remove('bi-bookmark');
                icon.classList.add('bi-bookmark-fill', 'text-primary');
                btn.title = 'Unsave';
            }
        } else {
            console.error('Failed to toggle save');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}
