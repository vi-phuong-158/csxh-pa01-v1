/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./frontend/templates/**/*.html",
    "./frontend/static/js/**/*.js",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      // === HỆ MÀU VCFE (Material You - Dark Olive) ===
      colors: {
        // Primary (Olive Green)
        'primary':                   '#c3cc8c',
        'on-primary':                '#2d3404',
        'primary-container':         '#4b5320',
        'on-primary-container':      '#bdc787',
        'primary-fixed':             '#dfe8a6',
        'primary-fixed-dim':         '#c3cc8c',
        'on-primary-fixed':          '#191e00',
        'on-primary-fixed-variant':  '#434b18',
        'inverse-primary':           '#5a632e',
        'surface-tint':              '#c3cc8c',
        // Secondary (Gold)
        'secondary':                 '#fff9ef',
        'on-secondary':              '#3a3000',
        'secondary-container':       '#ffdb3c',
        'on-secondary-container':    '#725f00',
        'secondary-fixed':           '#ffe16d',
        'secondary-fixed-dim':       '#e9c400',
        'on-secondary-fixed':        '#221b00',
        'on-secondary-fixed-variant':'#544600',
        // Tertiary (Gray)
        'tertiary':                  '#c6c6c7',
        'on-tertiary':               '#2f3131',
        'tertiary-container':        '#4d4f4f',
        'on-tertiary-container':     '#c0c1c1',
        'tertiary-fixed':            '#e2e2e2',
        'tertiary-fixed-dim':        '#c6c6c7',
        'on-tertiary-fixed':         '#1a1c1c',
        'on-tertiary-fixed-variant': '#454747',
        // Surface (Dark Charcoal-Olive)
        'surface':                    '#13140f',
        'surface-dim':                '#13140f',
        'surface-bright':             '#393934',
        'surface-container-lowest':   '#0e0e0a',
        'surface-container-low':      '#1c1c17',
        'surface-container':          '#20201b',
        'surface-container-high':     '#2a2a25',
        'surface-container-highest':  '#353530',
        'surface-variant':            '#353530',
        'on-surface':                 '#e5e2db',
        'on-surface-variant':         '#c8c7b8',
        'inverse-surface':            '#e5e2db',
        'inverse-on-surface':         '#31312c',
        // Error
        'error':                      '#ffb4ab',
        'on-error':                   '#690005',
        'error-container':            '#93000a',
        'on-error-container':         '#ffdad6',
        // Misc
        'outline':                    '#919283',
        'outline-variant':            '#47483c',
        'background':                 '#13140f',
        'on-background':              '#e5e2db',
      },
      // === FONT FAMILY ===
      fontFamily: {
        sans:       ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        'body-md':  ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        'body-lg':  ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        'h1':       ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        'h2':       ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        'h3':       ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        'label-caps':['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        'code':     ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      // === FONT SIZE ===
      fontSize: {
        'h1':         ['40px', { lineHeight: '1.3',  letterSpacing: '-0.02em', fontWeight: '700' }],
        'h2':         ['32px', { lineHeight: '1.4',  letterSpacing: '-0.01em', fontWeight: '600' }],
        'h3':         ['24px', { lineHeight: '1.5',  letterSpacing: '0',       fontWeight: '600' }],
        'body-lg':    ['18px', { lineHeight: '1.7',  letterSpacing: '0',       fontWeight: '400' }],
        'body-md':    ['16px', { lineHeight: '1.7',  letterSpacing: '0',       fontWeight: '400' }],
        'label-caps': ['12px', { lineHeight: '1.5',  letterSpacing: '0.1em',   fontWeight: '700' }],
        'code':       ['14px', { lineHeight: '1.5',                            fontWeight: '500' }],
      },
      // === BORDER RADIUS ===
      borderRadius: {
        'DEFAULT': '0.25rem',
        'lg':      '0.5rem',
        'xl':      '0.75rem',
        '2xl':     '1rem',
        'full':    '9999px',
      },
      // === SPACING ===
      spacing: {
        'unit':              '8px',
        'card-gap':          '24px',
        'gutter':            '32px',
        'section-margin':    '64px',
        'container-padding': '40px',
      },
    },
  },
  plugins: [],
}
