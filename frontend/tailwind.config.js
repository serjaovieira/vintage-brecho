/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        vintage: {
          cream: '#F6F1E7',
          sage: '#638875',
          terracotta: '#CE724A',
          wood: '#5C3D2E',
          text: '#3A3533',
          'cream-light': '#FAF7F2',
          'cream-dark': '#EADBCA',
          'sage-light': '#EEF4F0',
          'sage-dark': '#4F6F5F',
          'terracotta-light': '#F8E9E2',
          'terracotta-dark': '#B55A35',
        },
      },
      fontFamily: {
        serif: ['Fraunces', 'Playfair Display', 'serif'],
        sans: ['Plus Jakarta Sans', 'Inter', 'sans-serif'],
      },
      aspectRatio: {
        '3/4': '3 / 4',
        '4/3': '4 / 3',
        '4/5': '4 / 5',
      },
      boxShadow: {
        'vintage-soft': '0 4px 20px -2px rgba(92, 61, 46, 0.08)',
        'vintage-card': '0 2px 12px 0 rgba(99, 136, 117, 0.12)',
        'vintage-hover': '0 10px 25px -3px rgba(92, 61, 46, 0.14)',
      },
    },
  },
  plugins: [],
}
