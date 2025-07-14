/** @type {import('tailwindcss').Config} */
module.exports = {
  // Use the dark class for dark mode
  darkMode: 'class',
  content: [
    './apps/frontend/src/**/*.{html,ts}',
    './libs/**/*.{html,ts}'
  ],
  plugins: [],
  theme: {
    extend: {
      colors: {
        // Primary color palette (blue-gray)
        primary: {
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
          950: '#020617'
        },
        // Accent colors
        accent: {
          primary: '#06b6d4',
          hover: '#0891b2',
          light: '#67e8f9',
          dark: '#0e7490'
        },
        // Supporting colors
        supporting: {
          blue: '#3b82f6',
          green: '#10b981',
          gold: '#f59e0b'
        },
        // Sector-specific colors
        medical: {
          light: '#10b981',
          dark: '#059669'
        },
        legal: {
          light: '#3b82f6',
          dark: '#2563eb'
        },
        general: {
          light: '#06b6d4',
          dark: '#0891b2'
        }
      },
      fontFamily: {
        greek: ['Roboto', 'Noto Sans Greek', 'sans-serif']
      },
      transitionProperty: {
        height: 'height',
        spacing: 'margin, padding',
        colors: 'background-color, border-color, color, fill, stroke'
      },
      transitionDuration: {
        '300': '300ms'
      },
      transitionTimingFunction: {
        'ease': 'ease'
      }
    },
    screens: {
      sm: '576px',
      md: '768px',
      lg: '992px',
      xl: '1200px',
      '2xl': '1920px'
    }
  }
};