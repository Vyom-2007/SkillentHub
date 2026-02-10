document.addEventListener('DOMContentLoaded', function () {
    const chatArea = document.getElementById('chatArea');
    const msgInput = document.getElementById('msgInput');
    const sendBtn = document.getElementById('sendBtn');

    if (chatArea) {
        // Scroll to bottom
        chatArea.scrollTop = chatArea.scrollHeight;

        // Send
        sendBtn.addEventListener('click', sendMessage);
        msgInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });

        // Poll
        setInterval(fetchMessages, 3000);
    }

    async function sendMessage() {
        const content = msgInput.value.trim();
        if (!content) return;

        try {
            const res = await fetch('/messages/api/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    receiver_id: PARTNER_ID,
                    content: content
                })
            });
            const data = await res.json();
            if (data.status === 'success') {
                msgInput.value = '';
                fetchMessages(); // Refresh immediately
            }
        } catch (e) { }
    }

    async function fetchMessages() {
        try {
            const res = await fetch(`/messages/api/history/${PARTNER_ID}`);
            const data = await res.json();
            if (data.status === 'success') {
                updateChatUI(data.messages);
            }
        } catch (e) { }
    }

    function updateChatUI(messages) {
        // Simple full redraw for now (inefficient but safe)
        // Optimization: Append only new
        chatArea.innerHTML = messages.map(m => {
            const isMe = m.sender_id === MY_ID;
            return `
                <div class="d-flex mb-2 ${isMe ? 'justify-content-end' : 'justify-content-start'}">
                    <div class="p-2 rounded ${isMe ? 'bg-primary text-white' : 'bg-white border'}" style="max-width: 70%;">
                        ${m.content}
                        <div class="text-end" style="font-size: 0.7em; opacity: 0.7;">${m.created_at}</div>
                    </div>
                </div>
            `;
        }).join('');

        // Only scroll if we were at bottom? Or always?
        // chatArea.scrollTop = chatArea.scrollHeight;
    }
});
