// NurCoran — Premium Interactions

// Initialize Lucide icons
document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) lucide.createIcons();
});

// Mobile menu toggle
function toggleMobileMenu() {
  const menu = document.getElementById('mobile-menu');
  const hamburger = document.getElementById('hamburger');
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

// Tasbih pulse animation
function triggerTasbihPulse(btn) {
  btn.classList.remove('tasbih-pulse');
  void btn.offsetWidth; // force reflow
  btn.classList.add('tasbih-pulse');
}

