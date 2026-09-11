/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace']
      },
      colors: {
        bg: '#0a0a0a',
        panel: '#111113',
        panel2: '#17171a',
        border: '#222227',
        line: '#2a2a31',
        ink: '#e7e7ea',
        dim: '#8a8a93',
        accent: '#f0b232',
        accent2: '#d99a1f',
        ok: '#5ac96a',
        warn: '#e8b94a',
        err: '#e0625c'
      },
      boxShadow: {
        soft: '0 1px 0 rgba(255,255,255,0.04), 0 8px 24px rgba(0,0,0,0.35)',
        ring: '0 0 0 1px rgba(240,178,50,0.35), 0 0 0 4px rgba(240,178,50,0.10)'
      }
    }
  },
  plugins: []
}
