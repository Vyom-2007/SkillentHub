/**
 * Feed JavaScript
 * Handles auto-refresh, likes, comments, and post interactions
 */

// ========== INITIALIZATION ==========

document.addEventListener('DOMContentLoaded', function () {
    initCharCounter();
    initImagePreview();
    initTimeAgo();
    startAutoRefresh();
});

// ========== CHARACTER COUNTER ==========

function initCharCounter() {
    const content = document.getElementById('postContent');
    const count = document.getElementById('charCount');

    if (content && count) {
        content.addEventListener('input', function () {
            count.textContent = this.value.length;
        });
    }
}

// ========== IMAGE PREVIEW ==========

function initImagePreview() {
    const imageInput = document.getElementById('postImage');
    const preview = document.getElementById('imagePreview');
    const container = document.getElementById('imagePreviewContainer');

    if (imageInput && preview && container) {
        imageInput.addEventListener('change', function () {
            const file = this.files[0];
            if (file) {
                // Validate size
                if (file.size > 10 * 1024 * 1024) {
                    alert('File size exceeds 10MB limit');
                    this.value = '';
                    return;
                }

                const reader = new FileReader();
                reader.onload = function (e) {
                    preview.src = e.target.result;
                    container.style.display = 'block';
                };
                reader.readAsDataURL(file);
            } else {
                container.style.display = 'none';
            }
        });
    }
}

function removeImagePreview() {
    const imageInput = document.getElementById('postImage');
    const container = document.getElementById('imagePreviewContainer');

    if (imageInput) imageInput.value = '';
    if (container) container.style.display = 'none';
}

// ========== TIME AGO ==========

function initTimeAgo() {
    document.querySelectorAll('.time-ago[data-time]').forEach(el => {
        const time = el.dataset.time;
        if (time) {
            el.textContent = timeAgo(new Date(time));
        }
    });
}

function timeAgo(date) {
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);

    if (diff < 60) return 'Just now';
    if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
    if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
    if (diff < 604800) return Math.floor(diff / 86400) + 'd ago';

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

// ========== AUTO-REFRESH ==========

let lastPostId = 0;
let pendingPosts = [];

function startAutoRefresh() {
    const firstPostIdEl = document.getElementById('firstPostId');
    if (firstPostIdEl) {
        lastPostId = parseInt(firstPostIdEl.value) || 0;
    }

    // Check for new posts every 5 seconds
    setInterval(checkNewPosts, 5000);
}

function checkNewPosts() {
    if (lastPostId === 0) return;

    fetch(`/api/feed/new?since=${lastPostId}`)
        .then(res => res.json())
        .then(data => {
            if (data.success && data.count > 0) {
                pendingPosts = data.posts;
                showNewPostsBanner(data.count);

                // Update lastPostId to the newest
                if (data.posts.length > 0) {
                    lastPostId = Math.max(...data.posts.map(p => p.post_id));
                }
            }
        })
        .catch(console.error);
}

function showNewPostsBanner(count) {
    const banner = document.getElementById('newPostsBanner');
    const countEl = document.getElementById('newPostsCount');

    if (banner && countEl) {
        countEl.textContent = count;
        banner.style.display = 'block';
    }
}

function loadNewPosts() {
    const container = document.getElementById('postsContainer');
    const banner = document.getElementById('newPostsBanner');

    if (!container || pendingPosts.length === 0) return;

    // Generate HTML for new posts
    pendingPosts.forEach(post => {
        const html = generatePostHTML(post);
        container.insertAdjacentHTML('afterbegin', html);
    });

    // Reinit time ago
    initTimeAgo();

    // Clear and hide banner
    pendingPosts = [];
    banner.style.display = 'none';
}

function generatePostHTML(post) {
    const profilePic = post.profile_picture
        ? `/static/uploads/profiles/${post.profile_picture}`
        : `https://ui-avatars.com/api/?name=${encodeURIComponent(post.full_name || 'U')}&size=48&background=random`;

    const imageHtml = post.image_path
        ? `<img src="/static/uploads/posts/${post.image_path}" alt="Post image" class="post-image">`
        : '';

    const truncated = post.content.length > 300 ? 'truncated' : '';
    const readMore = post.content.length > 300
        ? `<span class="read-more" onclick="toggleContent(${post.post_id})">Read more</span>`
        : '';

    const likedClass = post.liked_by_current_user ? 'liked' : '';
    const heartIcon = post.liked_by_current_user ? 'bi-heart-fill' : 'bi-heart';

    return `
    <div class="post-card" data-post-id="${post.post_id}">
        <div class="d-flex align-items-start gap-3">
            <img src="${profilePic}" alt="${post.full_name}" class="post-author-pic">
            <div class="flex-grow-1">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <a href="/profile/${post.author_id}" class="fw-bold text-dark text-decoration-none">
                            ${post.full_name || 'User'}
                        </a>
                        ${post.headline ? `<p class="text-muted small mb-0">${post.headline}</p>` : ''}
                        <span class="time-ago" data-time="${post.created_at}">Just now</span>
                    </div>
                </div>
            </div>
        </div>
        <div class="mt-3">
            <p class="post-content ${truncated}" id="content-${post.post_id}">${escapeHtml(post.content)}</p>
            ${readMore}
        </div>
        ${imageHtml}
        <div class="post-actions">
            <button class="post-action-btn ${likedClass}" onclick="toggleLike(${post.post_id})" id="like-btn-${post.post_id}">
                <i class="bi ${heartIcon}"></i>
                <span id="likes-count-${post.post_id}">${post.likes_count || 0}</span>
            </button>
            <button class="post-action-btn" onclick="toggleComments(${post.post_id})">
                <i class="bi bi-chat"></i>
                <span id="comments-count-${post.post_id}">${post.comments_count || 0}</span>
            </button>
        </div>
        <div class="comments-section" id="comments-section-${post.post_id}" style="display: none;">
            <div id="comments-list-${post.post_id}"></div>
            <div class="comment-input">
                <input type="text" class="form-control form-control-sm" 
                       placeholder="Write a comment..." id="comment-input-${post.post_id}"
                       onkeypress="if(event.key === 'Enter') submitComment(${post.post_id})">
                <button class="btn btn-primary btn-sm" onclick="submitComment(${post.post_id})">
                    <i class="bi bi-send"></i>
                </button>
            </div>
        </div>
    </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========== POST CONTENT ==========

function toggleContent(postId) {
    const content = document.getElementById(`content-${postId}`);
    const readMore = content.nextElementSibling;

    if (content.classList.contains('truncated')) {
        content.classList.remove('truncated');
        readMore.textContent = 'Show less';
    } else {
        content.classList.add('truncated');
        readMore.textContent = 'Read more';
    }
}

// ========== LIKES ==========

function toggleLike(postId) {
    const btn = document.getElementById(`like-btn-${postId}`);
    const countEl = document.getElementById(`likes-count-${postId}`);
    const icon = btn.querySelector('i');

    // Optimistic update
    const wasLiked = btn.classList.contains('liked');
    let count = parseInt(countEl.textContent) || 0;

    if (wasLiked) {
        btn.classList.remove('liked');
        icon.classList.replace('bi-heart-fill', 'bi-heart');
        countEl.textContent = Math.max(0, count - 1);
    } else {
        btn.classList.add('liked');
        icon.classList.replace('bi-heart', 'bi-heart-fill');
        countEl.textContent = count + 1;
    }

    // Send request
    fetch(`/api/posts/${postId}/like`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                countEl.textContent = data.likes_count;
                if (data.liked) {
                    btn.classList.add('liked');
                    icon.classList.replace('bi-heart', 'bi-heart-fill');
                } else {
                    btn.classList.remove('liked');
                    icon.classList.replace('bi-heart-fill', 'bi-heart');
                }
            }
        })
        .catch(console.error);
}

// ========== COMMENTS ==========

function toggleComments(postId) {
    const section = document.getElementById(`comments-section-${postId}`);
    const list = document.getElementById(`comments-list-${postId}`);

    if (section.style.display === 'none') {
        section.style.display = 'block';

        // Load comments if not already loaded
        if (list.children.length === 0) {
            loadComments(postId);
        }
    } else {
        section.style.display = 'none';
    }
}

function loadComments(postId) {
    const list = document.getElementById(`comments-list-${postId}`);

    fetch(`/api/posts/${postId}/comments`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                list.innerHTML = data.comments.map(c => generateCommentHTML(c)).join('');
            }
        })
        .catch(console.error);
}

function submitComment(postId) {
    const input = document.getElementById(`comment-input-${postId}`);
    const content = input.value.trim();

    if (!content) return;

    fetch(`/api/posts/${postId}/comment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const list = document.getElementById(`comments-list-${postId}`);
                list.insertAdjacentHTML('beforeend', generateCommentHTML(data.comment));

                // Update count
                const countEl = document.getElementById(`comments-count-${postId}`);
                countEl.textContent = parseInt(countEl.textContent) + 1;

                // Clear input
                input.value = '';
            }
        })
        .catch(console.error);
}

function generateCommentHTML(comment) {
    const pic = comment.profile_picture
        ? `/static/uploads/profiles/${comment.profile_picture}`
        : `https://ui-avatars.com/api/?name=${encodeURIComponent(comment.full_name || 'U')}&size=32&background=random`;

    return `
    <div class="comment">
        <img src="${pic}" alt="${comment.full_name}" class="comment-pic">
        <div class="comment-content">
            <span class="comment-author">${escapeHtml(comment.full_name || 'User')}</span>
            <p class="comment-text mb-0">${escapeHtml(comment.content)}</p>
        </div>
    </div>
    `;
}

// ========== DELETE POST ==========

function deletePost(postId) {
    if (!confirm('Are you sure you want to delete this post?')) return;

    fetch(`/api/posts/${postId}`, { method: 'DELETE' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const card = document.querySelector(`[data-post-id="${postId}"]`);
                if (card) card.remove();
            } else {
                alert(data.error || 'Failed to delete post');
            }
        })
        .catch(console.error);
}

// Global exports for inline onclick handlers
window.toggleContent = toggleContent;
window.toggleLike = toggleLike;
window.toggleComments = toggleComments;
window.submitComment = submitComment;
window.deletePost = deletePost;
window.loadNewPosts = loadNewPosts;
window.removeImagePreview = removeImagePreview;
