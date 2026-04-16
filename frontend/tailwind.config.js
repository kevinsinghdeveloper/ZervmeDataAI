/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}', './public/index.html'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f3f1fe',
          100: '#e9e5fd',
          200: '#d5cdfb',
          300: '#b5a7f7',
          400: '#9a88f3',
          500: '#7b6df6',
          600: '#6a4fef',
          700: '#5b3fd9',
          800: '#4b34b5',
          900: '#3e2d94',
          DEFAULT: '#7b6df6',
        },
        secondary: {
          DEFAULT: '#10b981',
          light: '#34d399',
          dark: '#059669',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Roboto', 'Helvetica', 'Arial', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
