/**
 * College CMS - Main JavaScript Application
 * Handles UI interactions, form validations, and dynamic content
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    initializeSidebar();
    initializeFormHandlers();
    initializeTooltips();
    initializeModals();
    initializeCharts();
    initializeFormValidation();
    initializeSearchFilters();
    initializeWorkloadCalculators();
    
    // Add loading states
    addLoadingStates();
    
    // Initialize auto-hide alerts
    initializeAlerts();
    
    console.log('College CMS Application Initialized');
}

/**
 * Sidebar functionality
 */
function initializeSidebar() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                sidebar.classList.toggle('show');
            } else {
                sidebar.classList.toggle('collapsed');
                mainContent.classList.toggle('expanded');
            }
        });
    }
    
    // Set active sidebar link
    setActiveSidebarLink();
    
    // Handle responsive sidebar
    handleResponsiveSidebar();
}

/**
 * Set active sidebar link based on current page
 */
function setActiveSidebarLink() {
    const currentPath = window.location.pathname;
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    
    sidebarLinks.forEach(link => {
        link.classList.remove('active');
        
        const linkPath = new URL(link.href).pathname;
        if (currentPath === linkPath || (linkPath !== '/' && currentPath.startsWith(linkPath))) {
            link.classList.add('active');
        }
    });
}

/**
 * Handle responsive sidebar behavior
 */
function handleResponsiveSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    function handleResize() {
        if (window.innerWidth <= 768) {
            sidebar?.classList.remove('collapsed');
            mainContent?.classList.remove('expanded');
        }
    }
    
    window.addEventListener('resize', handleResize);
    handleResize(); // Initial call
}

/**
 * Initialize form handlers
 */
function initializeFormHandlers() {
    // Registration form role handling
    initializeRegistrationForm();
    
    // Assignment form handlers
    initializeAssignmentForm();
    
    // Excel import form handlers
    initializeExcelImportForm();
    
    // Timetable form handlers
    initializeTimetableForm();
    
    // Search form handlers
    initializeSearchForms();
}

/**
 * Registration form role-based field visibility
 */
function initializeRegistrationForm() {
    const roleSelect = document.getElementById('roleSelect');
    const facultyFields = document.getElementById('facultyFields');
    
    if (roleSelect && facultyFields) {
        function toggleFacultyFields() {
            if (roleSelect.value === 'faculty') {
                facultyFields.style.display = 'block';
                
                // Make faculty fields required
                const requiredFields = facultyFields.querySelectorAll('select[name="designation"]');
                requiredFields.forEach(field => {
                    field.setAttribute('required', 'required');
                });
            } else {
                facultyFields.style.display = 'none';
                
                // Remove required attribute from faculty fields
                const fields = facultyFields.querySelectorAll('input, select');
                fields.forEach(field => {
                    field.removeAttribute('required');
                    field.value = '';
                });
            }
        }
        
        roleSelect.addEventListener('change', toggleFacultyFields);
        toggleFacultyFields(); // Initial call
    }
}

/**
 * Assignment form handlers
 */
function initializeAssignmentForm() {
    const lectureHours = document.getElementById('lectureHours');
    const tutorialHours = document.getElementById('tutorialHours');
    const practicalHours = document.getElementById('practicalHours');
    const totalHours = document.getElementById('totalHours');
    const facultySelect = document.getElementById('facultySelect');
    
    if (lectureHours && tutorialHours && practicalHours && totalHours) {
        function updateTotalHours() {
            const lecture = parseInt(lectureHours.value) || 0;
            const tutorial = parseInt(tutorialHours.value) || 0;
            const practical = parseInt(practicalHours.value) || 0;
            const total = lecture + tutorial + practical;
            
            totalHours.textContent = total;
            
            // Update workload warning if faculty is selected
            if (facultySelect && facultySelect.value) {
                updateWorkloadWarning(total);
            }
        }
        
        [lectureHours, tutorialHours, practicalHours].forEach(input => {
            input.addEventListener('input', updateTotalHours);
        });
        
        if (facultySelect) {
            facultySelect.addEventListener('change', function() {
                updateFacultyWorkloadInfo();
                updateTotalHours();
            });
        }
        
        updateTotalHours(); // Initial calculation
    }
}

/**
 * Update faculty workload information
 */
function updateFacultyWorkloadInfo() {
    const facultySelect = document.getElementById('facultySelect');
    const workloadInfo = document.getElementById('facultyWorkloadInfo');
    
    if (!facultySelect || !workloadInfo) return;
    
    if (facultySelect.value) {
        // In a real implementation, this would fetch actual workload data
        workloadInfo.style.display = 'block';
    } else {
        workloadInfo.style.display = 'none';
    }
}

/**
 * Update workload warning
 */
function updateWorkloadWarning(additionalHours) {
    const warningDiv = document.getElementById('workloadWarning');
    if (!warningDiv) return;
    
    // This would be calculated based on actual faculty workload data
    // For now, just show/hide based on arbitrary threshold
    if (additionalHours > 20) {
        warningDiv.style.display = 'block';
    } else {
        warningDiv.style.display = 'none';
    }
}

/**
 * Excel import form handlers
 */
function initializeExcelImportForm() {
    const fileInput = document.querySelector('input[type="file"]');
    
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                validateExcelFile(file);
            }
        });
    }
}

/**
 * Validate Excel file
 */
function validateExcelFile(file) {
    const allowedTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
        'text/csv'
    ];
    
    const maxSize = 16 * 1024 * 1024; // 16MB
    
    if (!allowedTypes.includes(file.type)) {
        showAlert('Please select a valid Excel file (.xlsx, .xls, .csv)', 'warning');
        return false;
    }
    
    if (file.size > maxSize) {
        showAlert('File size must be less than 16MB', 'warning');
        return false;
    }
    
    return true;
}

/**
 * Timetable form handlers
 */
function initializeTimetableForm() {
    const startTime = document.getElementById('startTime');
    const endTime = document.getElementById('endTime');
    const facultySelect = document.getElementById('facultySelect');
    const daySelect = document.getElementById('daySelect');
    
    if (startTime && endTime) {
        function validateTimeRange() {
            if (startTime.value && endTime.value) {
                if (endTime.value <= startTime.value) {
                    endTime.setCustomValidity('End time must be after start time');
                } else {
                    endTime.setCustomValidity('');
                }
            }
        }
        
        startTime.addEventListener('change', validateTimeRange);
        endTime.addEventListener('change', validateTimeRange);
    }
    
    // Conflict checking (simplified version)
    if (facultySelect && daySelect && startTime && endTime) {
        function checkTimeConflicts() {
            // In a real implementation, this would make an AJAX call
            // to check for actual conflicts in the database
            const conflictAlert = document.getElementById('conflictAlert');
            if (conflictAlert) {
                // Simulate conflict checking
                if (Math.random() > 0.9) {
                    conflictAlert.style.display = 'block';
                } else {
                    conflictAlert.style.display = 'none';
                }
            }
        }
        
        [facultySelect, daySelect, startTime, endTime].forEach(element => {
            element.addEventListener('change', debounce(checkTimeConflicts, 500));
        });
    }
}

/**
 * Initialize search forms
 */
function initializeSearchForms() {
    const searchInputs = document.querySelectorAll('input[name="search"]');
    
    searchInputs.forEach(input => {
        // Auto-submit search after typing stops
        input.addEventListener('input', debounce(function() {
            if (input.value.length >= 3 || input.value.length === 0) {
                // Auto-submit the form
                const form = input.closest('form');
                if (form) {
                    form.submit();
                }
            }
        }, 500));
    });
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize modals
 */
function initializeModals() {
    // Auto-focus first input in modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            const firstInput = modal.querySelector('input, select, textarea');
            if (firstInput) {
                firstInput.focus();
            }
        });
    });
}

/**
 * Initialize charts for dashboard
 */
function initializeCharts() {
    // Set default Chart.js configurations
    if (typeof Chart !== 'undefined') {
        Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
        Chart.defaults.color = '#6c757d';
        Chart.defaults.backgroundColor = 'rgba(13, 110, 253, 0.1)';
        Chart.defaults.borderColor = 'rgba(13, 110, 253, 0.2)';
        
        // Add responsive behavior
        Chart.defaults.responsive = true;
        Chart.defaults.maintainAspectRatio = false;
    }
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Focus on first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
            
            form.classList.add('was-validated');
        });
    });
    
    // Real-time validation feedback
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.checkValidity()) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            }
        });
    });
}

/**
 * Initialize search filters with live updates
 */
function initializeSearchFilters() {
    const filterForms = document.querySelectorAll('form[method="GET"]');
    
    filterForms.forEach(form => {
        const selects = form.querySelectorAll('select');
        
        selects.forEach(select => {
            select.addEventListener('change', function() {
                // Auto-submit filter forms when select changes
                form.submit();
            });
        });
    });
}

/**
 * Initialize workload calculators
 */
function initializeWorkloadCalculators() {
    // Update workload progress bars
    updateWorkloadBars();
    
    // Initialize workload-related calculations
    const workloadItems = document.querySelectorAll('.workload-item');
    workloadItems.forEach(item => {
        const progressBar = item.querySelector('.progress-bar');
        if (progressBar) {
            animateProgressBar(progressBar);
        }
    });
}

/**
 * Update workload progress bars with animation
 */
function updateWorkloadBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    
    progressBars.forEach(bar => {
        animateProgressBar(bar);
    });
}

/**
 * Animate progress bar
 */
function animateProgressBar(progressBar) {
    const targetWidth = progressBar.style.width;
    progressBar.style.width = '0%';
    
    setTimeout(() => {
        progressBar.style.transition = 'width 1s ease-in-out';
        progressBar.style.width = targetWidth;
    }, 100);
}

/**
 * Add loading states to forms
 */
function addLoadingStates() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                
                // Add loading spinner
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Processing...
                `;
                
                // Reset after 10 seconds as fallback
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 10000);
            }
        });
    });
}

/**
 * Initialize alert auto-hide
 */
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(alert => {
        // Auto-hide success and info alerts after 5 seconds
        if (alert.classList.contains('alert-success') || alert.classList.contains('alert-info')) {
            setTimeout(() => {
                hideAlert(alert);
            }, 5000);
        }
    });
}

/**
 * Hide alert with animation
 */
function hideAlert(alert) {
    alert.style.opacity = '0';
    alert.style.transform = 'translateY(-20px)';
    
    setTimeout(() => {
        alert.remove();
    }, 300);
}

/**
 * Show custom alert
 */
function showAlert(message, type = 'info') {
    const alertContainer = document.querySelector('.flash-messages') || document.body;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        hideAlert(alert);
    }, 5000);
}

/**
 * Debounce function for search inputs
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

/**
 * Format numbers with proper separators
 */
function formatNumber(num) {
    return new Intl.NumberFormat().format(num);
}

/**
 * Smooth scroll to element
 */
function scrollToElement(element) {
    element.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('Copied to clipboard!', 'success');
    }).catch(() => {
        showAlert('Failed to copy to clipboard', 'warning');
    });
}

/**
 * Download data as CSV
 */
function downloadCSV(data, filename) {
    const csv = convertToCSV(data);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    
    window.URL.revokeObjectURL(url);
}

/**
 * Convert array of objects to CSV
 */
function convertToCSV(data) {
    if (!data || !data.length) return '';
    
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => `"${row[header] || ''}"`).join(','))
    ].join('\n');
    
    return csvContent;
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Validate phone number format
 */
function isValidPhone(phone) {
    const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
    return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
}

/**
 * Format date for display
 */
function formatDate(date, options = {}) {
    const defaultOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };
    
    return new Intl.DateTimeFormat('en-US', { ...defaultOptions, ...options }).format(new Date(date));
}

/**
 * Format time for display
 */
function formatTime(time) {
    return new Intl.DateTimeFormat('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    }).format(new Date(`2000-01-01T${time}`));
}

/**
 * Handle network errors gracefully
 */
function handleNetworkError(error) {
    console.error('Network Error:', error);
    showAlert('Network error occurred. Please check your connection and try again.', 'danger');
}

/**
 * Local storage helpers
 */
const Storage = {
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.error('Storage error:', e);
        }
    },
    
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('Storage error:', e);
            return defaultValue;
        }
    },
    
    remove(key) {
        try {
            localStorage.removeItem(key);
        } catch (e) {
            console.error('Storage error:', e);
        }
    }
};

/**
 * Theme management
 */
const Theme = {
    init() {
        const savedTheme = Storage.get('theme', 'light');
        this.apply(savedTheme);
    },
    
    apply(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        Storage.set('theme', theme);
    },
    
    toggle() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        this.apply(newTheme);
    }
};

// Initialize theme on load
Theme.init();

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    // Don't show user errors for script errors in production
    if (window.location.hostname !== 'localhost') {
        showAlert('An unexpected error occurred. Please refresh the page.', 'danger');
    }
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    handleNetworkError(e.reason);
});

// Export functions for global use
window.CollegeCMS = {
    showAlert,
    hideAlert,
    copyToClipboard,
    downloadCSV,
    formatDate,
    formatTime,
    formatNumber,
    isValidEmail,
    isValidPhone,
    Storage,
    Theme
};

console.log('College CMS JavaScript loaded successfully');
