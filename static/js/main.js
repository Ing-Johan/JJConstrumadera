document.addEventListener('DOMContentLoaded', () => {
  const menuToggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('.main-nav');
  const year = document.getElementById('year');
  const contactForm = document.getElementById('contactForm');

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
