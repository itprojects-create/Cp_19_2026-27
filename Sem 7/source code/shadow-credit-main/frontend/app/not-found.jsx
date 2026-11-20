'use client';

import Link from 'next/link';
import styles from './not-found.module.css';

export default function NotFound() {
  return (
    <div className={styles.page}>
      <span className={styles.code}>404</span>
      <h1 className={styles.heading}>Page not found</h1>
      <p className={styles.sub}>
        This session or page doesn't exist — or may have expired.
      </p>
      <div className={styles.actions}>
        <Link href="/" className={styles.homeBtn}>
          Go home
        </Link>
        <Link href="/dashboard" className={styles.dashBtn}>
          Open dashboard
        </Link>
      </div>
    </div>
  );
}
