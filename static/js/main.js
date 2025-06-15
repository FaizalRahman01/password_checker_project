document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const scanBtn = document.getElementById('scan-btn');
    const stopBtn = document.getElementById('stop-btn') || document.createElement('button');
    const wantSecureCheckbox = document.getElementById('want_secure');
    const lengthOptions = document.getElementById('length-options');
    const passLengthSlider = document.getElementById('pass_length');
    const lengthValue = document.getElementById('length-value');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const terminalOutput = document.getElementById('terminal-output');
    const passwordSuggestions = document.getElementById('password-suggestions');
    const passwordsGrid = document.getElementById('passwords-grid');
    const statusValue = document.getElementById('status-value');

    // State Management
    let isScanning = false;
    let progressInterval;
    let currentScanId = null;

    // Initialize UI
    initUI();

    // Event Listeners
    function initEventListeners() {
        wantSecureCheckbox.addEventListener('change', toggleLengthOptions);
        passLengthSlider.addEventListener('input', updateLengthDisplay);
        scanBtn.addEventListener('click', handleScan);
        stopBtn.addEventListener('click', handleStopScan);
        
        // Add keyboard support
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !isScanning) {
                handleScan();
            }
        });
    }

    // UI Initialization
    function initUI() {
        // Set up full screen behavior
        document.documentElement.style.overflow = 'hidden';
        document.body.style.overflow = 'hidden';
        document.body.style.margin = '0';
        document.body.style.padding = '0';

        // Initialize elements
        toggleLengthOptions();
        updateLengthDisplay();
        initEventListeners();
        
        // Welcome message
        addOutputLine("SYSTEM INITIALIZED", "#0ff");
        addOutputLine("Enter credentials to begin security audit", "#aaa");
        addOutputLine("----------------------------------------", "#555");
    }

    function toggleLengthOptions() {
        lengthOptions.style.display = wantSecureCheckbox.checked ? 'block' : 'none';
    }

    function updateLengthDisplay() {
        lengthValue.textContent = passLengthSlider.value;
    }

    // Main Scan Handler
    async function handleScan() {
        const email = emailInput.value.trim();
        const password = passwordInput.value.trim();
        const wantSecure = wantSecureCheckbox.checked;
        const passLength = parseInt(passLengthSlider.value);

        if (!validateInputs(email, password)) return;

        try {
            isScanning = true;
            updateUIState();
            resetScanUI();
            
            currentScanId = Date.now(); // Unique ID for each scan
            const scanId = currentScanId;
            
            // Start real progress monitoring
            await startRealScan(email, password, wantSecure, passLength, scanId);
            
        } catch (error) {
            handleError(error);
        } finally {
            if (currentScanId === scanId) { // Only update if this is still the current scan
                isScanning = false;
                updateUIState();
            }
        }
    }

    function validateInputs(email, password) {
        if (!email) {
            addOutputLine("ERROR: Email is required", "red");
            emailInput.focus();
            return false;
        }

        if (!email.includes('@')) {
            addOutputLine("ERROR: Invalid email format", "red");
            emailInput.focus();
            return false;
        }

        if (!password) {
            addOutputLine("WARNING: No password provided - checking reversed email pattern", "orange");
        }

        return true;
    }

    function resetScanUI() {
        terminalOutput.innerHTML = '';
        passwordSuggestions.style.display = 'none';
        passwordsGrid.innerHTML = '';
        progressFill.style.width = '0%';
        progressText.textContent = '0% COMPLETE';
        statusValue.textContent = 'INITIALIZING';
        statusValue.style.color = '#ff0';
        
        addOutputLine("Starting security scan...", "#0ff");
        addOutputLine(`Target: ${emailInput.value.trim()}`, "#aaa");
    }

    function updateUIState() {
        scanBtn.disabled = isScanning;
        scanBtn.textContent = isScanning ? 'SCANNING...' : 'START SCAN';
        stopBtn.disabled = !isScanning;
        emailInput.readOnly = isScanning;
        passwordInput.readOnly = isScanning;
        wantSecureCheckbox.disabled = isScanning;
    }

    // Real Scan Implementation
    async function startRealScan(email, password, wantSecure, passLength, scanId) {
        try {
            // Start the scan
            const response = await fetch('/start_check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: email,
                    password: password || null,
                    check_without_password: !password,
                    generate_passwords: wantSecure,
                    pass_length: passLength
                })
            });

            if (!response.ok) {
                throw new Error(await response.text() || 'Server error');
            }

            addOutputLine("Scan initiated successfully", "#0f0");
            
            // Start progress polling
            await pollProgress(scanId);

        } catch (error) {
            throw error;
        }
    }

    async function pollProgress(scanId) {
        let lastProgress = 0;
        
        while (isScanning && currentScanId === scanId) {
            try {
                const response = await fetch('/progress');
                if (!response.ok) throw new Error('Progress check failed');
                
                const data = await response.json();
                
                // Update progress
                progressFill.style.width = `${data.progress}%`;
                progressText.textContent = data.status || `${data.progress}% COMPLETE`;
                
                // Update status
                statusValue.textContent = data.running ? "SCANNING" : "COMPLETE";
                statusValue.style.color = data.running ? "#ff0" : "#0f0";
                
                // Add new output if progress changed
                if (data.progress > lastProgress) {
                    if (data.current_password) {
                        addOutputLine(`Checking: ${data.current_password}`, "#aaa");
                    }
                    lastProgress = data.progress;
                }
                
                // Check if scan is complete
                if (!data.running) {
                    handleScanComplete(data);
                    break;
                }
                
                // Wait before next poll
                await new Promise(resolve => setTimeout(resolve, 500));
                
            } catch (error) {
                addOutputLine(`Progress error: ${error.message}`, "red");
                throw error;
            }
        }
    }

    function handleScanComplete(data) {
        if (data.found_password) {
            addOutputLine("WARNING: PASSWORD COMPROMISED", "red");
            addOutputLine(`Found in database: ${data.found_password}`, "red");
            addOutputLine("SECURITY ALERT: Change this password immediately!", "red");
        } else {
            addOutputLine("PASSWORD NOT FOUND IN DATABASE", "#0f0");
            addOutputLine("This password appears secure in our checks", "#0f0");
        }
        
        if (data.generated_passwords?.length) {
            addOutputLine("GENERATED SECURE PASSWORDS:", "#0ff");
            displayGeneratedPasswords(data.generated_passwords);
        }
    }

    function handleStopScan() {
        if (!isScanning) return;
        
        addOutputLine("Stopping scan...", "orange");
        
        fetch('/stop_check', { method: 'POST' })
            .then(() => {
                addOutputLine("Scan stopped by user", "orange");
                isScanning = false;
                currentScanId = null;
                updateUIState();
            })
            .catch(error => {
                addOutputLine(`Error stopping scan: ${error.message}`, "red");
            });
    }

    function displayGeneratedPasswords(passwords) {
        passwordSuggestions.style.display = 'block';
        passwordsGrid.innerHTML = '';
        
        passwords.forEach(password => {
            const passwordEl = document.createElement('div');
            passwordEl.textContent = password;
            passwordEl.title = "Click to copy";
            
            passwordEl.addEventListener('click', () => {
                navigator.clipboard.writeText(password)
                    .then(() => {
                        passwordEl.classList.add('copied');
                        setTimeout(() => passwordEl.classList.remove('copied'), 1000);
                        addOutputLine(`Copied: ${password}`, "#0ff");
                    })
                    .catch(err => {
                        addOutputLine(`Copy failed: ${err}`, "red");
                    });
            });
            
            passwordsGrid.appendChild(passwordEl);
        });
    }

    function addOutputLine(text, color = "#0f0") {
        const line = document.createElement('div');
        line.className = 'output-line';
        
        // Add timestamp
        const now = new Date();
        const timestamp = now.toLocaleTimeString();
        const timeSpan = document.createElement('span');
        timeSpan.textContent = `[${timestamp}] `;
        timeSpan.style.color = '#555';
        
        // Add message
        const messageSpan = document.createElement('span');
        messageSpan.textContent = text;
        messageSpan.style.color = color;
        
        line.appendChild(timeSpan);
        line.appendChild(messageSpan);
        terminalOutput.appendChild(line);
        
        // Auto-scroll
        terminalOutput.scrollTop = terminalOutput.scrollHeight;
    }

    function handleError(error) {
        addOutputLine(`ERROR: ${error.message}`, "red");
        statusValue.textContent = 'ERROR';
        statusValue.style.color = '#f00';
    }
});