/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
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
