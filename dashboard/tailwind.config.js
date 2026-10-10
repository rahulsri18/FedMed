/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Space Grotesk"', '"Plus Jakarta Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
      },
      colors: {
        ops: {
          bg: '#f8fafc',
          surface: '#ffffff',
          elevated: '#f1f5f9',
          panel: '#ffffff',
          border: 'rgba(226, 232, 240, 0.95)',
          'border-active': 'rgba(2, 132, 199, 0.45)',
        },
        clinical: {
          cyan: '#0284c7',
          teal: '#0d9488',
          emerald: '#059669',
          amber: '#d97706',
          coral: '#e11d48',
          purple: '#7c3aed',
          blue: '#2563eb',
        },
        mask: {
          wt: '#059669', // Whole Tumor
          tc: '#d97706', // Tumor Core
          et: '#e11d48', // Enhancing Tumor
        }
      },
      boxShadow: {
        'card-soft': '0 4px 20px -2px rgba(15, 23, 42, 0.05), 0 2px 6px -1px rgba(15, 23, 42, 0.02)',
        'card-hover': '0 10px 30px -4px rgba(2, 132, 199, 0.1), 0 4px 12px -2px rgba(15, 23, 42, 0.04)',
        'glow-cyan': '0 0 20px -3px rgba(2, 132, 199, 0.25)',
        'glow-emerald': '0 0 20px -3px rgba(5, 150, 105, 0.25)',
        'glow-purple': '0 0 20px -3px rgba(124, 58, 237, 0.25)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 24s linear infinite',
      }
    },
  },
  plugins: [],
}
