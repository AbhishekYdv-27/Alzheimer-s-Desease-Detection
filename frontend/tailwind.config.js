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
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
          50: 'hsl(199 89% 48% / 0.1)',
          100: 'hsl(199 89% 48% / 0.1)',
          200: 'hsl(199 89% 48% / 0.2)',
          300: 'hsl(199 89% 48% / 0.3)',
          400: 'hsl(199 89% 48% / 0.4)',
          500: 'hsl(199 89% 48% / 0.5)',
          600: 'hsl(199 89% 48% / 0.6)',
          700: 'hsl(199 89% 48% / 0.7)',
          800: 'hsl(199 89% 48% / 0.8)',
          900: 'hsl(199 89% 48% / 0.9)',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
          50: 'hsl(270 83% 58% / 0.1)',
          100: 'hsl(270 83% 58% / 0.1)',
          200: 'hsl(270 83% 58% / 0.2)',
          300: 'hsl(270 83% 58% / 0.3)',
          400: 'hsl(270 83% 58% / 0.4)',
          500: 'hsl(270 83% 58% / 0.5)',
          600: 'hsl(270 83% 58% / 0.6)',
          700: 'hsl(270 83% 58% / 0.7)',
          800: 'hsl(270 83% 58% / 0.8)',
          900: 'hsl(270 83% 58% / 0.9)',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        dark: {
          100: '#1e293b',
          200: '#1a2234',
          300: '#151c2c',
          400: '#111827',
          500: '#0f172a',
          600: '#0d1421',
          700: '#0a1019',
          800: '#070d12',
          900: '#050a0d',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'slide-down': 'slideDown 0.5s ease-out',
        'scale-in': 'scaleIn 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
      },
    },
  },
  plugins: [],
}
