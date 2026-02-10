document.addEventListener('DOMContentLoaded', function () {
    // === Create Post ===
    const postContent = document.getElementById('postContent');
    const postImage = document.getElementById('postImage');
    const postBtn = document.getElementById('postBtn');
    const fileName = document.getElementById('fileName');

    if (postContent) {
        postContent.addEventListener('input', () => {
            postBtn.disabled = postContent.value.trim() === '';
        });

        postImage.addEventListener('change', () => {
            if (postImage.files.length > 0) {
                fileName.textContent = postImage.files[0].name;
                postBtn.disabled = false;
            } else {
                fileName.textContent = '';
                postBtn.disabled = postContent.value.trim() === '';
            }
        });

        postBtn.addEventListener('click', async () => {
            const formData = new FormData();
            formData.append('content', postContent.value);
            if (postImage.files.length > 0) {
                formData.append('image', postImage.files[0]);
            }

            // Assuming Post API at /api/posts/create
            // But blueprint prefix is /api/posts in __init__
            // Wait, prefix was /api/posts. So route /create is /api/posts/create

            try {
                const res = await fetch('/api/posts/create', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (data.status === 'success') {
                    window.location.reload(); // Simple reload for now to show new post
                } else {
                    alert('Error: ' + data.message);
                }
            } catch (e) {
                console.error(e);
            }
        });
    }

    // === Like Button ===
    document.addEventListener('click', async function (e) {
        if (e.target.closest('.like-btn')) {
            const btn = e.target.closest('.like-btn');
            const card = btn.closest('.post-card');
            const postId = card.dataset.postId;

            try {
                const res = await fetch(`/api/posts/${postId}/like`, { method: 'POST' });
                const data = await res.json();
                if (data.status === 'success') {
                    const countSpan = btn.querySelector('.like-count');
                    countSpan.textContent = data.count;
                    if (data.liked) {
                        btn.classList.add('text-primary', 'fw-bold');
                        btn.classList.remove('text-muted');
                    } else {
                        btn.classList.remove('text-primary', 'fw-bold');
                        btn.classList.add('text-muted');
                    }
                }
            } catch (e) { console.error(e); }
        }
    });

    // === Comments ===
    document.addEventListener('click', function (e) {
        if (e.target.closest('.comment-toggle')) {
            const card = e.target.closest('.post-card');
            const section = card.querySelector('.comments-section');
            if (section.style.display === 'none') {
                section.style.display = 'block';
                // Load comments?
                loadComments(card.dataset.postId, section.querySelector('.comments-list'));
            } else {
                section.style.display = 'none';
            }
        }
    });

    document.addEventListener('click', async function (e) {
        if (e.target.classList.contains('comment-submit')) {
            const section = e.target.closest('.comments-section');
            const input = section.querySelector('.comment-input');
            const card = e.target.closest('.post-card');
            const list = section.querySelector('.comments-list');

            if (input.value.trim() === '') return;

            try {
                const res = await fetch(`/api/posts/${card.dataset.postId}/comments`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: input.value })
                });
                const data = await res.json();
                if (data.status === 'success') {
                    input.value = '';
                    loadComments(card.dataset.postId, list);
                }
            } catch (e) { console.error(e); }
        }
    });

    async function loadComments(postId, listContainer) {
        try {
            const res = await fetch(`/api/posts/${postId}/comments`);
            const data = await res.json();
            if (data.status === 'success') {
                listContainer.innerHTML = data.comments.map(c => `
                    <div class="mb-2 bg-light p-2 rounded">
                        <strong>${c.full_name}</strong>: ${c.content}
                    </div>
                `).join('');
            }
        } catch (e) { console.error(e); }
    }

    // === Auto Refresh ===
    setInterval(checkForNewPosts, 5000);

    async function checkForNewPosts() {
        const firstCard = document.querySelector('.post-card');
        if (!firstCard) return;

        // Post ID is what we want, not Timestamp for 'since' usually, but here ID is safer
        const lastId = firstCard.dataset.postId;

        try {
            const res = await fetch(`/api/feed/new?since=${lastId}`);
            const data = await res.json();

            if (data.status === 'success' && data.count > 0) {
                const banner = document.getElementById('newPostsBanner');
                if (banner) {
                    banner.textContent = `${data.count} new posts available. Click to Refresh.`;
                    banner.style.display = 'block';
                    banner.onclick = () => window.location.reload();
                }
            }
        } catch (e) { console.error(e); }
    }
});
