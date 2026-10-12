document.addEventListener('DOMContentLoaded', () => {
  const menuToggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('.main-nav');
  const year = document.getElementById('year');
  const contactForm = document.getElementById('contactForm');
  const brandOwner = document.querySelector('.brand-click-owner');

  initHeroCollage();

  if (brandOwner) {
    let ownerClicks = 0;
    let ownerClickTimer = null;

    brandOwner.addEventListener('click', (event) => {
      event.preventDefault();
      ownerClicks += 1;

      if (ownerClickTimer) {
        clearTimeout(ownerClickTimer);
      }

      ownerClickTimer = setTimeout(() => {
        if (ownerClicks >= 4) {
          window.location.href = '/owner/login/';
        } else {
          window.location.href = brandOwner.getAttribute('href');
        }
        ownerClicks = 0;
      }, 500);
    });
  }

  if (year) {
    year.textContent = new Date().getFullYear();
  }

  if (menuToggle && nav) {
    menuToggle.addEventListener('click', () => {
      const isOpen = nav.classList.toggle('is-open');
      menuToggle.setAttribute('aria-expanded', String(isOpen));
    });

    nav.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => {
        nav.classList.remove('is-open');
        menuToggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  if (contactForm) {
    const submitButton = contactForm.querySelector('.btn-submit');
    const allInputs = contactForm.querySelectorAll('input, textarea');

    contactForm.addEventListener('submit', (event) => {
      let valid = true;

      allInputs.forEach((input) => {
        if ((input.required && !input.value.trim()) || (input.type === 'email' && input.value.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value.trim()))) {
          valid = false;
        }
      });

      if (!valid) {
        event.preventDefault();
        contactForm.reportValidity();
        return;
      }

      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = 'Enviando...';
      }
    });
  }
});

function initHeroCollage() {
  const collage = document.getElementById('hero-collage');
  if (!collage) return;

  const rotatingCards = Array.from(collage.querySelectorAll('.collage-card[data-index]'));
  if (rotatingCards.length === 0) return;

  // Deriva autónoma + cuerda naranja enlazada: cada tarjeta flota por sí sola
  // (posición/tamaño/rotación) y un hilo SVG recorre sus centros. El brillo
  // sigue al cursor solo con puntero fino. Sin movimiento reducido no hay
  // deriva ni cuerda (collage estático, CSS ya lo congela).
  setupCollageMotion(collage, rotatingCards);

  function setupCollageMotion(collageEl, cards) {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const ropeSvg = document.getElementById('collage-rope');
    if (reduced) {
      if (ropeSvg) ropeSvg.style.display = 'none';
      return;
    }

    setupCollageGlare(cards);

    const line = document.getElementById('collage-rope-line');
    const glow = document.getElementById('collage-rope-glow');
    const knotsG = document.getElementById('collage-rope-knots');
    const ropeOn = Boolean(ropeSvg && line && glow && knotsG && cards.length >= 2);
    if (!ropeOn && ropeSvg) ropeSvg.style.display = 'none';

    const SVG_NS = 'http://www.w3.org/2000/svg';
    const knots = ropeOn ? cards.map(() => {
      const circle = document.createElementNS(SVG_NS, 'circle');
      circle.setAttribute('class', 'rope-knot');
      circle.setAttribute('r', '4.5');
      knotsG.appendChild(circle);
      return circle;
    }) : [];

    // Deriva propia por tarjeta: fase/velocidad/amplitud distintas.
    // En móvil la amplitud se reduce para no saturar pantallas pequeñas.
    const smallScreen = window.matchMedia('(max-width: 767px)').matches;
    const ampScale = smallScreen ? 0.55 : 1;
    const drift = cards.map((_, i) => ({
      phase: i * 1.7,
      speed: 0.5 + (i % 3) * 0.12,
      ampX: (9 + (i % 2) * 4) * ampScale,
      ampY: (8 + ((i + 1) % 2) * 4) * ampScale,
    }));
    const offsets = cards.map(() => ({ x: 0, y: 0 }));

    let raf = null;
    let running = false;
    let t0 = 0;

    // Curva cerrada suave (Catmull-Rom a Bézier) por los centros.
    function smoothClosedPath(pts) {
      const n = pts.length;
      if (n < 3) return '';
      let d = `M ${pts[0].x.toFixed(1)},${pts[0].y.toFixed(1)}`;
      for (let i = 0; i < n; i++) {
        const p0 = pts[(i - 1 + n) % n];
        const p1 = pts[i];
        const p2 = pts[(i + 1) % n];
        const p3 = pts[(i + 2) % n];
        const c1x = p1.x + (p2.x - p0.x) / 6;
        const c1y = p1.y + (p2.y - p0.y) / 6;
        const c2x = p2.x - (p3.x - p1.x) / 6;
        const c2y = p2.y - (p3.y - p1.y) / 6;
        d += ` C ${c1x.toFixed(1)},${c1y.toFixed(1)} ${c2x.toFixed(1)},${c2y.toFixed(1)}`
          + ` ${p2.x.toFixed(1)},${p2.y.toFixed(1)}`;
      }
      return d + ' Z';
    }

    function drawRope() {
      if (!ropeOn) return;
      const pts = cards.map((card, i) => ({
        x: card.offsetLeft + card.offsetWidth / 2 + offsets[i].x,
        y: card.offsetTop + card.offsetHeight / 2 + offsets[i].y,
      }));
      const d = smoothClosedPath(pts);
      line.setAttribute('d', d);
      glow.setAttribute('d', d);
      pts.forEach((pt, i) => {
        knots[i].setAttribute('cx', pt.x.toFixed(1));
        knots[i].setAttribute('cy', pt.y.toFixed(1));
      });
    }

    function frame(now) {
      if (!running) return;
      const t = (now - t0) / 1000;
      cards.forEach((card, i) => {
        const c = drift[i];
        const dx = Math.sin(t * c.speed + c.phase) * c.ampX;
        const dy = Math.cos(t * c.speed * 0.9 + c.phase * 1.3) * c.ampY;
        const s = 1 + 0.018 * Math.sin(t * c.speed * 1.4 + c.phase);
        const r = Math.sin(t * c.speed * 0.7 + c.phase) * 1.1;
        offsets[i].x = dx;
        offsets[i].y = dy;
        card.style.transform =
          `translate3d(${dx.toFixed(1)}px, ${dy.toFixed(1)}px, 0)`
          + ` scale(${s.toFixed(3)}) rotate(${r.toFixed(2)}deg)`;
      });
      drawRope();
      raf = requestAnimationFrame(frame);
    }

    collageEl._collageMotion = {
      start() {
        if (running) return;
        running = true;
        t0 = performance.now();
        raf = requestAnimationFrame(frame);
      },
      stop() {
        running = false;
        if (raf) {
          cancelAnimationFrame(raf);
          raf = null;
        }
      },
    };
    collageEl._collageMotion.start();
  }

  // Brillo que sigue al cursor (solo posiciona variables CSS, sin transforms:
  // no pelea con la deriva ni con el crossfade).
  function setupCollageGlare(cards) {
    const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    if (!finePointer) return;
    cards.forEach((card) => {
      let raf = null;
      card.addEventListener('mousemove', (event) => {
        if (raf) return;
        raf = requestAnimationFrame(() => {
          raf = null;
          const rect = card.getBoundingClientRect();
          const px = (event.clientX - rect.left) / rect.width;
          const py = (event.clientY - rect.top) / rect.height;
          card.style.setProperty('--glare-x', `${(px * 100).toFixed(1)}%`);
          card.style.setProperty('--glare-y', `${(py * 100).toFixed(1)}%`);
        });
      });
      card.addEventListener('mouseleave', () => {
        if (raf) {
          cancelAnimationFrame(raf);
          raf = null;
        }
        card.style.setProperty('--glare-x', '50%');
        card.style.setProperty('--glare-y', '50%');
      });
    });
  }

  function stopMotion() {
    if (collage._collageMotion) collage._collageMotion.stop();
  }

  function startMotion() {
    if (collage._collageMotion && !document.hidden) collage._collageMotion.start();
  }

  // Imágenes extra provistas por el backend (CMS). Sin hardcodeo de rutas /media/.
  let extraImages = [];
  const extraDataEl = document.getElementById('hero-extra-images-data');
  if (extraDataEl) {
    try {
      const parsed = JSON.parse(extraDataEl.textContent);
      if (Array.isArray(parsed)) {
        extraImages = parsed.filter((item) => item && item.src);
      }
    } catch (error) {
      extraImages = [];
    }
  }

  const pauseButton = document.getElementById('collage-pause');
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Sin imágenes extra o con movimiento reducido: collage estático (el Ken Burns
  // vive en CSS) y sin botón de pausa.
  if (extraImages.length === 0 || prefersReducedMotion) {
    if (pauseButton) pauseButton.style.display = 'none';
    return;
  }

  let currentImageIndex = 0;
  let isTransitioning = false;
  let userPaused = false;
  let rotationTimer = null;
  const ROTATION_INTERVAL = 8000;

  function preloadImages(items) {
    items.forEach(item => {
      const img = new Image();
      img.src = item.src;
    });
  }

  preloadImages(extraImages);

  function stopTimer() {
    if (rotationTimer) {
      clearInterval(rotationTimer);
      rotationTimer = null;
    }
  }

  function startTimer() {
    stopTimer();
    if (userPaused || document.hidden) return;
    rotationTimer = setInterval(rotateCard, ROTATION_INTERVAL);
  }

  function setPaused(paused) {
    userPaused = paused;
    collage.classList.toggle('is-paused', paused);
    if (pauseButton) {
      pauseButton.setAttribute('aria-pressed', String(paused));
      pauseButton.setAttribute(
        'aria-label',
        paused ? 'Reanudar animación del carrusel' : 'Pausar animación del carrusel'
      );
    }
    if (paused) {
      stopTimer();
      stopMotion();
    } else {
      startTimer();
      startMotion();
    }
  }

  if (pauseButton) {
    pauseButton.addEventListener('click', () => setPaused(!userPaused));
  }

  // Reinicia el Ken Burns para que cada imagen rotada empiece su propio zoom.
  function restartKenBurns(img) {
    img.style.animation = 'none';
    void img.offsetWidth;
    img.style.animation = '';
  }

  function rotateCard() {
    if (isTransitioning || rotatingCards.length === 0) return;

    const cardToRotate = rotatingCards[Math.floor(Math.random() * rotatingCards.length)];
    if (!cardToRotate) return;

    isTransitioning = true;
    cardToRotate.classList.add('collage-card--exiting');

    setTimeout(() => {
      const img = cardToRotate.querySelector('.collage-image');
      const nextImage = extraImages[currentImageIndex];
      if (img && nextImage) {
        img.src = nextImage.src;
        img.alt = nextImage.alt || img.alt;
        restartKenBurns(img);
        currentImageIndex = (currentImageIndex + 1) % extraImages.length;
      }

      cardToRotate.classList.remove('collage-card--exiting');
      cardToRotate.classList.add('collage-card--entering');

      let finished = false;
      const done = () => {
        if (finished) return;
        finished = true;
        cardToRotate.classList.remove('collage-card--entering');
        isTransitioning = false;
      };
      cardToRotate.addEventListener('animationend', done, { once: true });
      // Respaldo por si animationend no dispara (pestaña oculta, etc.).
      setTimeout(done, 900);
    }, 550);
  }

  startTimer();

  collage.addEventListener('mouseenter', stopTimer);
  collage.addEventListener('mouseleave', startTimer);

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      stopTimer();
      stopMotion();
    } else {
      startTimer();
      startMotion();
    }
  });
}
