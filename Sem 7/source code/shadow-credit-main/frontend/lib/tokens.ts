// Design System Tokens for Shadow Credit RM Dashboard
// Typed with 'as const' for exact literal types

export const COLORS = {
  bg: { base: '#0D1117', surface: '#161B22', elevated: '#1C2128', overlay: '#21262D', input: '#0D1117' },
  border: { subtle: '#21262D', default: '#30363D', strong: '#484F58' },
  text: { primary: '#E6EDF3', secondary: '#8B949E', tertiary: '#6E7681', inverse: '#0D1117' },
  accent: { DEFAULT: '#1F6FEB', subtle: 'rgba(31,111,235,0.1)', hover: '#388BFD' },
  status: {
    success: '#3FB950', successSubtle: 'rgba(63,185,80,0.1)',
    warning: '#D29922', warningSubtle: 'rgba(210,153,34,0.1)',
    error: '#F85149', errorSubtle: 'rgba(248,81,73,0.1)',
    info: '#1F6FEB'
  }
} as const;

export const SPACING = {
  '0': '0px',
  'px': '1px',
  '0.5': '4px',
  '1': '8px',
  '1.5': '12px',
  '2': '16px',
  '2.5': '20px',
  '3': '24px',
  '3.5': '28px',
  '4': '32px',
  '5': '40px',
  '6': '48px',
  '8': '64px',
  '10': '80px',
  '12': '96px',
  '16': '128px',
  '20': '160px',
  '24': '192px',
  '32': '256px',
  '40': '320px',
  '48': '384px',
  '56': '448px',
  '64': '512px',
} as const;

export const RADIUS = { sm: '6px', md: '8px', lg: '12px', xl: '16px', full: '9999px' } as const;

export const SHADOWS = {
  sm: '0 1px 0 rgba(255,255,255,0.04)',
  border: 'inset 0 0 0 1px #30363D',
  modal: '0 16px 48px rgba(0,0,0,0.60)'
} as const;

export const FONT_SIZES = {
  xs: '12px',
  sm: '14px',
  base: '16px',
  lg: '18px',
  xl: '20px',
  '2xl': '24px',
  '3xl': '30px',
  '4xl': '36px',
} as const;
