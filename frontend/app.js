let currentSessionId = null; // Managed by the backend

document.addEventListener('DOMContentLoaded', () => {
    // Clock
    setInterval(() => {
        const now = new Date();
        document.getElementById('clock').textContent = now.toISOString().split('T')[1].split('.')[0] + ' UTC';
    }, 1000);

    const chatForm = document.getElementById('chatForm');
    const input = document.getElementById('userInput');
    const chatLog = document.getElementById('chatLog');
    const mapDisplay = document.getElementById('mapDisplay');

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;

        // Add user message
        appendMessage('user', 'OPERATOR', text);
        input.value = '';

        // Add loading state
        const loadId = appendMessage('system', 'SYSTEM', 'PROCESSING UPLINK...');

        // Live API call to the LangChain FastAPI backend
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, session_id: currentSessionId })
            });
            const data = await response.json();
            
            // Persist session_id for conversational memory
            if (data.session_id) {
                currentSessionId = data.session_id;
            }
            
            document.getElementById(loadId).remove();

            if (data.error) {
                appendMessage('system', 'ERROR', data.error);
                return;
            }

            // Display Agent's textual reply
            appendMessage('agent', 'GEMINI-2.5-PRO', data.reply);

            // Attempt to find an image in the tool_results to display
            let foundImage = false;
            let hazardType = "UNKNOWN";
            
            if (data.tool_results && data.tool_results.length > 0) {
                for (const step of data.tool_results) {
                    const resultData = step.result;
                    // If the tool returned a string that looks like an image URL
                    if (typeof resultData === 'string' && (resultData.startsWith('http') && (resultData.endsWith('.png') || resultData.endsWith('.gif') || resultData.endsWith('.jpg')))) {
                        foundImage = resultData;
                        hazardType = step.tool.toUpperCase();
                        break;
                    }
                    // If the tool returned a JSON with a url or map_url field
                    else if (typeof resultData === 'object' && resultData !== null) {
                        let potentialUrl = resultData.map_url || resultData.url;
                        if (potentialUrl) {
                            // Extract URL if it's markdown ![alt](url)
                            const markdownMatch = potentialUrl.match(/!\[.*?\]\((.*?)\)/);
                            if (markdownMatch) {
                                foundImage = markdownMatch[1];
                            } else {
                                foundImage = potentialUrl;
                            }
                            hazardType = step.tool.toUpperCase();
                            break;
                        }
                    }
                }
            }

            if (foundImage) {
                mapDisplay.innerHTML = `<img src="${foundImage}" alt="AEMET Data Map" class="map-image">`;
                document.getElementById('telemetryMeta').innerHTML = `
                    <div class="meta-row"><span>HAZARD_TYPE:</span> <span class="data-value warning">${hazardType}</span></div>
                    <div class="meta-row"><span>STATUS:</span> <span class="data-value" style="color:var(--accent-success)">LIVE_UPLINK</span></div>
                `;
            } else {
                mapDisplay.innerHTML = `<div class="empty-state"><div class="radar-sweep"></div><p>NO VISUAL TELEMETRY RETURNED</p></div>`;
            }

        } catch (err) {
            document.getElementById(loadId).remove();
            appendMessage('system', 'ERROR', 'Failed to connect to LangChain backend.');
        }
    });

    function appendMessage(role, header, text) {
        const div = document.createElement('div');
        div.className = `message ${role}`;
        const id = 'msg-' + Date.now();
        div.id = id;
        
        div.innerHTML = `
            <div class="msg-header">${header}</div>
            <div class="msg-body">${text}</div>
        `;
        
        chatLog.appendChild(div);
        chatLog.scrollTop = chatLog.scrollHeight;
        return id;
    }
});
