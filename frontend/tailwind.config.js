/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        docuq: {
          bg: '#090d16',
          surface: '#111827',
          elevated: '#1a2234',
          border: '#243049',
          borderHover: '#3b82f6',
          primary: '#3b82f6',
          accent: '#06b6d4',
          textMain: '#f8fafc',
          textMuted: '#94a3b8',
          textDark: '#64748b',
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}
