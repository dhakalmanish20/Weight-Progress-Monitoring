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
        cursorChar: '|', // Custom cursor character
        smartBackspace: true, // Only backspace what's necessary
      });
    } catch (error) {
      console.error('Typed.js initialization failed:', error);
    }
  }

  // Initialize WOW.js for scroll animations
  if (typeof WOW !== 'undefined') {
    try {
      new WOW({
        boxClass: 'wow', // Default
        animateClass: 'animated', // Default
        offset: 100, // Distance from the bottom of the viewport
        mobile: true, // Enable animations on mobile
        live: true, // Detect new elements added dynamically
      }).init();
    } catch (error) {
      console.error('WOW.js initialization failed:', error);
    }
  }

  // Back to Top Button
  const backToTopButton = document.querySelector('.back-to-top');
  if (backToTopButton) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 300) {
        backToTopButton.classList.add('show');
      } else {
        backToTopButton.classList.remove('show');
      }
    });

    backToTopButton.addEventListener('click', (e) => {
      e.preventDefault();
      window.scrollTo({
        top: 0,
        behavior: 'smooth',
      });
    });
  }
});