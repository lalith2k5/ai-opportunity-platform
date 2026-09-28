/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'SF Pro Display', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'SF Mono', 'ui-monospace', 'Menlo', 'monospace'],
      },
      fontSize: {
        '2xs':  ['0.6875rem', { lineHeight: '1rem',     letterSpacing: '0.02em' }],  // 11 caption2
        'xs':   ['0.75rem',   { lineHeight: '1.125rem', letterSpacing: '0.01em' }],  // 12 caption1
        'sm':   ['0.8125rem', { lineHeight: '1.25rem' }],                            // 13 footnote
        'base': ['0.875rem',  { lineHeight: '1.375rem' }],                           // 14 subhead
        'md':   ['0.9375rem', { lineHeight: '1.5rem' }],                             // 15 subhead+
        'lg':   ['1.0625rem', { lineHeight: '1.5rem',   letterSpacing: '-0.005em' }],// 17 body
        'xl':   ['1.25rem',   { lineHeight: '1.75rem',  letterSpacing: '-0.01em' }], // 20 title3
        '2xl':  ['1.5rem',    { lineHeight: '2rem',     letterSpacing: '-0.015em' }],// 24 title2
        '3xl':  ['1.75rem',   { lineHeight: '2.125rem', letterSpacing: '-0.02em' }], // 28 title1
        '4xl':  ['2.125rem',  { lineHeight: '2.5rem',   letterSpacing: '-0.025em' }],// 34 large
        '5xl':  ['2.5rem',    { lineHeight: '3rem',     letterSpacing: '-0.03em' }], // 40 hero
      },
      borderRadius: {
        sm: '6px',
        DEFAULT: '10px',
        md: '12px',
        lg: '14px',
        xl: '18px',
        '2xl': '22px',
        '3xl': '28px',
      },
      colors: {
        canvas:  'rgb(var(--bg-base) / <alpha-value>)',
        surface: 'rgb(var(--bg-elevated) / <alpha-value>)',
        overlay: 'rgb(var(--bg-overlay) / <alpha-value>)',
        subtle:  'rgb(var(--bg-subtle) / <alpha-value>)',

        edge: {
          DEFAULT: 'rgb(var(--border-default) / <alpha-value>)',
          subtle:  'rgb(var(--border-subtle) / <alpha-value>)',
          strong:  'rgb(var(--border-strong) / <alpha-value>)',
        },

        ink: {
          DEFAULT: 'rgb(var(--text-primary) / <alpha-value>)',
          2:       'rgb(var(--text-secondary) / <alpha-value>)',
          3:       'rgb(var(--text-tertiary) / <alpha-value>)',
          4:       'rgb(var(--text-muted) / <alpha-value>)',
        },

        accent: {
          DEFAULT: 'rgb(var(--accent) / <alpha-value>)',
          hover:   'rgb(var(--accent-hover) / <alpha-value>)',
          soft:    'rgb(var(--accent-subtle) / <alpha-value>)',
          fg:      'rgb(var(--accent-fg) / <alpha-value>)',
        },

        success: {
          DEFAULT: 'rgb(var(--success) / <alpha-value>)',
          soft:    'rgb(var(--success-subtle) / <alpha-value>)',
        },
        warning: {
          DEFAULT: 'rgb(var(--warning) / <alpha-value>)',
          soft:    'rgb(var(--warning-subtle) / <alpha-value>)',
        },
        danger: {
          DEFAULT: 'rgb(var(--danger) / <alpha-value>)',
          soft:    'rgb(var(--danger-subtle) / <alpha-value>)',
        },

        'brand-dark':   'rgb(var(--bg-base) / <alpha-value>)',
        'brand-panel':  'rgb(var(--bg-elevated) / <alpha-value>)',
        'brand-border': 'rgb(var(--border-default) / <alpha-value>)',
        'brand-accent': 'rgb(var(--accent) / <alpha-value>)',
      },
      boxShadow: {
        // Apple-style multi-layer shadows
        xs:   '0 1px 2px rgba(0,0,0,0.35), 0 0 1px rgba(0,0,0,0.25)',
        sm:   '0 2px 6px rgba(0,0,0,0.30), 0 1px 2px rgba(0,0,0,0.25)',
        DEFAULT: '0 4px 12px rgba(0,0,0,0.30), 0 1px 3px rgba(0,0,0,0.20)',
        md:   '0 6px 16px rgba(0,0,0,0.35), 0 2px 6px rgba(0,0,0,0.25)',
        lg:   '0 16px 40px rgba(0,0,0,0.45), 0 6px 16px rgba(0,0,0,0.30)',
        xl:   '0 24px 60px rgba(0,0,0,0.55), 0 10px 24px rgba(0,0,0,0.35)',
        '2xl': '0 40px 80px rgba(0,0,0,0.60), 0 16px 40px rgba(0,0,0,0.40)',
        glow:  '0 0 0 1px rgb(var(--accent) / 0.30), 0 0 40px -8px rgb(var(--accent) / 0.55)',
        'inner-soft': 'inset 0 1px 0 0 rgba(255,255,255,0.04)',
      },
      transitionTimingFunction: {
        // Apple spring-like easings
        'apple':        'cubic-bezier(0.34, 1.56, 0.64, 1)',   // bounce-out
        'smooth':       'cubic-bezier(0.25, 1, 0.5, 1)',       // ease-out-quart
        'standard':     'cubic-bezier(0.4, 0, 0.2, 1)',        // material
      },
      transitionDuration: {
        DEFAULT: '150ms',
        '250': '250ms',
        '400': '400ms',
      },
      keyframes: {
        'fade-in':       { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        'fade-up':       { '0%': { opacity: '0', transform: 'translateY(8px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        'slide-up':      { '0%': { opacity: '0', transform: 'translateY(6px) scale(0.98)' }, '100%': { opacity: '1', transform: 'translateY(0) scale(1)' } },
        'slide-in-left': { '0%': { transform: 'translateX(-100%)' }, '100%': { transform: 'translateX(0)' } },
        'scale-in':      { '0%': { opacity: '0', transform: 'scale(0.96)' }, '100%': { opacity: '1', transform: 'scale(1)' } },
        'shimmer':       { '0%': { backgroundPosition: '-1000px 0' }, '100%': { backgroundPosition: '1000px 0' } },
        'pulse-soft':    { '0%,100%': { opacity: '1' }, '50%': { opacity: '0.6' } },
      },
      animation: {
        'fade-in':       'fade-in 200ms cubic-bezier(0.25, 1, 0.5, 1)',
        'fade-up':       'fade-up 300ms cubic-bezier(0.25, 1, 0.5, 1)',
        'slide-up':      'slide-up 250ms cubic-bezier(0.34, 1.56, 0.64, 1)',
        'slide-in-left': 'slide-in-left 250ms cubic-bezier(0.25, 1, 0.5, 1)',
        'scale-in':      'scale-in 200ms cubic-bezier(0.34, 1.56, 0.64, 1)',
        'shimmer':       'shimmer 2s linear infinite',
        'pulse-soft':    'pulse-soft 2s ease-in-out infinite',
      },
      backdropBlur: {
        'xs': '4px',
        '2xl': '40px',
        '3xl': '64px',
      },
    },
  },
  plugins: [],
}
