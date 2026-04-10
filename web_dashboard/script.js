document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const statusCard = document.getElementById('main-status-card');
    const statusText = document.getElementById('status-text');
    const statusSubtext = document.getElementById('status-subtext');
    const globalDot = document.getElementById('global-status-dot');
    
    const angleValue = document.getElementById('angle-value');
    const velocityValue = document.getElementById('velocity-value');
    const confidenceValue = document.getElementById('confidence-value');
    const confidenceBar = document.getElementById('confidence-bar');
    const eventLog = document.getElementById('event-log');
    
    const feedStatus = document.getElementById('feed-status');
    const videoStream = document.getElementById('video-stream');
    const noFeedMsg = document.getElementById('no-feed-msg');
    
    const btnRealtime = document.getElementById('btn-realtime');
    const btnVideo = document.getElementById('btn-video');
    const btnStop = document.getElementById('btn-stop');
    const toastMsg = document.getElementById('toast-message');
    const dbLogsBody = document.getElementById('db-logs-body');

    let activeStream = false;
    let currentState = 'NORMAL';

    // 1. Control APIs to Python Backend
    async function sendCommand(mode) {
        toastMsg.innerText = "Processing...";
        try {
            const res = await fetch('/api/control', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: mode })
            });
            const data = await res.json();
            toastMsg.innerText = data.message;
            toastMsg.style.color = data.success ? "var(--color-normal)" : "var(--color-danger)";
            
            if (data.success && mode !== 'stop') {
                // Attach video stream src directly to the IMG tag MJPEG endpoint
                videoStream.src = `/video_feed?t=${new Date().getTime()}`;
                videoStream.style.display = 'block';
                noFeedMsg.style.display = 'none';
                feedStatus.innerText = "Active";
                feedStatus.style.color = "var(--color-normal)";
                activeStream = true;
                logEvent(`Started AI Feed: ${mode}`);
            } else if (mode === 'stop') {
                videoStream.src = "";
                videoStream.style.display = 'none';
                noFeedMsg.style.display = 'block';
                feedStatus.innerText = "Inactive";
                feedStatus.style.color = "var(--color-warning)";
                activeStream = false;
                logEvent("Stopped AI Feed");
                changeState('NORMAL');
                updateMetrics(0, 0, 0);
            }
        } catch (e) {
            toastMsg.innerText = "Error connecting to backend API. Is app.py running?";
            toastMsg.style.color = "var(--color-danger)";
        }
    }

    btnRealtime.addEventListener('click', () => sendCommand('realtime'));
    btnVideo.addEventListener('click', () => sendCommand('video'));
    btnStop.addEventListener('click', () => sendCommand('stop'));

    // 2. Fetch Live Telemetry from Python Backend
    async function pollStatus() {
        if (!activeStream) return;
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            
            updateMetrics(data.angle, data.velocity, data.confidence);
            
            if (data.status !== currentState) {
                changeState(data.status);
                logEvent(`State changed: ${data.status}`);
                currentState = data.status;
            }
        } catch (e) {}
    }

    // 3. Fetch SQLite DB Logs from Python Backend
    async function pollLogs() {
        try {
            const res = await fetch('/api/logs');
            const logs = await res.json();
            
            dbLogsBody.innerHTML = "";
            logs.forEach(log => {
                const tr = document.createElement('tr');
                const timeStr = new Date(log.timestamp * 1000).toLocaleTimeString();
                
                // Colorizing the Status column based on danger
                let statusColor = log.event_type === 'FALLEN' ? 'var(--color-danger)' : 
                                  log.event_type === 'ABOUT_TO_FALL' ? 'var(--color-warning)' : 'var(--text-secondary)';
                
                tr.innerHTML = `
                    <td>#${log.id}</td>
                    <td>${timeStr}</td>
                    <td style="color: ${statusColor}; font-weight: bold;">${log.event_type}</td>
                    <td>${log.angle.toFixed(1)}°</td>
                    <td>${(log.confidence*100).toFixed(0)}%</td>
                `;
                dbLogsBody.appendChild(tr);
            });
        } catch (e) {}
    }

    // Start Polling Loops
    setInterval(pollStatus, 200); // 200ms polls for live AI metric updates
    setInterval(pollLogs, 2500);  // 2.5sec polls checking the database for new recorded falls

    function updateMetrics(angle, velocity, conf) {
        angleValue.innerText = `${angle.toFixed(1)}°`;
        velocityValue.innerText = `${velocity.toFixed(3)} m/s`;
        confidenceValue.innerText = `${conf.toFixed(0)}%`;
        confidenceBar.style.width = `${Math.min(100, conf)}%`;
    }

    // Dynamic Theming wrapper
    function changeState(state) {
        statusCard.className = 'panel status-card';
        globalDot.className = 'pulse-dot';
        
        if (state === 'NORMAL' || state === 'STUMBLE' || state === 'FLOOR_ACTIVITY') {
            statusCard.classList.add('normal-state');
            statusText.innerText = state;
            statusSubtext.innerText = 'Safe conditions detected.';
            confidenceBar.style.background = 'var(--color-normal)';
            globalDot.classList.add('normal');
        } 
        else if (state === 'ABOUT_TO_FALL') {
            statusCard.classList.add('warning-state');
            statusText.innerText = 'WARNING / FALLING';
            statusSubtext.innerText = 'Metrics indicate rapid dropping.';
            confidenceBar.style.background = 'var(--color-warning)';
            globalDot.classList.add('warning'); 
            globalDot.style.background = 'var(--color-warning)';
        }
        else if (state === 'FALLEN') {
            statusCard.classList.add('danger-state');
            statusText.innerText = 'FALL DETECTED';
            statusSubtext.innerText = 'CRITICAL: Alert conditions met.';
            confidenceBar.style.background = 'var(--color-danger)';
            globalDot.classList.add('danger');
        }
    }

    function logEvent(message) {
        const li = document.createElement('li');
        const timeString = new Date().toLocaleTimeString();
        li.innerHTML = `<span class="time">${timeString}</span> ${message}`;
        eventLog.prepend(li);
        if(eventLog.children.length > 50) eventLog.removeChild(eventLog.lastChild);
    }
});
