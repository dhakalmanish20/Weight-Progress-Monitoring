document.addEventListener('DOMContentLoaded', function () {
  // Typed.js for animated typing effect in the hero section
  const typedElement = document.querySelector('.typed-text');
  if (typedElement) {
      try {
          new Typed(typedElement, {
              strings: ['Achieve Your Best Self', 'Transform Your Life', 'Join FitnessPro Today'],
              typeSpeed: 50,
              backSpeed: 25,
              loop: true,
              cursorChar: '|',
              smartBackspace: true,
          });
      } catch (error) {
          console.error('Typed.js initialization failed:', error);
      }
  }

  // Initialize WOW.js for scroll animations
  if (typeof WOW !== 'undefined') {
      try {
          new WOW({
              boxClass: 'wow',
              animateClass: 'animate__animated',
              offset: 100,
              mobile: true,
              live: true,
          }).init();
      } catch (error) {
          console.error('WOW.js initialization failed:', error);
      }
  }

  // Back to Top Button
  const backToTopButton = document.querySelector('.back-to-top');
  if (backToTopButton) {
      window.addEventListener('scroll', () => {
          backToTopButton.classList.toggle('show', window.scrollY > 300);
      });

      backToTopButton.addEventListener('click', (e) => {
          e.preventDefault();
          window.scrollTo({
              top: 0,
              behavior: 'smooth',
          });
      });
  }

  // Mobile menu toggle
  const menuButton = document.querySelector('.navbar-toggler');
  const navMenu = document.querySelector('.nav-menu');
  if (menuButton && navMenu) {
      menuButton.addEventListener('click', () => {
          navMenu.classList.toggle('active');
      });
  }
});