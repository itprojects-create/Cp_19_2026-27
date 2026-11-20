'use client';

import styles from './StepDots.module.css';

export default function StepDots({ total, current }) {
  return (
    <div className={styles.dots} role="progressbar" aria-valuenow={current}
      aria-valuemin={1} aria-valuemax={total}
      aria-label={`Step ${current} of ${total}`}
    >
      {Array.from({ length: total }, (_, i) => {
        const step = i + 1;
        const isActive    = step === current;
        const isCompleted = step < current;

        return (
          <span
            key={step}
            className={`
              ${styles.dot}
              ${isActive    ? styles.dotActive    : ''}
              ${isCompleted ? styles.dotCompleted : ''}
            `}
          />
        );
      })}
    </div>
  );
}
