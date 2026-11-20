import React from 'react';
import styles from './UploadCard.module.css';

interface UploadCardProps {
  icon: string;
  title: string;
  subtitle: string;
  badge?: { text: string; variant: 'success' | 'warning' | 'optional' };
  uploaded?: boolean;
  fileName?: string;
  fileSize?: string;
  error?: string;
  onUpload?: () => void;
  expandable?: boolean;
  expandedContent?: React.ReactNode;
}

export const UploadCard: React.FC<UploadCardProps> = ({
  icon,
  title,
  subtitle,
  badge,
  uploaded = false,
  fileName,
  fileSize,
  error,
  onUpload,
  expandable = false,
  expandedContent,
}) => {
  const [expanded, setExpanded] = React.useState(false);

  return (
    <div className={styles.container}>
      <div
        className={`${styles.card} ${uploaded ? styles.uploaded : ''} ${error ? styles.error : ''}`}
        onClick={!uploaded ? onUpload : undefined}
        role={!uploaded ? 'button' : undefined}
        tabIndex={!uploaded ? 0 : undefined}
      >
        <div className={styles.iconCircle}>{icon}</div>
        
        <div className={styles.content}>
          <div className={styles.titleRow}>
            <span className={styles.title}>{title}</span>
            {badge && (
              <span className={`${styles.badge} ${styles[badge.variant]}`}>
                {badge.text}
              </span>
            )}
          </div>
          <span className={styles.subtitle}>
            {uploaded && fileName ? `${fileName} · ${fileSize}` : subtitle}
          </span>
        </div>

        {uploaded ? (
          <div className={styles.checkmark}>✓</div>
        ) : (
          <div className={styles.uploadIcon}>↑</div>
        )}
      </div>

      {error && <div className={styles.errorMessage}>{error}</div>}

      {expandable && (
        <button
          className={styles.expandButton}
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? '−' : '+'} How to export?
        </button>
      )}

      {expanded && expandedContent && (
        <div className={styles.expandedContent}>{expandedContent}</div>
      )}
    </div>
  );
};
