(function() {
    const CONFIG = {
        serverUrl: '/chatbot',
        title: 'Laura | Flexi Boost',
        primaryColor: '#2563eb'
    };

    const style = document.createElement('style');
    style.innerHTML = `
        #fb-widget-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 999999;
            font-family: 'Inter', sans-serif;
        }
        #fb-chat-button {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: ${CONFIG.primaryColor};
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        #fb-chat-button:hover {
            transform: scale(1.1);
        }
        #fb-chat-button svg {
            color: white;
            width: 30px;
            height: 30px;
        }
        #fb-chat-window {
            position: absolute;
            bottom: 80px;
            right: 0;
            width: 450px;
            height: 650px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 12px 24px rgba(0,0,0,0.15);
            overflow: hidden;
            display: none;
            flex-direction: column;
            transform-origin: bottom right;
            transition: all 0.3s ease;
            opacity: 0;
            transform: scale(0.9);
        }
        #fb-chat-window.open {
            display: flex;
            opacity: 1;
            transform: scale(1);
        }
        #fb-chat-iframe {
            width: 100%;
            height: 100%;
            border: none;
        }
    `;
    document.head.appendChild(style);

    const container = document.createElement('div');
    container.id = 'fb-widget-container';
    container.innerHTML = `
        <div id="fb-chat-window">
            <iframe id="fb-chat-iframe" src="${CONFIG.serverUrl}"></iframe>
        </div>
        <div id="fb-chat-button">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
        </div>
    `;
    document.body.appendChild(container);

    const button = document.getElementById('fb-chat-button');
    const windowEl = document.getElementById('fb-chat-window');
    let isOpen = false;

    button.onclick = () => {
        isOpen = !isOpen;
        if (isOpen) {
            windowEl.style.display = 'flex';
            setTimeout(() => windowEl.classList.add('open'), 10);
            button.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            `;
        } else {
            windowEl.classList.remove('open');
            setTimeout(() => windowEl.style.display = 'none', 300);
            button.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
            `;
        }
    };
})();
