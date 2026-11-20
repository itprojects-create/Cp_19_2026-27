import { Inter, Instrument_Serif } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets:  ['latin'],
  variable: '--font-sans-loaded',
  display:  'swap',
});

const instrumentSerif = Instrument_Serif({
  subsets: ['latin'],
  weight:  ['400'],
  style:   ['normal', 'italic'],
  variable: '--font-serif-loaded',
  display:  'swap',
});

export const metadata = {
  title:       'Shadow Credit — AI Business Credit',
  description: 'Instant credit decisions for informal businesses using AI agents.',
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  themeColor: '#0D0D18',
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${inter.variable} ${instrumentSerif.variable}`}
    >
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                var t = localStorage.getItem('sc-theme') || 'dark';
                document.documentElement.setAttribute('data-theme', t);
              } catch(e) {}
            `,
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
