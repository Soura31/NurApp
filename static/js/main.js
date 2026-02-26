(function () {
  const ready = (fn) => {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  };

  function toast(message, type = 'info') {
    const c = document.getElementById('toast-container');
    if (!c) return;
    const cls = {
      success: 'bg-[#1a6b4a]',
      error: 'bg-red-600',
      warning: 'bg-yellow-600 text-black',
      info: 'bg-[#161b22] border border-[#c9a84c]/30'
    };
    const el = document.createElement('div');
    el.className = `toast px-4 py-3 rounded-xl text-white shadow-2xl ${cls[type] || cls.info}`;
    el.textContent = message;
    c.appendChild(el);
    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transform = 'translateX(120%)';
      setTimeout(() => el.remove(), 250);
    }, 4200);
  }

  function initCounters() {
    document.querySelectorAll('[data-counter]').forEach((el) => {
      const target = parseInt(el.dataset.counter || '0', 10);
      let n = 0;
      const step = Math.max(1, Math.floor(target / 70));
      const t = setInterval(() => {
        n += step;
        if (n >= target) {
          el.textContent = target.toLocaleString('fr-FR');
          clearInterval(t);
        } else {
          el.textContent = n.toLocaleString('fr-FR');
        }
      }, 20);
    });
  }

  function initStars() {
    const canvas = document.getElementById('stars-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const stars = [];

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    for (let i = 0; i < 140; i += 1) {
      stars.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        r: Math.random() * 1.8,
        a: Math.random(),
        d: (Math.random() * 0.02) + 0.004,
      });
    }

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      stars.forEach((s) => {
        s.a += s.d;
        if (s.a > 1 || s.a < 0.2) s.d *= -1;
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(240,192,96,${s.a})`;
        ctx.fill();
      });
      requestAnimationFrame(draw);
    };
    draw();
  }

  function initPrayerCountdown() {
    const cards = [...document.querySelectorAll('.prayer-card')];
    if (!cards.length) return;

    const toSeconds = (hhmm) => {
      if (!hhmm || hhmm.indexOf(':') === -1) return null;
      const [h, m] = hhmm.split(':').map((v) => parseInt(v, 10));
      if (Number.isNaN(h) || Number.isNaN(m)) return null;
      return (h * 3600) + (m * 60);
    };

    const nameEl = document.getElementById('next-prayer-name');
    const timeEl = document.getElementById('next-prayer-time');
    const countdownEl = document.getElementById('countdown');

    const tick = () => {
      const now = new Date();
      const nowSec = now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds();
      let next = null;
      cards.forEach((c) => {
        const t = toSeconds(c.dataset.time || '');
        if (t === null) return;
        if (t >= nowSec && (!next || t < next.time)) next = { el: c, time: t, name: c.dataset.name, clock: c.dataset.time };
      });
      if (!next) {
        const first = cards[0];
        const t = toSeconds(first?.dataset.time || '00:00') || 0;
        next = { el: first, time: t + 86400, name: first?.dataset.name || 'Fajr', clock: first?.dataset.time || '00:00' };
      }
      cards.forEach((c) => c.classList.remove('ring-2', 'ring-[#c9a84c]'));
      next.el?.classList.add('ring-2', 'ring-[#c9a84c]');
      if (nameEl) nameEl.textContent = next.name;
      if (timeEl) timeEl.textContent = next.clock;
      const remain = next.time - nowSec;
      const h = Math.floor(remain / 3600).toString().padStart(2, '0');
      const m = Math.floor((remain % 3600) / 60).toString().padStart(2, '0');
      const s = Math.floor(remain % 60).toString().padStart(2, '0');
      if (countdownEl) countdownEl.textContent = `${h}:${m}:${s}`;
    };
    tick();
    setInterval(tick, 1000);
  }

  window.tasbihApp = function tasbihApp() {
    return {
      presets: [
        { text: 'SubhanAllah', arabic: 'سُبْحَانَ ٱللَّٰهِ', target: 33 },
        { text: 'Alhamdulillah', arabic: 'ٱلْحَمْدُ لِلَّٰهِ', target: 33 },
        { text: 'AllahuAkbar', arabic: 'اللَّهُ أَكْبَر', target: 33 },
      ],
      selectedText: 'SubhanAllah',
      selectedArabic: 'سُبْحَانَ ٱللَّٰهِ',
      count: 0,
      target: 33,
      get dashArray() { return 2 * Math.PI * 102; },
      get dashOffset() {
        const progress = Math.min(1, this.count / Math.max(1, this.target));
        return this.dashArray * (1 - progress);
      },
      selectPreset(p) {
        this.selectedText = p.text;
        this.selectedArabic = p.arabic;
        this.target = p.target;
        this.count = 0;
      },
      increment() { this.count += 1; },
      reset() { this.count = 0; },
    };
  };

  ready(() => {
    const loader = document.getElementById('page-loader');
    if (loader) {
      setTimeout(() => {
        loader.style.opacity = '0';
        setTimeout(() => loader.remove(), 350);
      }, 280);
    }

    document.querySelectorAll('#django-messages span').forEach((el) => {
      const level = (el.dataset.level || 'info').split(' ')[0];
      toast(el.textContent.trim(), level);
    });

    initCounters();
    initStars();
    initPrayerCountdown();

    // Polling simple pour notifications
    setInterval(() => {
      if (!document.body.dataset.authenticated) return;
    }, 30000);
  });
})();
