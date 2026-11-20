'use client';

import styles from './StatusBadge.module.css';

const STATUS_CONFIG = {
  PENDING: {
    label: 'PENDING',
    className: 'pending',
  },
  ANALYZING: {
    label: 'ANALYZING',
    className: 'analyzing',
  },
  COMPLETE: {
    label: 'COMPLETE',
    className: 'complete',
  },
  FAILED: {
    label: 'FAILED',
    className: 'failed',
  },
};

export default function StatusBadge({ status }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.PENDING;
  const isAnalyzing = status === 'ANALYZING';

  return (
    <span className={`${styles.badge} ${styles[config.className]}`}>
      <span className={`${styles.dot} ${isAnalyzing ? styles.dotPulse : ''}`} />
      <span>{config.label}</span>
    </span>
  );
}
