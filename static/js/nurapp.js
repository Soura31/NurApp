// NurCoran — Premium Interactions

// Initialize Lucide icons
document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) lucide.createIcons();
});

// Mobile menu toggle
function toggleMobileMenu(forceClose = false) {
  const menu = document.getElementById('mobile-menu');
  const backdrop = document.getElementById('mobile-menu-backdrop');
  const hamburger = document.getElementById('hamburger');
  if (!menu) return;
  const shouldOpen = forceClose ? false : !menu.classList.contains('open');
  menu.classList.toggle('open', shouldOpen);
  menu.setAttribute('aria-hidden', shouldOpen ? 'false' : 'true');
  backdrop?.classList.toggle('open', shouldOpen);
  hamburger?.classList.toggle('active', shouldOpen);
  hamburger?.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');
  document.body.style.overflow = shouldOpen ? 'hidden' : '';
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
  const backdrop = document.getElementById('mobile-menu-backdrop');
  if (!menu || window.innerWidth >= 1024) {
    document.body.style.overflow = '';
    menu?.classList.remove('open');
    menu?.setAttribute('aria-hidden', 'true');
    backdrop?.classList.remove('open');
    document.getElementById('hamburger')?.classList.remove('active');
    document.getElementById('hamburger')?.setAttribute('aria-expanded', 'false');
  }
});

// Tasbih pulse animation
function triggerTasbihPulse(btn) {
  btn.classList.remove('tasbih-pulse');
  void btn.offsetWidth; // force reflow
  btn.classList.add('tasbih-pulse');
}

function getPreferredThemeMode() {
  try {
    return localStorage.getItem('nur-theme-mode') || 'night';
  } catch (e) {
    return 'night';
  }
}

function resolveTheme(mode) {
  if (mode === 'auto') {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'day' : 'night';
  }
  return mode;
}

function syncThemeSelectors(mode) {
  ['theme-selector', 'theme-selector-mobile'].forEach((id) => {
    const select = document.getElementById(id);
    if (select) select.value = mode;
  });
}

function applyTheme(mode) {
  const html = document.documentElement;
  const body = document.body;
  const resolved = resolveTheme(mode);
  const isLightLike = resolved !== 'night';
  html.setAttribute('data-theme', resolved);
  html.style.colorScheme = isLightLike ? 'light' : 'dark';
  if (body) {
    body.classList.remove('theme-dark', 'theme-light', 'theme-day', 'theme-parchment');
    body.classList.add(
      resolved === 'night'
        ? 'theme-dark'
        : resolved === 'parchment'
          ? 'theme-parchment'
          : 'theme-day'
    );
  }

  const desktopIcon = document.getElementById('theme-toggle-icon');
  const mobileIcon = document.getElementById('theme-toggle-mobile-icon');
  const mobileText = document.getElementById('theme-toggle-mobile-text');
  if (desktopIcon) desktopIcon.className = mode === 'auto' ? 'fa-solid fa-wand-magic-sparkles' : 'fa-solid fa-circle-half-stroke';
  if (mobileIcon) mobileIcon.className = mode === 'auto' ? 'fa-solid fa-wand-magic-sparkles' : 'fa-solid fa-circle-half-stroke';
  if (mobileText) {
    mobileText.textContent =
      mode === 'auto'
        ? 'Le theme suit votre appareil.'
        : resolved === 'parchment'
          ? 'Lecture chaude type parchemin.'
          : resolved === 'day'
            ? 'Interface claire pour la journee.'
            : 'Interface sombre pour la lecture nocturne.';
  }
  syncThemeSelectors(mode);
}

function setThemeMode(mode) {
  applyTheme(mode);
  try {
    localStorage.setItem('nur-theme-mode', mode);
  } catch (e) {}
}

function toggleTheme() {
  const modes = ['night', 'day', 'parchment', 'auto'];
  const current = getPreferredThemeMode();
  const next = modes[(modes.indexOf(current) + 1) % modes.length];
  setThemeMode(next);
}

window.toggleTheme = toggleTheme;
window.setThemeMode = setThemeMode;

document.addEventListener('DOMContentLoaded', () => {
  applyTheme(getPreferredThemeMode());
  ['theme-selector', 'theme-selector-mobile'].forEach((id) => {
    document.getElementById(id)?.addEventListener('change', (event) => {
      setThemeMode(event.target.value);
    });
  });
  window.matchMedia?.('(prefers-color-scheme: light)')?.addEventListener('change', () => {
    if (getPreferredThemeMode() === 'auto') applyTheme('auto');
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') toggleMobileMenu(true);
  });
});

