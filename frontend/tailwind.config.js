/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'space-black': '#08121E',
        'deep-ocean': '#0F172A',
        'earth-green': '#2ECC71',
        'forest-green': '#1B5E20',
        'eco-lime': '#A3E635',
        'muted': '#94A3B8',
        success: '#22C55E',
        warning: '#F59E0B',
        danger: '#EF4444',
        emerald: {
          50:  'hsl(152, 80%, 97%)',
          100: 'hsl(152, 75%, 90%)',
          200: 'hsl(152, 70%, 80%)',
          300: 'hsl(152, 65%, 65%)',
          400: 'hsl(152, 60%, 52%)',
          500: 'hsl(152, 72%, 40%)',
          600: 'hsl(152, 72%, 32%)',
          700: 'hsl(152, 72%, 24%)',
          800: 'hsl(152, 72%, 16%)',
          900: 'hsl(152, 72%, 10%)',
          950: 'hsl(152, 72%, 6%)',
        },
        slate: {
          850: 'hsl(220, 18%, 11%)',
          950: 'hsl(220, 25%, 5%)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        poppins: ['Poppins', 'sans-serif'],
        montserrat: ['Montserrat', 'sans-serif'],
      },
      animation: {
        'spin-slow': 'spin 2s linear infinite',
      },
      backdropBlur: {
        xl: '24px',
      },
    },
  },
  plugins: [],
}
