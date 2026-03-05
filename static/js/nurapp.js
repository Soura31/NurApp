// NurCoran — Premium Interactions

// Initialize Lucide icons
document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) lucide.createIcons();
});

// Mobile menu toggle
function toggleMobileMenu() {
  const menu = document.getElementById('mobile-menu');
  const hamburger = document.getElementById('hamburger');
  if (!menu) return;
  menu?.classList.toggle('open');
  hamburger?.classList.toggle('active');
  document.body.style.overflow = menu?.classList.contains('open') ? 'hidden' : '';
}

// Navbar scroll effect
window.addEventListener('scroll', () => {
  const nav = document.getElementById('main-nav');
  if (nav) nav.classList.toggle('scrolled', window.scrollY > 30);
});

// Scroll fade-in animations
const fadeObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      fadeObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.fade-up').forEach(el => fadeObserver.observe(el));
});

window.addEventListener('resize', () => {
  const menu = document.getElementById('mobile-menu');
  if (!menu || window.innerWidth >= 1024) {
    document.body.style.overflow = '';
    menu?.classList.remove('open');
    document.getElementById('hamburger')?.classList.remove('active');
  }
});

// Tasbih pulse animation
function triggerTasbihPulse(btn) {
  btn.classList.remove('tasbih-pulse');
  void btn.offsetWidth; // force reflow
  btn.classList.add('tasbih-pulse');
}

function applyTheme(theme) {
  const html = document.documentElement;
  const body = document.body;
  const isLight = theme === 'light';
  html.setAttribute('data-theme', theme);
  html.style.colorScheme = isLight ? 'light' : 'dark';
  if (body) {
    body.classList.toggle('theme-light', isLight);
    body.classList.toggle('theme-dark', !isLight);
  }

  const desktopIcon = document.getElementById('theme-toggle-icon');
  const mobileIcon = document.getElementById('theme-toggle-mobile-icon');
  const mobileText = document.getElementById('theme-toggle-mobile-text');
  const desktopBtn = document.getElementById('theme-toggle');

  if (desktopIcon) desktopIcon.className = isLight ? 'fa-solid fa-moon' : 'fa-solid fa-sun';
  if (mobileIcon) mobileIcon.className = isLight ? 'fa-solid fa-moon' : 'fa-solid fa-sun';
  if (mobileText) mobileText.textContent = isLight ? 'Mode nuit' : 'Mode jour';
  if (desktopBtn) desktopBtn.setAttribute('aria-label', isLight ? 'Activer le mode nuit' : 'Activer le mode jour');
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'light' ? 'dark' : 'light';
  applyTheme(next);
  try {
    localStorage.setItem('nur-theme', next);
  } catch (e) {}
}

window.toggleTheme = toggleTheme;

document.addEventListener('DOMContentLoaded', () => {
  const saved = (() => {
    try {
      return localStorage.getItem('nur-theme');
    } catch (e) {
      return null;
    }
  })();
  applyTheme(saved || document.documentElement.getAttribute('data-theme') || 'dark');
});

