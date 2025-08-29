// PetHealth Pro - Shared JavaScript Functions

// Global variables
let notificationTimeout = null;

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    initializeApp();
});

function initializeApp() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Initialize any other global components
    setupGlobalEventListeners();
    setupTTS();
}

function setupGlobalEventListeners() {
    // Handle form submissions with loading states
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function (e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                showLoadingState(submitBtn);
            }
        });
    });

    // Handle navigation active states
    updateActiveNavigation();
}

// ===============
// Murf TTS Client
// ===============
let ttsAudioElement = null;
let lastTtsBlobUrl = null;

function setupTTS() {
    // Create a single hidden audio element reused across pages
    ttsAudioElement = document.createElement('audio');
    ttsAudioElement.setAttribute('preload', 'auto');
    ttsAudioElement.style.display = 'none';
    document.body.appendChild(ttsAudioElement);
}

async function fetchMurfTts(text, opts = {}) {
    const body = {
        text: text,
        voice_id: opts.voiceId || 'en-US-natalie',
        format: opts.format || 'MP3'
    };
    const resp = await fetch('/api/tts_generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    const data = await resp.json();
    if (!data.success) throw new Error(data.error || 'TTS failed');
    const mime = data.mime || 'audio/mpeg';
    const bin = atob(data.audio_b64);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    const blob = new Blob([bytes], { type: mime });
    if (lastTtsBlobUrl) URL.revokeObjectURL(lastTtsBlobUrl);
    lastTtsBlobUrl = URL.createObjectURL(blob);
    return lastTtsBlobUrl;
}

async function speakText(text, options = {}) {
    try {
        if (!text || typeof text !== 'string') {
            console.warn('speakText called with invalid text:', text);
            return false;
        }
        const url = await fetchMurfTts(text, options);
        ttsAudioElement.src = url;
        // Try autoplay. If blocked, the caller should show a Listen button (we add it anyway).
        try { await ttsAudioElement.play(); } catch (e) { /* Autoplay likely blocked */ }
        return true;
    } catch (err) {
        console.error('TTS error:', err);
        showNotification('Unable to play voice. Use the Listen button.', 'warning');
        return false;
    }
}

function attachListenButton(container, getTextFn) {
    if (!container) return;
    // Remove any previous button
    const existing = container.querySelector('.tts-listen-btn');
    if (existing) existing.remove();

    const btn = document.createElement('button');
    btn.className = 'btn btn-outline-secondary btn-sm tts-listen-btn mt-2';
    btn.type = 'button';
    btn.innerHTML = '<span style="font-size:14px">🔊</span> Listen';
    btn.addEventListener('click', async () => {
        const text = getTextFn();
        if (text) await speakText(text);
    });
    container.appendChild(btn);
}

// Expose TTS helpers to global scope in case of scoping differences
window.speakText = speakText;
window.attachListenButton = attachListenButton;
window.wireExplicitListenButton = wireExplicitListenButton;

// Also expose a simple hook to show explicit buttons if present in templates
function wireExplicitListenButton(buttonId, getTextFn) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;
    btn.style.display = 'inline-block';
    btn.addEventListener('click', async () => {
        const text = getTextFn();
        if (text) await speakText(text);
    });
}

function updateActiveNavigation() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link[href]');

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// Notification System
function showNotification(message, type = 'info') {
    // Remove any existing notifications
    const existingNotifications = document.querySelectorAll('.custom-notification');
    existingNotifications.forEach(notif => notif.remove());

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `custom-notification alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 350px;
        max-width: 450px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        border: none;
        border-radius: 12px;
        backdrop-filter: blur(10px);
        animation: slideInRight 0.4s ease-out;
    `;

    const iconMap = {
        'error': 'exclamation-triangle',
        'success': 'check-circle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };

    const icon = iconMap[type] || 'info-circle';

    notification.innerHTML = `
        <div class="d-flex align-items-start">
            <i class="fas fa-${icon} me-3 mt-1" style="font-size: 1.2em;"></i>
            <div class="flex-grow-1">
                <div class="fw-semibold mb-1">${type === 'success' ? 'Success!' : type === 'error' ? 'Error!' : type === 'warning' ? 'Warning!' : 'Information'}</div>
                <div style="font-size: 0.95em; opacity: 0.9;">${message}</div>
            </div>
            <button type="button" class="btn-close ms-2" data-bs-dismiss="alert" style="font-size: 0.8em;"></button>
        </div>
    `;

    document.body.appendChild(notification);

    // Auto dismiss after 4 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.add('fade');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }
    }, 4000);
}

function createNotificationElement(message, type) {
    const typeConfig = {
        success: { icon: 'fas fa-check-circle', class: 'alert-success' },
        error: { icon: 'fas fa-exclamation-circle', class: 'alert-danger' },
        warning: { icon: 'fas fa-exclamation-triangle', class: 'alert-warning' },
        info: { icon: 'fas fa-info-circle', class: 'alert-info' }
    };

    const config = typeConfig[type] || typeConfig.info;

    const notification = document.createElement('div');
    notification.className = `alert ${config.class} app-notification position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        max-width: 500px;
        transform: translateX(100%);
        transition: transform 0.3s ease, opacity 0.3s ease;
        opacity: 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        border: none;
        border-radius: 8px;
    `;

    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="${config.icon} me-2"></i>
            <span class="flex-grow-1">${message}</span>
            <button type="button" class="btn-close ms-2" onclick="hideNotification(this.parentElement.parentElement)"></button>
        </div>
    `;

    return notification;
}

function hideNotification(notification) {
    if (notification && notification.parentElement) {
        notification.style.transform = 'translateX(100%)';
        notification.style.opacity = '0';

        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 300);
    }
}

// Loading States
function showLoadingState(element, originalText = null) {
    if (!element) return;

    if (!originalText) {
        originalText = element.innerHTML;
    }

    element.disabled = true;
    element.setAttribute('data-original-text', originalText);
    element.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" role="status">
            <span class="visually-hidden">Loading...</span>
        </span>
        Loading...
    `;
}


function hideLoadingState(element) {
    if (!element) return;

    const originalText = element.getAttribute('data-original-text');
    if (originalText) {
        element.innerHTML = originalText;
        element.removeAttribute('data-original-text');
    }
    element.disabled = false;
}

// Utility Functions
function formatDate(dateString, options = {}) {
    const date = new Date(dateString);
    const defaultOptions = {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    };

    return date.toLocaleDateString('en-US', { ...defaultOptions, ...options });
}

function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatDateTime(dateString) {
    return `${formatDate(dateString)} at ${formatTime(dateString)}`;
}

function truncateText(text, maxLength) {
    if (!text || text.length <= maxLength) {
        return text;
    }
    return text.substring(0, maxLength).trim() + '...';
}

function capitalizeFirstLetter(string) {
    if (!string) return '';
    return string.charAt(0).toUpperCase() + string.slice(1);
}

function sanitizeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// API Helper Functions
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        }
    };

    const config = { ...defaultOptions, ...options };

    try {
        const response = await fetch(url, config);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `HTTP error! status: ${response.status}`);
        }

        return data;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

async function uploadFile(url, formData, onProgress = null) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable && onProgress) {
                const percentComplete = (e.loaded / e.total) * 100;
                onProgress(percentComplete);
            }
        });

        xhr.addEventListener('load', () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    resolve(response);
                } catch (error) {
                    reject(new Error('Invalid JSON response'));
                }
            } else {
                reject(new Error(`HTTP error! status: ${xhr.status}`));
            }
        });

        xhr.addEventListener('error', () => {
            reject(new Error('Network error'));
        });

        xhr.open('POST', url);
        xhr.send(formData);
    });
}

// Validation Functions
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validatePhone(phone) {
    const phoneRegex = /^\+?[\d\s\-\(\)]+$/;
    return phoneRegex.test(phone) && phone.replace(/\D/g, '').length >= 10;
}

function validateRequired(value) {
    return value && value.toString().trim().length > 0;
}

function validateForm(formElement) {
    const errors = [];
    const requiredFields = formElement.querySelectorAll('[required]');

    requiredFields.forEach(field => {
        if (!validateRequired(field.value)) {
            errors.push(`${getFieldLabel(field)} is required`);
            field.classList.add('is-invalid');
        } else {
            field.classList.remove('is-invalid');
        }
    });

    // Email validation
    const emailFields = formElement.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        if (field.value && !validateEmail(field.value)) {
            errors.push(`${getFieldLabel(field)} must be a valid email address`);
            field.classList.add('is-invalid');
        }
    });

    return errors;
}

function getFieldLabel(field) {
    const label = field.closest('.form-group, .mb-3')?.querySelector('label');
    return label ? label.textContent.replace('*', '').trim() : field.name || 'Field';
}

// Storage Helpers
function saveToStorage(key, value, isSession = false) {
    const storage = isSession ? sessionStorage : localStorage;
    try {
        storage.setItem(key, JSON.stringify(value));
        return true;
    } catch (error) {
        console.error('Storage save failed:', error);
        return false;
    }
}

function loadFromStorage(key, defaultValue = null, isSession = false) {
    const storage = isSession ? sessionStorage : localStorage;
    try {
        const value = storage.getItem(key);
        return value ? JSON.parse(value) : defaultValue;
    } catch (error) {
        console.error('Storage load failed:', error);
        return defaultValue;
    }
}

function removeFromStorage(key, isSession = false) {
    const storage = isSession ? sessionStorage : localStorage;
    try {
        storage.removeItem(key);
        return true;
    } catch (error) {
        console.error('Storage remove failed:', error);
        return false;
    }
}

// Animation Helpers
function fadeIn(element, duration = 300) {
    element.style.opacity = '0';
    element.style.display = 'block';

    const start = performance.now();

    function animate(currentTime) {
        const elapsed = currentTime - start;
        const progress = Math.min(elapsed / duration, 1);

        element.style.opacity = progress.toString();

        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }

    requestAnimationFrame(animate);
}

function fadeOut(element, duration = 300) {
    const start = performance.now();
    const startOpacity = parseFloat(getComputedStyle(element).opacity);

    function animate(currentTime) {
        const elapsed = currentTime - start;
        const progress = Math.min(elapsed / duration, 1);

        element.style.opacity = (startOpacity * (1 - progress)).toString();

        if (progress < 1) {
            requestAnimationFrame(animate);
        } else {
            element.style.display = 'none';
        }
    }

    requestAnimationFrame(animate);
}

function slideDown(element, duration = 300) {
    element.style.display = 'block';
    element.style.height = '0';
    element.style.overflow = 'hidden';

    const fullHeight = element.scrollHeight;
    const start = performance.now();

    function animate(currentTime) {
        const elapsed = currentTime - start;
        const progress = Math.min(elapsed / duration, 1);

        element.style.height = (fullHeight * progress) + 'px';

        if (progress < 1) {
            requestAnimationFrame(animate);
        } else {
            element.style.height = '';
            element.style.overflow = '';
        }
    }

    requestAnimationFrame(animate);
}

// Device Detection
function isMobile() {
    return window.innerWidth <= 768;
}

function isTablet() {
    return window.innerWidth > 768 && window.innerWidth <= 1024;
}

function isDesktop() {
    return window.innerWidth > 1024;
}

// Scroll Utilities
function scrollToElement(element, offset = 0) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }

    if (element) {
        const elementPosition = element.getBoundingClientRect().top + window.pageYOffset;
        const offsetPosition = elementPosition - offset;

        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    }
}

function scrollToTop(smooth = true) {
    window.scrollTo({
        top: 0,
        behavior: smooth ? 'smooth' : 'auto'
    });
}

// URL Utilities
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

function updateUrlParameter(name, value) {
    const url = new URL(window.location);
    url.searchParams.set(name, value);
    window.history.replaceState({}, '', url);
}

function removeUrlParameter(name) {
    const url = new URL(window.location);
    url.searchParams.delete(name);
    window.history.replaceState({}, '', url);
}

// Pet Management Functions
async function addPet() {
    const form = document.getElementById('addPetForm');
    const formData = new FormData(form);

    const petData = {
        name: formData.get('petName') || document.getElementById('petName').value,
        species: formData.get('petSpecies') || document.getElementById('petSpecies').value,
        breed: formData.get('petBreed') || document.getElementById('petBreed').value,
        age: parseInt(formData.get('petAge') || document.getElementById('petAge').value),
        medical_notes: formData.get('petNotes') || document.getElementById('petNotes').value || ''
    };

    // Validate required fields
    if (!petData.name || !petData.species || !petData.breed || !petData.age) {
        showNotification('Please fill in all required fields', 'warning');
        return;
    }

    try {
        const response = await apiRequest('/api/add_pet', {
            method: 'POST',
            body: JSON.stringify(petData)
        });

        if (response.success) {
            // Close modal first
            const modal = bootstrap.Modal.getInstance(document.getElementById('addPetModal'));
            if (modal) {
                modal.hide();
            }

            // Reset form
            form.reset();

            // Show notification after modal is closed
            setTimeout(() => {
                showNotification('Pet added successfully!', 'success');
            }, 300);

            // Reload pets if function exists
            if (typeof loadPets === 'function') {
                loadPets('petsContainer');
            }
            if (typeof loadDashboardData === 'function') {
                loadDashboardData();
            }
        } else {
            showNotification('Error adding pet: ' + response.error, 'error');
        }
    } catch (error) {
        showNotification('Error adding pet: ' + error.message, 'error');
    }
}

// Dashboard Functions
async function loadDashboardData() {
    try {
        // Load pets count
        const petsResponse = await apiRequest('/api/get_pets');
        if (petsResponse.success) {
            const totalPetsElement = document.getElementById('totalPets');
            if (totalPetsElement) {
                totalPetsElement.textContent = petsResponse.pets.length;
            }
        }

        // Load reminders count
        const remindersResponse = await apiRequest('/api/get_reminders');
        if (remindersResponse.success) {
            const pendingReminders = remindersResponse.reminders.filter(r => !r.completed && new Date(r.due_date) >= new Date());
            const pendingElement = document.getElementById('pendingReminders');
            if (pendingElement) {
                pendingElement.textContent = pendingReminders.length;
            }
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Consultation Functions
async function startConsultation(petId = null) {
    // If no petId provided, try to get it from various sources
    if (!petId) {
        petId = document.getElementById('petSelect')?.value ||
            window.selectedPetId ||
            getUrlParameter('pet_id');
    }

    if (!petId) {
        showNotification('Please select a pet first', 'warning');
        return;
    }

    try {
        const response = await apiRequest('/api/start_consultation', {
            method: 'POST',
            body: JSON.stringify({ pet_id: petId })
        });

        if (response.success) {
            // Show consultation options - direct join or consultation page
            const roomId = "doctor-consultation-room";
            const consultationUrl = `https://meet.jit.si/${roomId}`;
            console.log('Consultation URL:', consultationUrl);

            // Show modal with options
            const modalHtml = `
                <div class="modal fade" id="consultationModal" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Start Consultation</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <p><strong>Consultation room created successfully!</strong></p>
                                <div class="alert alert-info">
                                    <i class="fas fa-info-circle me-2"></i>
                                    Share this link with your veterinarian to join the consultation:
                                </div>
                                <div class="input-group mb-3">
                                    <input type="text" class="form-control" value="${consultationUrl}" id="consultationLink" readonly>
                                    <button class="btn btn-outline-secondary" type="button" onclick="copyConsultationLink()">
                                        <i class="fas fa-copy"></i> Copy
                                    </button>
                                </div>
                                <div class="d-flex gap-2">
                                    <button class="btn btn-success flex-fill" onclick="joinConsultationDirect('${consultationUrl}')">
                                        <i class="fas fa-video me-1"></i>Join Now
                                    </button>
                                    <button class="btn btn-primary flex-fill" onclick="goToConsultationPage(${petId}, '${roomId}')">
                                        <i class="fas fa-desktop me-1"></i>Full Page View
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Remove existing modal if present
            const existingModal = document.getElementById('consultationModal');
            if (existingModal) {
                existingModal.remove();
            }

            // Add new modal to body
            document.body.insertAdjacentHTML('beforeend', modalHtml);

            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('consultationModal'));
            modal.show();
        } else {
            showNotification('Error starting consultation: ' + response.error, 'error');
        }
    } catch (error) {
        showNotification('Error starting consultation: ' + error.message, 'error');
    }
}

// Global helper function for consultation from modal
function startConsultationFromModal() {
    const petId = window.selectedPetId || getUrlParameter('pet_id');
    startConsultation(petId);
}

// Helper functions for consultation modal
function copyConsultationLink() {
    const linkInput = document.getElementById('consultationLink');
    linkInput.select();
    linkInput.setSelectionRange(0, 99999); // For mobile devices
    navigator.clipboard.writeText(linkInput.value).then(() => {
        showNotification('Consultation link copied to clipboard!', 'success');
    }).catch(() => {
        // Fallback for older browsers
        document.execCommand('copy');
        showNotification('Consultation link copied to clipboard!', 'success');
    });
}

function joinConsultationDirect(consultationUrl) {
    // Open Jitsi Meet in a new tab/window
    window.open(consultationUrl, '_blank', 'noopener,noreferrer');

    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('consultationModal'));
    if (modal) {
        modal.hide();
    }
}

function goToConsultationPage(petId, roomId) {
    // Redirect to consultation page with health history sidebar
    window.location.href = `/consultation/${petId}?room_id=${roomId}`;
}

// Export functions for use in other scripts
window.PetHealthPro = {
    showNotification,
    hideNotification,
    showLoadingState,
    hideLoadingState,
    formatDate,
    formatTime,
    formatDateTime,
    truncateText,
    capitalizeFirstLetter,
    sanitizeHtml,
    apiRequest,
    uploadFile,
    validateEmail,
    validatePhone,
    validateRequired,
    validateForm,
    saveToStorage,
    loadFromStorage,
    removeFromStorage,
    fadeIn,
    fadeOut,
    slideDown,
    isMobile,
    isTablet,
    isDesktop,
    scrollToElement,
    scrollToTop,
    getUrlParameter,
    updateUrlParameter,
    removeUrlParameter,
    addPet,
    loadDashboardData,
    startConsultation
};

// Make functions globally available
window.addPet = addPet;
window.loadDashboardData = loadDashboardData;
window.startConsultation = startConsultation;
window.startConsultationFromModal = startConsultationFromModal;
window.copyConsultationLink = copyConsultationLink;
window.joinConsultationDirect = joinConsultationDirect;
window.goToConsultationPage = goToConsultationPage;
window.showDiagnosisExplanation = showDiagnosisExplanation;
window.startConsultationFromExplanation = startConsultationFromExplanation;

// Dynamic Diagnosis Explanation System using Gemini AI
async function showDiagnosisExplanation(diagnosisName) {
    console.log('showDiagnosisExplanation called with:', diagnosisName);

    // Skip warning messages
    if (diagnosisName.toLowerCase().includes('warning') || diagnosisName.includes('⚠')) {
        showNotification('This is a warning message, not a medical diagnosis.', 'info');
        return;
    }

    // Clean diagnosis name - remove any HTML entities and extra characters
    const cleanedDiagnosisName = diagnosisName.replace(/&quot;/g, '"').replace(/&#39;/g, "'").trim();
    console.log('Cleaned diagnosis name:', cleanedDiagnosisName);

    // Create and show loading modal first
    const loadingModalHtml = `
        <div class="modal fade" id="diagnosisModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-info-circle text-primary me-2"></i>
                            ${cleanedDiagnosisName}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body text-center">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p class="mt-2 text-muted">Generating detailed explanation...</p>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if present
    const existingModal = document.getElementById('diagnosisModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add loading modal to body
    document.body.insertAdjacentHTML('beforeend', loadingModalHtml);

    // Show loading modal
    const loadingModal = new bootstrap.Modal(document.getElementById('diagnosisModal'));
    loadingModal.show();

    try {
        console.log('Sending request to API...');

        // Fetch explanation from Gemini API
        const response = await fetch('/api/get_diagnosis_explanation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                diagnosis: cleanedDiagnosisName
            })
        });

        console.log('Response status:', response.status);
        const data = await response.json();
        console.log('Response data:', data);

        if (data.success && data.explanation) {
            const explanation = data.explanation;
            console.log('Explanation received:', explanation);

            // Update modal content with the explanation
            const modalContent = `
                <div class="modal-header">
                    <h5 class="modal-title">
                        <i class="fas fa-info-circle text-primary me-2"></i>
                        ${cleanedDiagnosisName}
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-4">
                        <h6><i class="fas fa-book text-info me-2"></i>What it is</h6>
                        <p class="text-muted">${explanation.description || 'A medical condition that requires veterinary attention.'}</p>
                    </div>

                    <div class="mb-4">
                        <h6><i class="fas fa-list-ul text-warning me-2"></i>Possible Causes</h6>
                        <ul class="list-group list-group-flush">
                            ${(explanation.causes || ['Various factors may contribute to this condition']).map(cause => 
                                `<li class="list-group-item px-0 py-2">
                                    <i class="fas fa-angle-right text-muted me-2"></i>${cause}
                                </li>`
                            ).join('')}
                        </ul>
                    </div>

                    <div class="mb-4">
                        <h6><i class="fas fa-eye text-danger me-2"></i>What to Watch For</h6>
                        <ul class="list-group list-group-flush">
                            ${(explanation.symptoms || ['Monitor your pet closely and consult a veterinarian']).map(symptom => 
                                `<li class="list-group-item px-0 py-2">
                                    <i class="fas fa-exclamation-triangle text-warning me-2"></i>${symptom}
                                </li>`
                            ).join('')}
                        </ul>
                    </div>

                    <div class="alert alert-warning">
                        <h6 class="alert-heading">
                            <i class="fas fa- stethoscope me-2"></i>Important Reminder
                        </h6>
                        <p class="mb-0">
                            This information is for educational purposes only. Always consult with a qualified veterinarian 
                            for accurate diagnosis, treatment recommendations, and professional medical advice.
                        </p>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-success" onclick="startConsultationFromExplanation()">
                        <i class="fas fa-video me-1"></i>Schedule Consultation
                    </button>
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            `;

            document.querySelector('#diagnosisModal .modal-content').innerHTML = modalContent;
        } else {
            console.log('API response indicates failure, trying to get fallback explanation');

            // Try to get fallback explanation
            try {
                const fallbackResponse = await fetch('/api/get_diagnosis_explanation', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        diagnosis: cleanedDiagnosisName,
                        use_fallback: true
                    })
                });

                const fallbackData = await fallbackResponse.json();

                if (fallbackData.success && fallbackData.explanation) {
                    const explanation = fallbackData.explanation;

                    const modalContent = `
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-info-circle text-primary me-2"></i>
                                ${cleanedDiagnosisName}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-4">
                                <h6><i class="fas fa-book text-info me-2"></i>What it is</h6>
                                <p class="text-muted">${explanation.description || 'A medical condition that requires veterinary attention.'}</p>
                            </div>

                            <div class="mb-4">
                                <h6><i class="fas fa-list-ul text-warning me-2"></i>Possible Causes</h6>
                                <ul class="list-group list-group-flush">
                                    ${(explanation.causes || ['Various factors may contribute to this condition']).map(cause => 
                                        `<li class="list-group-item px-0 py-2">
                                            <i class="fas fa-angle-right text-muted me-2"></i>${cause}
                                        </li>`
                                    ).join('')}
                                </ul>
                            </div>

                            <div class="mb-4">
                                <h6><i class="fas fa-eye text-danger me-2"></i>What to Watch For</h6>
                                <ul class="list-group list-group-flush">
                                    ${(explanation.symptoms || ['Monitor your pet closely and consult a veterinarian']).map(symptom => 
                                        `<li class="list-group-item px-0 py-2">
                                            <i class="fas fa-exclamation-triangle text-warning me-2"></i>${symptom}
                                        </li>`
                                    ).join('')}
                                </ul>
                            </div>

                            <div class="alert alert-warning">
                                <h6 class="alert-heading">
                                    <i class="fas fa- stethoscope me-2"></i>Important Reminder
                                </h6>
                                <p class="mb-0">
                                    This information is for educational purposes only. Always consult with a qualified veterinarian 
                                    for accurate diagnosis, treatment recommendations, and professional medical advice.
                                </p>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-success" onclick="startConsultationFromExplanation()">
                                <i class="fas fa-video me-1"></i>Schedule Consultation
                            </button>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    `;

                    document.querySelector('#diagnosisModal .modal-content').innerHTML = modalContent;
                } else {
                    throw new Error('Fallback also failed');
                }
            } catch (fallbackError) {
                console.error('Fallback explanation also failed:', fallbackError);

                // Final fallback - basic error message
                const errorContent = `
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-info-circle text-primary me-2"></i>
                            ${cleanedDiagnosisName}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-info">
                            <h6 class="alert-heading">Information Currently Unavailable</h6>
                            <p class="mb-0">We're unable to provide detailed information about this diagnosis at the moment. Please consult with your veterinarian for more information.</p>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-success" onclick="startConsultationFromExplanation()">
                            <i class="fas fa-video me-1"></i>Schedule Consultation
                        </button>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                `;

                document.querySelector('#diagnosisModal .modal-content').innerHTML = errorContent;
            }
        }
    } catch (error) {
        console.error('Error fetching diagnosis explanation:', error);

        // Provide a fallback explanation modal
        const fallbackModalContent = `
            <div class="modal-header">
                <h5 class="modal-title">
                    <i class="fas fa-info-circle text-primary me-2"></i>
                    ${cleanedDiagnosisName}
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    We're unable to provide detailed information about this condition right now. 
                    Please consult with a qualified veterinarian for professional medical advice and treatment options.
                </div>
                <div class="mb-3">
                    <h6><i class="fas fa- stethoscope text-primary me-2"></i>General Recommendation</h6>
                    <p class="text-muted">
                        For any concerning symptoms or conditions, it's always best to schedule an appointment 
                        with your veterinarian for proper diagnosis and treatment.
                    </p>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            </div>
        `;

        // Remove existing modal if present
        const existingModal = document.getElementById('diagnosisModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Create and show fallback modal
        const modalHtml = `
            <div class="modal fade" id="diagnosisModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        ${fallbackModalContent}
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modal = new bootstrap.Modal(document.getElementById('diagnosisModal'));
        modal.show();
    }
}

function startConsultationFromExplanation() {
    // Close the diagnosis modal first
    const modal = bootstrap.Modal.getInstance(document.getElementById('diagnosisModal'));
    if (modal) {
        modal.hide();
    }

    // Start consultation
    const petId = document.getElementById('petSelect')?.value || window.selectedPetId;
    if (petId) {
        startConsultation(petId);
    } else {
        showNotification('Please select a pet to start consultation', 'warning');
    }
}

// Global error handler
window.addEventListener('error', function (event) {
    console.error('Global error:', event.error);
    showNotification('An unexpected error occurred. Please try again.', 'error');
});

// Global promise rejection handler
window.addEventListener('unhandledrejection', function (event) {
    console.error('Unhandled promise rejection:', event.reason);
    showNotification('An unexpected error occurred. Please try again.', 'error');
});