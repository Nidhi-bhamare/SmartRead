/**
 * 📚 SmartRead - Main JavaScript
 * AI-Powered Book Reading Platform
 */

// ==========================================
// NAVBAR SCROLL EFFECT
// ==========================================

window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    }
});

// ==========================================
// HORIZONTAL SCROLL FOR BOOK ROWS
// ==========================================

function scrollBooks(button, direction) {
    const row = button.parentElement.querySelector('.book-slider');
    if (row) {
        const scrollAmount = 800;
        row.scrollBy({
            left: scrollAmount * direction,
            behavior: 'smooth'
        });
    }
}

// ==========================================
// AUTO-HIDE FLASH MESSAGES
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(flash => {
        setTimeout(() => {
            flash.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => flash.remove(), 300);
        }, 5000);
    });
});

// Add slideOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
`;
document.head.appendChild(style);

// ==========================================
// WORD MEANING POPUP (GLOBAL)
// ==========================================

let currentWordAudio = '';

function closeWordPopup() {
    const popup = document.getElementById('wordPopup');
    if (popup) {
        popup.classList.remove('active');
    }
}

function playWordAudio() {
    const audio = document.getElementById('wordAudio');
    if (currentWordAudio) {
        audio.src = currentWordAudio;
        audio.play();
    } else {
        // Use browser speech synthesis as fallback
        const word = document.getElementById('popupWord')?.textContent;
        if (word && 'speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(word);
            utterance.lang = 'en-US';
            speechSynthesis.speak(utterance);
        }
    }
}

// Close popup when clicking outside
document.addEventListener('click', (e) => {
    const popup = document.getElementById('wordPopup');
    if (popup && popup.classList.contains('active')) {
        if (!e.target.closest('.word-popup') && !e.target.classList.contains('word')) {
            closeWordPopup();
        }
    }
});

// Close popup with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeWordPopup();
    }
});

// ==========================================
// UTILITY FUNCTIONS
// ==========================================

/**
 * Format time in minutes:seconds
 */
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const container = document.querySelector('.flash-container') || createFlashContainer();
    
    const flash = document.createElement('div');
    flash.className = `flash flash-${type}`;
    flash.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">&times;</button>
    `;
    
    container.appendChild(flash);
    
    setTimeout(() => {
        flash.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => flash.remove(), 300);
    }, 4000);
}

function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-container';
    document.body.appendChild(container);
    return container;
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ==========================================
// LOADING STATES
// ==========================================

function showLoading(element) {
    if (element) {
        element.dataset.originalContent = element.innerHTML;
        element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        element.disabled = true;
    }
}

function hideLoading(element) {
    if (element && element.dataset.originalContent) {
        element.innerHTML = element.dataset.originalContent;
        element.disabled = false;
    }
}

// ==========================================
// API HELPERS
// ==========================================

async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showNotification('Something went wrong. Please try again.', 'error');
        throw error;
    }
}

// ==========================================
// INITIALIZE
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('📚 SmartRead initialized');
    
    // Add smooth scroll to all internal links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});
console.log("redeploy")
