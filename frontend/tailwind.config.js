/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'SF Mono', 'Menlo', 'monospace'],
      },
      fontSize: {
        '2xs':  ['0.6875rem', { lineHeight: '1rem' }],
        'xs':   ['0.75rem',   { lineHeight: '1.125rem' }],
        'sm':   ['0.8125rem', { lineHeight: '1.25rem' }],
        'base': ['0.875rem',  { lineHeight: '1.375rem' }],
        'md':   ['0.9375rem', { lineHeight: '1.5rem' }],
        'lg':   ['1.0625rem', { lineHeight: '1.5rem' }],
        'xl':   ['1.25rem',   { lineHeight: '1.75rem' }],
        '2xl':  ['1.5rem',    { lineHeight: '2rem' }],
        '3xl':  ['1.875rem',  { lineHeight: '2.25rem' }],
        '4xl':  ['2.25rem',   { lineHeight: '2.5rem' }],
      },
      borderRadius: {
        sm: '4px',
        DEFAULT: '6px',
        md: '6px',
        lg: '8px',
        xl: '10px',
        '2xl': '14px',
      },
      colors: {
        // Surfaces
        canvas:  'rgb(var(--bg-base) / <alpha-value>)',
        surface: 'rgb(var(--bg-elevated) / <alpha-value>)',
        overlay: 'rgb(var(--bg-overlay) / <alpha-value>)',
        subtle:  'rgb(var(--bg-subtle) / <alpha-value>)',

        // Borders
        edge: {
          DEFAULT: 'rgb(var(--border-default) / <alpha-value>)',
          subtle:  'rgb(var(--border-subtle) / <alpha-value>)',
          strong:  'rgb(var(--border-strong) / <alpha-value>)',
        },

        // Text
        ink: {
          DEFAULT: 'rgb(var(--text-primary) / <alpha-value>)',
          2:       'rgb(var(--text-secondary) / <alpha-value>)',
          3:       'rgb(var(--text-tertiary) / <alpha-value>)',
          4:       'rgb(var(--text-muted) / <alpha-value>)',
        },

        // Accent
        accent: {
          DEFAULT: 'rgb(var(--accent) / <alpha-value>)',
          hover:   'rgb(var(--accent-hover) / <alpha-value>)',
          soft:    'rgb(var(--accent-subtle) / <alpha-value>)',
          fg:      'rgb(var(--accent-fg) / <alpha-value>)',
        },

        // Status
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

        // Legacy aliases — now theme-aware, keeps existing pages working
        'brand-dark':   'rgb(var(--bg-base) / <alpha-value>)',
        'brand-panel':  'rgb(var(--bg-elevated) / <alpha-value>)',
        'brand-border': 'rgb(var(--border-default) / <alpha-value>)',
        'brand-accent': 'rgb(var(--accent) / <alpha-value>)',
      },
      boxShadow: {
        xs:   '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        sm:   '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        md:   '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        lg:   '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
        xl:   '0 20px 25px -5px rgb(0 0 0 / 0.15), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
        glow: '0 0 0 1px rgb(var(--accent) / 0.25), 0 0 24px -4px rgb(var(--accent) / 0.45)',
      },
      transitionDuration: { DEFAULT: '150ms' },
      keyframes: {
        'fade-in':  { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        'slide-up': { '0%': { opacity: '0', transform: 'translateY(4px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
      },
      animation: {
        'fade-in': 'fade-in 150ms ease-out',
        'slide-up': 'slide-up 200ms ease-out',
      },
    },
  },
  plugins: [],
}
