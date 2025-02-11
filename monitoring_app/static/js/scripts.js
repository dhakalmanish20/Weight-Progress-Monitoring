document.addEventListener('DOMContentLoaded', function () {
  // Typed.js for animated typing effect in the hero section
  if (document.querySelector('.typed-text')) {
      new Typed('.typed-text', {
          strings: ['Achieve Your Best Self', 'Transform Your Life', 'Join FitnessPro Today'],
          typeSpeed: 50,
          backSpeed: 25,
          loop: true
      });
  }

  // Initialize WOW.js for scroll animations
  new WOW().init();
});