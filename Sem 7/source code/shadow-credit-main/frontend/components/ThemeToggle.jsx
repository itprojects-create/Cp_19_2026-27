'use client';

import { useEffect, useState } from 'react';
import styles from './ThemeToggle.module.css';

export default function ThemeToggle() {
  const [theme, setTheme] = useState('dark');
  const [mounted, setMounted] = useState(false);

  // Read persisted theme on mount — avoid flash
  useEffect(() => {
    const saved = localStorage.getItem('sc-theme') ?? 'dark';
    document.documentElement.setAttribute('data-theme', saved);
    setTheme(saved);
    setMounted(true);
  }, []);

  function toggle() {
    const next = theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('sc-theme', next);
    setTheme(next);
  }

  // Render nothing until mounted to prevent hydration mismatch
  if (!mounted) return <div className={styles.placeholder} />;

  const isDark = theme === 'dark';

  return (
    <button
      className={styles.btn}
      onClick={toggle}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={isDark ? 'Light mode' : 'Dark mode'}
    >
      {isDark ? (
        /* Sun icon */
        <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
          <circle cx="7.5" cy="7.5" r="2.5"
            stroke="currentColor" strokeWidth="1.4" />
          <path
            d="M7.5 1v1.5M7.5 12.5V14M1 7.5h1.5M12.5 7.5H14
               M3.05 3.05l1.06 1.06M10.89 10.89l1.06 1.06
               M3.05 11.95l1.06-1.06M10.89 4.11l1.06-1.06"
            stroke="currentColor" strokeWidth="1.4"
            strokeLinecap="round"
          />
        </svg>
      ) : (
        /* Moon icon */
        <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
          <path
            d="M12.5 9.5A6 6 0 015.5 2.5a6 6 0 100 10 6 6 0 007-3z"
            stroke="currentColor" strokeWidth="1.4"
            strokeLinecap="round" strokeLinejoin="round"
          />
        </svg>
      )}
    </button>
  );
}
