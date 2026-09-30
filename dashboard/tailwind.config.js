/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0fdf4',
          500: '#22c55e',
          900: '#14532d',
        },
        cyber: {
          bg: '#0a0f1d',
          card: '#111827',
          border: '#1f2937',
          accent: '#38bdf8',
        }
      }
    },
  },
  plugins: [],
}
