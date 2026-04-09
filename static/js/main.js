// MultiStore Global JavaScript

// ------------------- DARK MODE TOGGLE -------------------
(function() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        // Check for saved theme in localStorage
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'light') {
            document.body.classList.add('light-mode');
            darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        } else {
            darkModeToggle.innerHTML = '<i class="fas fa-moon"></i>';
        }
        
        darkModeToggle.addEventListener('click', function() {
            document.body.classList.toggle('light-mode');
            const isLight = document.body.classList.contains('light-mode');
            localStorage.setItem('theme', isLight ? 'light' : 'dark');
            darkModeToggle.innerHTML = isLight ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
        });
    }
})();

// ------------------- COPY LINK FUNCTION (Global) -------------------
function copyPageUrl() {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
        // Use language-aware alert if available
        const lang = document.documentElement.lang || 'en';
        const message = (lang === 'sw') ? 'Kiungo kimenakiliwa!' : 'Link copied to clipboard!';
        alert(message);
    }).catch(() => {
        const lang = document.documentElement.lang || 'en';
        const message = (lang === 'sw') ? 'Imeshindwa kunakili kiungo.' : 'Failed to copy link.';
        alert(message);
    });
}

// Automatically add a floating copy button (if not already in base.html)
// This is a fallback; the button is already in base.html, but we keep the function global.
document.addEventListener('DOMContentLoaded', function() {
    // Ensure a copy button exists; if not, create one (optional)
    if (!document.getElementById('copyLinkBtn')) {
        const copyBtn = document.createElement('button');
        copyBtn.id = 'copyLinkBtn';
        copyBtn.innerHTML = '<i class="fas fa-link"></i>';
        copyBtn.className = 'btn btn-outline-light btn-sm rounded-circle position-fixed';
        copyBtn.style.bottom = '20px';
        copyBtn.style.left = '20px';
        copyBtn.style.zIndex = '1000';
        copyBtn.style.width = '45px';
        copyBtn.style.height = '45px';
        copyBtn.style.borderRadius = '50%';
        copyBtn.style.backgroundColor = 'var(--accent)';
        copyBtn.style.border = 'none';
        copyBtn.style.color = '#fff';
        copyBtn.onclick = copyPageUrl;
        document.body.appendChild(copyBtn);
    } else {
        // If button already exists, attach event
        const existingBtn = document.getElementById('copyLinkBtn');
        if (existingBtn) existingBtn.onclick = copyPageUrl;
    }
});

// ------------------- BOOTSTRAP NAVBAR AUTO COLLAPSE -------------------
// Close navbar when a nav-link is clicked (mobile-friendly)
document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    if (navbarCollapse) {
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth < 992) {
                    const bsCollapse = new bootstrap.Collapse(navbarCollapse, {
                        toggle: false
                    });
                    bsCollapse.hide();
                }
            });
        });
    }
});

// ------------------- TOOLTIP INITIALIZATION (Optional) -------------------
// Initialize Bootstrap tooltips if any
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
