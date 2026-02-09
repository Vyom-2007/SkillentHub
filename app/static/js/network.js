/**
 * Network JavaScript
 * Handles search, filtering, and user card rendering
 */

// ========== INITIALIZATION ==========

let currentPage = 1;
let searchTimeout = null;
let selectedSkills = [];

document.addEventListener('DOMContentLoaded', function () {
    initSearch();
    initSkillFilters();
    initLocationFilter();

    currentPage = parseInt(document.getElementById('currentPage')?.value || 1);
});

// ========== DEBOUNCED SEARCH ==========

function initSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(performSearch, 300);
        });
    }
}

function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// ========== SKILL FILTERS ==========

function initSkillFilters() {
    document.querySelectorAll('.skill-filter-badge').forEach(badge => {
        badge.addEventListener('click', function () {
            const skillName = this.dataset.skill;
            const checkbox = this.querySelector('input');

            if (selectedSkills.includes(skillName)) {
                selectedSkills = selectedSkills.filter(s => s !== skillName);
                this.classList.remove('selected');
                checkbox.checked = false;
            } else {
                selectedSkills.push(skillName);
                this.classList.add('selected');
                checkbox.checked = true;
            }

            performSearch();
        });
    });
}

// ========== LOCATION FILTER ==========

function initLocationFilter() {
    const locationFilter = document.getElementById('locationFilter');
    if (locationFilter) {
        locationFilter.addEventListener('change', performSearch);
    }
}

// ========== SEARCH API ==========

function performSearch(page = 1) {
    currentPage = page;

    const q = document.getElementById('searchInput')?.value || '';
    const location = document.getElementById('locationFilter')?.value || '';
    const skills = selectedSkills.join(',');

    // Build URL
    const params = new URLSearchParams();
    if (q) params.append('q', q);
    if (location) params.append('location', location);
    if (skills) params.append('skills', skills);
    params.append('page', page);

    // Show loading
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.style.display = 'flex';

    fetch(`/api/users/search?${params.toString()}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                renderUsers(data.users, page === 1);
                updateResultsCount(data.total);
                updateLoadMore(data.has_more);
            }
        })
        .catch(console.error)
        .finally(() => {
            if (overlay) overlay.style.display = 'none';
        });
}

// ========== RENDER USERS ==========

function renderUsers(users, replace = true) {
    const container = document.getElementById('usersContainer');
    if (!container) return;

    if (replace) {
        container.innerHTML = '';
    }

    if (users.length === 0 && replace) {
        container.innerHTML = `
            <div class="col-12 no-results">
                <i class="bi bi-people display-1 text-muted"></i>
                <p class="mt-3">No users found matching your criteria.</p>
            </div>
        `;
        return;
    }

    users.forEach(user => {
        const html = generateUserCardHTML(user);
        container.insertAdjacentHTML('beforeend', html);
    });
}

function generateUserCardHTML(user) {
    const avatar = user.profile_picture
        ? `/static/uploads/profiles/${user.profile_picture}`
        : `https://ui-avatars.com/api/?name=${encodeURIComponent(user.full_name || 'U')}&size=80&background=random`;

    const skillsHtml = user.skills && user.skills.length > 0
        ? user.skills.slice(0, 3).map(s => `<span class="skill-badge">${escapeHtml(s)}</span>`).join('')
        : '<span class="text-muted small">No skills listed</span>';

    return `
    <div class="col-md-6 col-lg-4 mb-4">
        <div class="user-card">
            <img src="${avatar}" alt="${escapeHtml(user.full_name)}" class="user-avatar">
            <h6 class="user-name">${escapeHtml(user.full_name || 'User')}</h6>
            ${user.headline ? `<p class="user-headline">${escapeHtml(user.headline)}</p>` : '<p class="user-headline text-muted">No headline</p>'}
            ${user.location ? `<p class="user-location"><i class="bi bi-geo-alt me-1"></i>${escapeHtml(user.location)}</p>` : ''}
            <div class="skills-container">${skillsHtml}</div>
            <div class="d-flex gap-2 justify-content-center">
                <a href="/profile/${user.user_id}" class="btn btn-primary btn-sm">
                    <i class="bi bi-person me-1"></i>View
                </a>
                <a href="/messages?user=${user.user_id}" class="btn btn-outline-primary btn-sm">
                    <i class="bi bi-chat me-1"></i>Message
                </a>
            </div>
        </div>
    </div>
    `;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========== UI UPDATES ==========

function updateResultsCount(total) {
    const countEl = document.getElementById('resultsCount');
    if (countEl) {
        countEl.textContent = `${total} user${total !== 1 ? 's' : ''} found`;
    }
}

function updateLoadMore(hasMore) {
    const container = document.getElementById('loadMoreContainer');
    if (container) {
        container.style.display = hasMore ? 'block' : 'none';
    }
}

// ========== LOAD MORE ==========

function loadMore() {
    currentPage++;
    performSearch(currentPage);
}

// ========== CLEAR FILTERS ==========

function clearFilters() {
    // Clear search
    const searchInput = document.getElementById('searchInput');
    if (searchInput) searchInput.value = '';

    // Clear location
    const locationFilter = document.getElementById('locationFilter');
    if (locationFilter) locationFilter.value = '';

    // Clear skills
    selectedSkills = [];
    document.querySelectorAll('.skill-filter-badge').forEach(badge => {
        badge.classList.remove('selected');
        const checkbox = badge.querySelector('input');
        if (checkbox) checkbox.checked = false;
    });

    // Re-search
    performSearch();
}

// Global exports
window.loadMore = loadMore;
window.clearFilters = clearFilters;
