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
    
    const trackingBox = document.getElementById('tracking-box');
    const boxLabel = document.getElementById('box-label');
    const eventLog = document.getElementById('event-log');

    // State Variables for Simulation
    let angle = 80;
    let confidence = 0;
    let velocity = 0;
    let currentState = 'NORMAL'; 
    let simulationTime = 0;

    // Simulation Loop (runs every 100ms)
    setInterval(() => {
        simulationTime++;
        
        // --- 1. Simulate Pose Dynamics ---
        
        // Every 150 ticks (~15 sec), simulate a fall event
        const cycle = simulationTime % 200;
        
        if (cycle > 50 && cycle < 120) {
            // FALLING SCENARIO
            if (angle > 15) angle -= 3; // drops to horizontal
            velocity = (Math.random() * 0.05 + 0.02).toFixed(2);
            
            // Confidence builds over time while fallen (my new logic!)
            if (angle < 45) {
                confidence += 4;
            }
        } 
        else if (cycle >= 120 && cycle < 130) {
            // RECOVERY SCENARIO
            angle += 8;
            velocity = (Math.random() * 0.02).toFixed(2);
            confidence -= 10;
        } 
        else {
            // NORMAL STANDING SCENARIO
            angle = Math.min(90, angle + Math.random() * 2);
            velocity = (Math.random() * 0.01).toFixed(2);
            confidence = Math.max(0, confidence - 5);
        }

        // Clamp values
        confidence = Math.min(100, Math.max(0, confidence));
        if (confidence > 100) confidence = 100;
        
        // --- 2. Determine State based on thresholds ---
        let newState = 'NORMAL';
        if (confidence > 70 && angle < 45) {
            newState = 'FALLEN';
        } else if (confidence > 30) {
            newState = 'ABOUT_TO_FALL';
        }

        // --- 3. Update the UI DOM ---
        angleValue.innerText = `${Math.floor(angle)}°`;
        velocityValue.innerText = `${velocity} m/s`;
        confidenceValue.innerText = `${Math.floor(confidence)}%`;
        confidenceBar.style.width = `${confidence}%`;

        // Physical Tracking Box Simulation (it drops when fallen)
        const boxTop = angle < 45 ? '80%' : '50%';
        const boxHeight = angle < 45 ? '120px' : '250px';
        const boxWidth = angle < 45 ? '250px' : '120px';
        trackingBox.style.top = boxTop;
        trackingBox.style.height = boxHeight;
        trackingBox.style.width = boxWidth;

        // Apply State Transitions
        if (newState !== currentState) {
            changeState(newState);
            logEvent(`State transitioned from ${currentState} to ${newState}`);
            currentState = newState;
        }

    }, 100);

    // Helper functions for UI manipulation
    function changeState(state) {
        // Reset classes
        statusCard.className = 'panel status-card';
        globalDot.className = 'pulse-dot';
        
        if (state === 'NORMAL') {
            statusCard.classList.add('normal-state');
            statusText.innerText = 'NORMAL';
            statusSubtext.innerText = 'No anomalies detected.';
            confidenceBar.style.background = 'var(--color-normal)';
            trackingBox.style.borderColor = 'var(--color-normal)';
            boxLabel.style.background = 'var(--color-normal)';
            boxLabel.innerText = 'ID: 1 - NORMAL';
            globalDot.classList.add('normal');
        } 
        else if (state === 'ABOUT_TO_FALL') {
            statusCard.classList.add('warning-state');
            statusText.innerText = 'WARNING';
            statusSubtext.innerText = 'Person may be falling... tracking.';
            confidenceBar.style.background = 'var(--color-warning)';
            trackingBox.style.borderColor = 'var(--color-warning)';
            boxLabel.style.background = 'var(--color-warning)';
            boxLabel.innerText = 'ID: 1 - ABOUT_TO_FALL';
            globalDot.classList.add('warning'); // generic static yellow could be added
            globalDot.style.background = 'var(--color-warning)';
        }
        else if (state === 'FALLEN') {
            statusCard.classList.add('danger-state');
            statusText.innerText = 'FALL DETECTED';
            statusSubtext.innerText = 'CRITICAL: Sending alerts immediately.';
            confidenceBar.style.background = 'var(--color-danger)';
            trackingBox.style.borderColor = 'var(--color-danger)';
            boxLabel.style.background = 'var(--color-danger)';
            boxLabel.innerText = 'ID: 1 - FALLEN!';
            globalDot.classList.add('danger');
            
            // Pop an alert the first time
            setTimeout(() => {
                logEvent("CRITICAL ALERT DISPATCHED TO SMS & EMAIL");
            }, 500);
        }
    }

    function logEvent(message) {
        const li = document.createElement('li');
        const now = new Date();
        const timeString = now.toTimeString().split(' ')[0];
        li.innerHTML = `<span class="time">${timeString}</span> ${message}`;
        eventLog.prepend(li);
        
        // keep log small
        if(eventLog.children.length > 25) {
            eventLog.removeChild(eventLog.lastChild);
        }
    }
});
