/**
 * LATECME Application JavaScript
 * Global configuration for HTMX and Alpine.js
 */

// =============================================================================
// Dependency Checker
// =============================================================================

/**
 * Check if critical JavaScript libraries are loaded
 * Reports missing dependencies to user
 */
function checkDependencies() {
    const missing = [];

    if (typeof htmx === 'undefined') {
        missing.push('HTMX');
    }
    if (typeof Alpine === 'undefined') {
        missing.push('Alpine.js');
    }

    if (missing.length > 0) {
        console.error('Missing dependencies:', missing.join(', '));
        // Create a visible banner
        const banner = document.createElement('div');
        banner.style.cssText = 'position:fixed;top:0;left:0;right:0;background:#d63939;color:white;padding:12px;text-align:center;z-index:9999;font-family:system-ui;';
        banner.innerHTML = `⚠️ Erro ao carregar recursos: ${missing.join(', ')}. <a href="#" onclick="location.reload()" style="color:white;text-decoration:underline;font-weight:bold;">Clique aqui para recarregar</a>`;
        document.body.prepend(banner);
    }
}

// Run dependency check after DOM loads
document.addEventListener('DOMContentLoaded', checkDependencies);

// =============================================================================
// HTMX Configuration
// =============================================================================

// Configure HTMX to include CSRF token in all requests
document.addEventListener('DOMContentLoaded', function() {
    // Check if HTMX is available
    if (typeof htmx === 'undefined') {
        console.error('HTMX not loaded! Dynamic features will not work.');
        // Note: checkDependencies() will show user-visible banner
        return;
    }

    // Get CSRF token from cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    // Warn if CSRF token is missing on page load
    if (!csrftoken) {
        console.warn('CSRF token not found in cookies. POST/PUT/DELETE requests will fail.');
    }

    // Add CSRF token to all HTMX requests
    document.body.addEventListener('htmx:configRequest', function(event) {
        // Only set header if token exists
        if (csrftoken) {
            event.detail.headers['X-CSRFToken'] = csrftoken;
        } else {
            // For non-safe methods, show user feedback
            const method = event.detail.verb.toUpperCase();
            if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
                console.error(`Cannot perform ${method} request: CSRF token missing`);
                // Show toast notification if Alpine is available
                if (window.Alpine && Alpine.store('toasts')) {
                    Alpine.store('toasts').error('Sessão expirada. Por favor, recarregue a página.');
                }
            }
        }
    });

    // Handle HTMX errors
    document.body.addEventListener('htmx:responseError', function(event) {
        console.error('HTMX Error:', event.detail);
        // You could show a toast notification here
    });

    // Add loading class to body during HTMX requests
    document.body.addEventListener('htmx:beforeRequest', function(event) {
        const indicator = event.detail.elt.querySelector('.htmx-indicator');
        if (indicator) {
            indicator.style.display = 'inline-block';
        }
    });

    document.body.addEventListener('htmx:afterRequest', function(event) {
        const indicator = event.detail.elt.querySelector('.htmx-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    });

    // Handle HTMX redirect responses (for Django login required)
    document.body.addEventListener('htmx:beforeSwap', function(event) {
        // Check if response is a redirect to login page
        if (event.detail.xhr.status === 403 || event.detail.xhr.status === 401) {
            window.location.href = '/accounts/login/';
        }
    });
});

// =============================================================================
// Alpine.js Global Data and Utilities
// =============================================================================

// Flag to prevent duplicate initialization
let alpineStoresInitialized = false;

// Register Alpine.js global stores when Alpine is ready
// Use both alpine:init and a fallback check
function initAlpineStores() {
    // Check if Alpine is available
    if (typeof Alpine === 'undefined' || typeof Alpine.store === 'undefined') {
        console.warn('Alpine.js not available, skipping stores initialization');
        return;
    }

    // Prevent duplicate initialization
    if (alpineStoresInitialized) {
        return;
    }
    alpineStoresInitialized = true;
    // Toast notification store
    Alpine.store('toasts', {
        items: [],

        add(message, type = 'info', duration = 5000) {
            const id = Date.now();
            this.items.push({ id, message, type });

            if (duration > 0) {
                setTimeout(() => this.remove(id), duration);
            }
        },

        remove(id) {
            this.items = this.items.filter(item => item.id !== id);
        },

        success(message) {
            this.add(message, 'success');
        },

        error(message) {
            this.add(message, 'danger');
        },

        warning(message) {
            this.add(message, 'warning');
        },

        info(message) {
            this.add(message, 'info');
        }
    });

    // Sidebar state store
    Alpine.store('sidebar', {
        open: false,

        toggle() {
            this.open = !this.open;
        },

        close() {
            this.open = false;
        }
    });

    // Global modal helper
    Alpine.data('modal', (initialOpen = false) => ({
        open: initialOpen,

        show() {
            this.open = true;
            document.body.classList.add('modal-open');
        },

        hide() {
            this.open = false;
            document.body.classList.remove('modal-open');
        },

        toggle() {
            this.open ? this.hide() : this.show();
        }
    }));

    // Dropdown helper
    Alpine.data('dropdown', () => ({
        open: false,

        toggle() {
            this.open = !this.open;
        },

        close() {
            this.open = false;
        }
    }));

    // Confirm dialog helper
    Alpine.data('confirmDialog', () => ({
        open: false,
        title: '',
        message: '',
        confirmText: 'Confirmar',
        cancelText: 'Cancelar',
        onConfirm: null,

        show(options = {}) {
            this.title = options.title || 'Confirmar';
            this.message = options.message || 'Tem certeza?';
            this.confirmText = options.confirmText || 'Confirmar';
            this.cancelText = options.cancelText || 'Cancelar';
            this.onConfirm = options.onConfirm || null;
            this.open = true;
        },

        confirm() {
            if (typeof this.onConfirm === 'function') {
                this.onConfirm();
            }
            this.open = false;
        },

        cancel() {
            this.open = false;
        }
    }));
}

// Primary initialization: Use alpine:init event (fires before Alpine starts)
document.addEventListener('alpine:init', function() {
    console.log('Alpine.js initializing, registering stores...');
    initAlpineStores();
});

// Fallback 1: If Alpine loads before our script
if (typeof Alpine !== 'undefined') {
    console.log('Alpine.js already loaded, initializing stores immediately');
    initAlpineStores();
}

// Fallback 2: Poll for Alpine availability (max 5 seconds)
let alpineCheckAttempts = 0;
const alpineCheckInterval = setInterval(function() {
    alpineCheckAttempts++;
    if (typeof Alpine !== 'undefined' && typeof Alpine.store !== 'undefined') {
        initAlpineStores();
        clearInterval(alpineCheckInterval);
    } else if (alpineCheckAttempts >= 50) {  // 50 * 100ms = 5 seconds
        console.error('Alpine.js failed to load after 5 seconds');
        clearInterval(alpineCheckInterval);
    }
}, 100);

// =============================================================================
// Utility Functions
// =============================================================================

// Format currency (Brazilian Real)
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Format date (Brazilian format)
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('pt-BR').format(date);
}

// Format datetime (Brazilian format)
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('pt-BR', {
        dateStyle: 'short',
        timeStyle: 'short'
    }).format(date);
}

// Debounce function for search inputs
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

// =============================================================================
// HTMX Extensions
// =============================================================================

// Custom HTMX extension for handling Django messages
// Wait for HTMX to be available before defining extension
if (typeof htmx !== 'undefined') {
    htmx.defineExtension('django-messages', {
        onEvent: function(name, evt) {
            if (name === 'htmx:afterSwap') {
                // Look for messages in the response
                const messagesContainer = evt.detail.elt.querySelector('[data-messages]');
                if (messagesContainer && window.Alpine) {
                    const messages = JSON.parse(messagesContainer.dataset.messages || '[]');
                    messages.forEach(msg => {
                        Alpine.store('toasts').add(msg.message, msg.tags);
                    });
                }
            }
        }
    });
} else {
    console.warn('HTMX not available, skipping django-messages extension');
}

// =============================================================================
// Icon Helper
// =============================================================================

// Function to use Tabler icons from sprite
function icon(name, size = 24, strokeWidth = 2) {
    return `<svg class="icon icon-tabler" width="${size}" height="${size}" viewBox="0 0 24 24" stroke-width="${strokeWidth}" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <use href="/static/icons/tabler-sprite.svg#tabler-${name}"></use>
    </svg>`;
}
