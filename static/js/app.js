/**
 * LATECME Application JavaScript
 * Global configuration for HTMX and Alpine.js
 */

// =============================================================================
// HTMX Configuration
// =============================================================================

// Configure HTMX to include CSRF token in all requests
document.addEventListener('DOMContentLoaded', function() {
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

    // Add CSRF token to all HTMX requests
    document.body.addEventListener('htmx:configRequest', function(event) {
        event.detail.headers['X-CSRFToken'] = csrftoken;
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

// Register Alpine.js global stores when Alpine is ready
document.addEventListener('alpine:init', () => {
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
});

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

// =============================================================================
// Icon Helper
// =============================================================================

// Function to use Tabler icons from sprite
function icon(name, size = 24, strokeWidth = 2) {
    return `<svg class="icon icon-tabler" width="${size}" height="${size}" viewBox="0 0 24 24" stroke-width="${strokeWidth}" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <use href="/static/icons/tabler-sprite.svg#tabler-${name}"></use>
    </svg>`;
}
