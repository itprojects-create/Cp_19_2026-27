'use client';

import { useEffect, useState } from 'react';
import { healthApi } from '@/lib/api';
import ThemeToggle from '@/components/ThemeToggle';
import styles from './DashboardTopBar.module.css';

export default function DashboardTopBar({ title = '', subtitle = '' }) {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    healthApi.check()
      .then(() => setHealth('operational'))
      .catch(() => setHealth('degraded'));
  }, []);

  return (
    <header className={styles.topbar}>

      {/* Left — page title */}
      <div className={styles.left}>
        {title && (
          <div className={styles.titleBlock}>
            <h1 className={styles.title}>{title}</h1>
            {subtitle && (
              <span className={styles.subtitle}>{subtitle}</span>
            )}
          </div>
        )}
      </div>

      {/* Right — system status + badge + theme toggle */}
      <div className={styles.right}>

        {/* Backend health indicator */}
        <div className={styles.healthBadge}>
          <span
            className={`${styles.healthDot} ${
              health === 'operational'
                ? styles.healthGreen
                : health === 'degraded'
                ? styles.healthRed
                : styles.healthGrey
            }`}
          />
          <span className={styles.healthLabel}>
            {health === 'operational'
              ? 'System operational'
              : health === 'degraded'
              ? 'System degraded'
              : 'Checking...'}
          </span>
        </div>

        {/* Divider */}
        <div className={styles.topbarDivider} />

        {/* Portal label */}
        <div className={styles.portalBadge}>
          <span className={styles.portalDot} />
          <span className={styles.portalLabel}>Bank RM Portal</span>
        </div>

        {/* Divider */}
        <div className={styles.topbarDivider} />

        {/* Theme toggle */}
        <ThemeToggle />

      </div>
    </header>
  );
}
