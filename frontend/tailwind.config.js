/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-dark': '#0a0e1a',
        'brand-panel': '#131826',
        'brand-border': '#1f2937',
        'brand-accent': '#6366f1',
      }
    },
  },
  plugins: [],
}
