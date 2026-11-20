'use client';

import {
  MapPin,
  FileSearch,
  MessageSquare,
  TrendingUp,
  BarChart2,
  GitMerge,
  FileText,
  Loader,
  Check,
  X,
} from 'lucide-react';
import styles from './AgentNode.module.css';

const ICON_MAP = {
  agent_00: MapPin,
  agent_01: FileSearch,
  agent_02: MessageSquare,
  agent_03: TrendingUp,
  agent_04: BarChart2,
  agent_05: GitMerge,
  agent_06: FileText,
};

const SHORT_ID = {
  agent_00: 'ag-00',
  agent_01: 'ag-01',
  agent_02: 'ag-02',
  agent_03: 'ag-03',
  agent_04: 'ag-04',
  agent_05: 'ag-05',
  agent_06: 'ag-06',
};

export default function AgentNode({ id, label, state = 'idle', paused = false }) {
  const Icon = ICON_MAP[id] || FileText;
  const shortId = SHORT_ID[id] || id;

  const stateClass = {
    idle: styles.idle,
    running: styles.running,
    complete: styles.complete,
    error: styles.error,
  }[state] || styles.idle;

  const cardClass = [
    styles.card,
    stateClass,
    paused && state === 'running' ? styles.paused : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={cardClass}>
      {/* Glow ring for running */}
      {state === 'running' && !paused && <span className={styles.glowRing} />}

      {/* Top-right status badge */}
      {state === 'running' && !paused && (
        <span className={styles.badge}>
          <Loader className={styles.spin} size={12} />
        </span>
      )}
      {state === 'running' && paused && (
        <span className={`${styles.badge} ${styles.badgePaused}`}>
          <span className={styles.pauseIcon} />
        </span>
      )}
      {state === 'complete' && (
        <span className={`${styles.badge} ${styles.badgeComplete}`}>
          <Check size={12} strokeWidth={2.5} />
        </span>
      )}
      {state === 'error' && (
        <span className={`${styles.badge} ${styles.badgeError}`}>
          <X size={12} strokeWidth={2.5} />
        </span>
      )}

      {/* Center icon */}
      <div className={styles.iconWrap}>
        <Icon size={26} strokeWidth={1.6} />
      </div>

      {/* Bottom row */}
      <div className={styles.footer}>
        <span className={styles.shortId}>{shortId}</span>
        <span className={styles.label}>{label}</span>
      </div>
    </div>
  );
}
