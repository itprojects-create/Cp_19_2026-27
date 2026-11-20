import { Inter, JetBrains_Mono } from 'next/font/google';

export const interFont = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const monoFont = JetBrains_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-mono',
});
