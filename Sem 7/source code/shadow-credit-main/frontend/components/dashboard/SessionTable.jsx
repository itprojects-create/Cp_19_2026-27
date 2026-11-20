'use client';

import { Inbox } from 'lucide-react';
import StatusBadge from './StatusBadge';
import styles from './SessionTable.module.css';

function GradeBadge({ grade }) {
  if (!grade) return <span className={styles.emptyCell}>—</span>;

  const colorMap = {
    'A':  { color: '#22C55E', bg: 'rgba(34,197,94,0.08)',  border: 'rgba(34,197,94,0.2)'  },
    'B+': { color: '#22C55E', bg: 'rgba(34,197,94,0.08)',  border: 'rgba(34,197,94,0.2)'  },
    'B':  { color: '#22C55E', bg: 'rgba(34,197,94,0.08)',  border: 'rgba(34,197,94,0.2)'  },
    'C':  { color: '#F59E0B', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)' },
    'D':  { color: '#EF4444', bg: 'rgba(239,68,68,0.08)',  border: 'rgba(239,68,68,0.2)'  },
  };

  const cfg = colorMap[grade] || colorMap['D'];

  return (
    <span
      className={styles.gradePill}
      style={{
        color:       cfg.color,
        background:  cfg.bg,
        borderColor: cfg.border,
      }}
    >
      {grade}
    </span>
  );
}

function formatDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('en-IN', {
    day:    '2-digit',
    month:  'short',
    hour:   '2-digit',
    minute: '2-digit',
  });
}

export default function SessionTable({ sessions, onSelect, formatRupees }) {
  if (!sessions || sessions.length === 0) {
    return (
      <div className={styles.emptyState}>
        <Inbox size={32} strokeWidth={1.2} className={styles.emptyIcon} />
        <p className={styles.emptyTitle}>No sessions found</p>
        <p className={styles.emptySub}>
          Sessions will appear here as applicants submit.
        </p>
      </div>
    );
  }

  return (
    <table className={styles.table}>
      <thead className={styles.thead}>
        <tr>
          <th className={styles.th}>Session</th>
          <th className={styles.th}>Applicant</th>
          <th className={styles.th}>Location</th>
          <th className={styles.th}>Status</th>
          <th className={styles.th}>Grade</th>
          <th className={styles.th}>Credit Limit</th>
          <th className={styles.th}>Submitted</th>
        </tr>
      </thead>
      <tbody>
        {sessions.map((session) => {
          const assessment  = session.credit_assessments?.[0];
          const isAnalyzing = session.status === 'ANALYZING';
          const isFailed    = session.status === 'FAILED';

          return (
            <tr
              key={session.session_id}
              className={`
                ${styles.row}
                ${isAnalyzing ? styles.rowAnalyzing : ''}
                ${isFailed    ? styles.rowFailed    : ''}
              `}
              onClick={() => onSelect(session.session_id)}
            >
              {/* Session ID */}
              <td className={styles.td}>
                <div className={styles.sessionIdWrap}>
                  <span className={styles.sessionId}>
                    {session.session_id?.slice(0, 10) || '—'}
                  </span>
                  {session.demo_mode && (
                    <span className={styles.demoPill}>DEMO</span>
                  )}
                </div>
              </td>

              {/* Applicant */}
              <td className={styles.td}>
                <span className={styles.applicantName}>
                  {session.owner_name || '—'}
                </span>
              </td>

              {/* Location */}
              <td className={styles.td}>
                <span className={styles.location}>
                  {session.location_district || '—'}
                </span>
              </td>

              {/* Status */}
              <td className={styles.td}>
                <StatusBadge status={session.status} />
              </td>

              {/* Grade */}
              <td className={styles.td}>
                <GradeBadge grade={assessment?.grade} />
              </td>

              {/* Credit limit */}
              <td className={styles.td}>
                {assessment?.credit_limit
                  ? <span className={styles.limitValue}>
                      {formatRupees(assessment.credit_limit)}
                    </span>
                  : <span className={styles.emptyCell}>—</span>
                }
              </td>

              {/* Date */}
              <td className={styles.td}>
                <span className={styles.dateValue}>
                  {formatDate(session.created_at)}
                </span>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
