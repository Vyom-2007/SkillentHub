/**
 * SkillentHub — Feed JS (ES6+)
 * Features:
 *   - Image preview
 *   - Read More toggler
 *   - Like / Unlike AJAX (optimistic)
 *   - Comments (Fetch / Post)
 *   - Delete Post
 *   - Auto-refresh polling (5s)
 *   - Relative timestamps
 */

document.addEventListener('DOMContentLoaded', () => {
    // ── 1. Create Post: Image Preview ─────────────────────────
    const postImageInput = document.getElementById('post-image');
    const imagePreviewContainer = document.getElementById('image-preview-container');
    const imagePreview = document.getElementById('image-preview');
    const removeImageBtn = document.getElementById('remove-image-btn');
    const uploadLabel = document.querySelector('.upload-label');

    if (postImageInput && imagePreviewContainer) {
        postImageInput.addEventListener('change', () => {
            const file = postImageInput.files[0];
            if (!file) return;

            if (file.size > 10 * 1024 * 1024) {
                alert('Image must be under 10 MB.');
                postImageInput.value = '';
                return;
            }

            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
                imagePreviewContainer.classList.remove('d-none');
                // Change label style to indicate selection
                uploadLabel.innerHTML = `<i class="bi bi-check-circle-fill me-1 text-success"></i>Photo Selected`;
            };
            reader.readAsDataURL(file);
        });

        removeImageBtn.addEventListener('click', () => {
            postImageInput.value = '';
            imagePreviewContainer.classList.add('d-none');
            imagePreview.src = '';
            uploadLabel.innerHTML = `<i class="bi bi-image me-1"></i>Photo`;
        });
    }

    // ── Create Post: Loading State ─────────────────────────────
    const createForm = document.getElementById('create-post-form');
    if (createForm) {
        createForm.addEventListener('submit', (e) => {
            const content = document.getElementById('post-content').value.trim();
            const hasImage = postImageInput && postImageInput.files.length > 0;

            if (!content && !hasImage) {
                e.preventDefault();
                alert('Please write something or upload a photo.');
                return;
            }

            const btn = document.getElementById('post-submit-btn');
            if (btn) {
                btn.disabled = true;
                btn.querySelector('.btn-text').classList.add('d-none');
                btn.querySelector('.btn-loader').classList.remove('d-none');
            }
        });
    }

    // ── 2. Read More Toggler ───────────────────────────────────
    document.querySelectorAll('.read-more-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const p = link.closest('.post-text');
            const fullText = p.getAttribute('data-full');
            if (fullText) {
                p.textContent = fullText;
            }
        });
    });

    // ── 3. Like / Unlike (Delegated) ───────────────────────────
    document.getElementById('feed-container')?.addEventListener('click', async (e) => {
        const likeBtn = e.target.closest('.like-btn');
        if (!likeBtn) return;

        e.preventDefault();
        const postId = likeBtn.dataset.postId;
        const icon = likeBtn.querySelector('i');
        const countSpan = likeBtn.querySelector('.like-count');
        let count = parseInt(countSpan.textContent, 10);

        // Optimistic UI update
        const isLiked = likeBtn.classList.contains('liked');
        if (isLiked) {
            likeBtn.classList.remove('liked');
            icon.classList.replace('bi-heart-fill', 'bi-heart');
            count = Math.max(0, count - 1);
        } else {
            likeBtn.classList.add('liked');
            icon.classList.replace('bi-heart', 'bi-heart-fill');
            count++;
        }
        countSpan.textContent = count;

        try {
            const res = await fetch(`/api/posts/${postId}/like`, { method: 'POST' });
            const data = await res.json();
            // Reconcile with server
            if (data.liked) {
                likeBtn.classList.add('liked');
                icon.classList.replace('bi-heart', 'bi-heart-fill');
            } else {
                likeBtn.classList.remove('liked');
                icon.classList.replace('bi-heart-fill', 'bi-heart');
            }
            countSpan.textContent = data.count;
        } catch (err) {
            console.error('Like failed', err);
            // Revert on failure could be added here
        }
    });

    // ── 4. Comments (Delegated) ────────────────────────────────
    // Toggle Comments Section & Load
    document.getElementById('feed-container')?.addEventListener('click', async (e) => {
        const toggleBtn = e.target.closest('.comment-toggle-btn');
        if (!toggleBtn) return;

        const postId = toggleBtn.dataset.postId;
        const section = document.getElementById(`comments-${postId}`);
        const list = document.getElementById(`comments-list-${postId}`);

        if (section.classList.contains('d-none')) {
            section.classList.remove('d-none');
            // Fetch comments if empty
            if (list.children.length === 0) {
                loadComments(postId, list);
            }
        } else {
            section.classList.add('d-none');
        }
    });

    async function loadComments(postId, listElement) {
        listElement.innerHTML = '<div class="text-center py-2"><span class="spinner-border spinner-border-sm text-secondary"></span></div>';
        try {
            const res = await fetch(`/api/posts/${postId}/comments`);
            const comments = await res.json();
            listElement.innerHTML = '';

            if (comments.length === 0) {
                listElement.innerHTML = '<p class="text-muted small text-center my-2">No comments yet.</p>';
                return;
            }

            comments.forEach(c => appendComment(listElement, c));
        } catch (err) {
            listElement.innerHTML = '<p class="text-danger small text-center">Failed to lead comments.</p>';
        }
    }

    function appendComment(listElement, c) {
        // Remove "No comments" msg if exists
        const noCommentsMsg = listElement.querySelector('.text-center.my-2');
        if (noCommentsMsg) noCommentsMsg.remove();

        const div = document.createElement('div');
        div.className = 'comment-item';
        const avatarUrl = c.profile_picture ? `/${c.profile_picture}` : '';
        const timeAgo = timeSince(new Date(c.created_at));

        div.innerHTML = `
            <div class="comment-avatar">
                ${avatarUrl
                ? `<img src="${avatarUrl}" alt="${c.full_name}">`
                : `<div class="comment-avatar-placeholder"><i class="bi bi-person-fill"></i></div>`
            }
            </div>
            <div class="comment-body">
                <span class="comment-author">${c.full_name}</span>
                <p class="comment-text">${escapeHtml(c.content)}</p>
                <span class="comment-time">${timeAgo}</span>
            </div>
        `;
        listElement.appendChild(div);
    }

    // Post Comment
    document.getElementById('feed-container')?.addEventListener('click', async (e) => {
        const sendBtn = e.target.closest('.send-comment-btn');
        if (!sendBtn) return;

        const postId = sendBtn.dataset.postId;
        const input = sendBtn.previousElementSibling; // .comment-input
        const content = input.value.trim();
        const list = document.getElementById(`comments-list-${postId}`);

        if (!content) return;

        // Disable input
        input.disabled = true;
        sendBtn.disabled = true;

        try {
            const res = await fetch(`/api/posts/${postId}/comments`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content })
            });
            const newComment = await res.json();

            if (res.ok) {
                input.value = '';
                appendComment(list, newComment);
                // Scroll to bottom
                list.scrollTop = list.scrollHeight;
            } else {
                alert(newComment.error || 'Failed to post comment');
            }
        } catch (err) {
            alert('Error posting comment');
        } finally {
            input.disabled = false;
            sendBtn.disabled = false;
            input.focus();
        }
    });

    // ── 5. Delete Post ─────────────────────────────────────────
    document.getElementById('feed-container')?.addEventListener('click', async (e) => {
        const delBtn = e.target.closest('.delete-post-btn');
        if (!delBtn) return;

        if (!confirm('Are you sure you want to delete this post?')) return;

        const postId = delBtn.dataset.postId;
        const card = delBtn.closest('.post-card');

        try {
            const res = await fetch(`/api/posts/${postId}`, { method: 'DELETE' });
            if (res.ok) {
                card.style.opacity = '0';
                card.style.transform = 'scale(0.9)';
                setTimeout(() => card.remove(), 300);
            } else {
                alert('Failed to delete post.');
            }
        } catch (err) {
            console.error(err);
        }
    });

    // ── 6. Auto-Refresh Polling (5s) ───────────────────────────
    const banner = document.getElementById('new-posts-banner');
    const bannerText = document.getElementById('new-posts-text');
    const latestPostInput = document.getElementById('latest-post-id');

    if (latestPostInput) {
        let latestId = parseInt(latestPostInput.value, 10);

        setInterval(async () => {
            try {
                const res = await fetch(`/api/feed/new?since=${latestId}`);
                const data = await res.json();

                if (data.new_count > 0) {
                    bannerText.textContent = `${data.new_count} new post${data.new_count > 1 ? 's' : ''}`;
                    banner.classList.remove('d-none');
                }
            } catch (err) {
                /* silent fail */
            }
        }, 5000);

        banner.addEventListener('click', () => {
            window.location.reload();
        });
    }

    // ── 7. Relative Time ───────────────────────────────────────
    function timeSince(date) {
        const seconds = Math.floor((new Date() - date) / 1000);
        let interval = seconds / 31536000;
        if (interval > 1) return Math.floor(interval) + " years ago";
        interval = seconds / 2592000;
        if (interval > 1) return Math.floor(interval) + " months ago";
        interval = seconds / 86400;
        if (interval > 1) return Math.floor(interval) + " days ago";
        interval = seconds / 3600;
        if (interval > 1) return Math.floor(interval) + " hours ago";
        interval = seconds / 60;
        if (interval > 1) return Math.floor(interval) + " minutes ago";
        return "Just now";
    }

    function updateTimestamps() {
        document.querySelectorAll('.post-time').forEach(el => {
            const iso = el.getAttribute('data-time');
            if (iso) el.textContent = timeSince(new Date(iso));
        });
    }

    updateTimestamps();
    setInterval(updateTimestamps, 60000); // update every minute

    // Utility
    function escapeHtml(text) {
        const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
});
