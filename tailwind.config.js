/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './monitoring_app/templates/**/*.html',
    './monitoring_app/static/**/*.js',
    './monitoring_app/static/**/*.css',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#00468B',
        secondary: '#FFD700',
        accent: '#00C9B1',
      },
    },
  },
  plugins: [],
}