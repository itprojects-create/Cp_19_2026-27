'use client';

import Link from 'next/link';
import styles from './ApplyShell.module.css';

export default function ApplyShell({ children, showBack = false, backHref = '/' }) {
  return (
    <div className={styles.shell}>
      <header className={styles.topbar}>
        <div className={styles.topbarInner}>
          <Link href="/" className={styles.logo}>
            <span className={styles.logoMark}>SC</span>
            <span className={styles.logoText}>Shadow Credit</span>
          </Link>
          {showBack && (
            <Link href={backHref} className={styles.backLink}>
              ← Back
            </Link>
          )}
        </div>
      </header>
      <main className={styles.main}>
        {children}
      </main>
    </div>
  );
}
