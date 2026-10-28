/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
        },
        dark: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
        linear: {
          black: '#08090a',
          panel: '#0f1011',
          surface: '#191a1b',
          elevated: '#28282c',
          brand: '#5e6ad2',
          accent: '#7170ff',
          hover: '#828fff',
          lavender: '#7a7fad',
          green: '#27a644',
          emerald: '#10b981',
        },
        ln: {
          text: '#f7f8f8',
          secondary: '#d0d6e0',
          tertiary: '#8a8f98',
          muted: '#62666d',
          border: '#23252a',
          'border-secondary': '#34343a',
          'border-tertiary': '#3e3e44',
          line: '#141516',
          'line-tertiary': '#18191a',
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
      fontFamily: {
        inter: ['Inter Variable', 'Inter', 'SF Pro Display', '-apple-system', 'system-ui', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['Berkeley Mono', 'ui-monospace', 'SF Mono', 'Menlo', 'monospace'],
      },
      fontWeight: {
        'linear': '510',
        'semi': '590',
      },
    },
  },
  plugins: [],
}
