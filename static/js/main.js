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
    if (paused) stopTimer();
    else startTimer();
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
    if (document.hidden) stopTimer();
    else startTimer();
  });
}
