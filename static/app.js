document.addEventListener('DOMContentLoaded', () => {
    const chatHistory = document.getElementById('chat-history');
    const chatInput = document.getElementById('chat-input');
    const statusIndicator = document.getElementById('status-indicator');
    const orb = document.getElementById('orb');

    const ws = new WebSocket(`ws://${location.host}/ws/chat`);

    let currentZedMessageDiv = null;

    function setStatus(status) {
        statusIndicator.className = 'status-indicator ' + status;
        orb.className = 'orb ' + status;
    }

    ws.onopen = () => {
        setStatus('idle');
        console.log("Connected to Zed websocket.");
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'chunk') {
            setStatus('typing');
            if (!currentZedMessageDiv) {
                currentZedMessageDiv = document.createElement('div');
                currentZedMessageDiv.className = 'message zed';
                chatHistory.appendChild(currentZedMessageDiv);
            }
            // Append text with a small space if it doesn't just start with space
            currentZedMessageDiv.textContent += (currentZedMessageDiv.textContent && data.text && !data.text.startsWith(' ') ? ' ' : '') + data.text;
            chatHistory.scrollTop = chatHistory.scrollHeight;
        } else if (data.type === 'done') {
            setStatus('idle');
            currentZedMessageDiv = null;
        } else if (data.type === 'error') {
            setStatus('idle');
            const errDiv = document.createElement('div');
            errDiv.className = 'message zed';
            errDiv.style.borderLeftColor = '#ef4444';
            errDiv.textContent = "[Error] " + data.text;
            chatHistory.appendChild(errDiv);
            currentZedMessageDiv = null;
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
    };

    ws.onclose = () => {
        console.log("Disconnected.");
    };

    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && chatInput.value.trim() !== '') {
            const text = chatInput.value.trim();
            
            // Render user message
            const msgDiv = document.createElement('div');
            msgDiv.className = 'message user';
            msgDiv.textContent = text;
            chatHistory.appendChild(msgDiv);
            chatHistory.scrollTop = chatHistory.scrollHeight;

            // Send via WS
            ws.send(text);
            chatInput.value = '';
            
            setStatus('thinking');
            currentZedMessageDiv = null;
        }
    });

    setStatus('idle');
});
