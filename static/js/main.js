const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const chatMessages = document.getElementById('chat-messages');
const sendBtn = document.getElementById('send-btn');

let sessionId = localStorage.getItem('session_id') || null;

const quickRepliesContainer = document.getElementById('quick-replies');

function appendMessage(role, content) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message');
    msgDiv.classList.add(role === 'user' ? 'user-message' : 'bot-message');
    
    // Convert newlines to breaks
    const formattedContent = content.replace(/\n/g, '<br>');
    msgDiv.innerHTML = `<div class="message-content">${formattedContent}</div>`;
    
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Clear quick replies when a new message is added (unless it's the bot providing them)
    if (role === 'user') {
        clearQuickReplies();
    }
}

function renderQuickReplies(buttons) {
    clearQuickReplies();
    if (!buttons || buttons.length === 0) return;
    
    buttons.forEach(buttonText => {
        const btn = document.createElement('button');
        btn.classList.add('quick-reply-btn');
        btn.textContent = buttonText;
        btn.onclick = () => handleButtonClick(buttonText);
        quickRepliesContainer.appendChild(btn);
    });
}

function clearQuickReplies() {
    quickRepliesContainer.innerHTML = '';
}

async function handleButtonClick(text) {
    appendMessage('user', text);
    clearQuickReplies();
    showTypingIndicator();
    await sendMessage(text);
}

async function sendMessage(message) {
    try {
        const response = await fetch('/chatbot/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message: message,
                session_id: sessionId 
            })
        });

        const data = await response.json();
        
        removeTypingIndicator();

        if (data.output) {
            appendMessage('bot', data.output);
            if (data.buttons) {
                renderQuickReplies(data.buttons);
            }
            if (data.session_id) {
                sessionId = data.session_id;
                localStorage.setItem('session_id', sessionId);
            }
        } else if (data.error) {
            appendMessage('bot', "I'm sorry, I encountered an error. Please try again later.");
            console.error(data.error);
        }
    } catch (error) {
        removeTypingIndicator();
        appendMessage('bot', "Connection error. Is the server running?");
        console.error(error);
    }
}

function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.classList.add('message', 'bot-message', 'typing-indicator');
    indicator.id = 'typing-indicator';
    indicator.innerHTML = '<div class="message-content">Laura is typing...</div>';
    chatMessages.appendChild(indicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.remove();
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;

    appendMessage('user', message);
    userInput.value = '';
    showTypingIndicator();
    await sendMessage(message);
});

// Initial Welcome Menu (Optional: if you want it to show on load)
window.onload = () => {
    // You could trigger a 'welcome' message here if needed
    renderQuickReplies([
        "Automate my business",
        "Improve Google ranking",
        "Build custom tool",
        "Request a call-back",
        "Get a quote"
    ]);
};
