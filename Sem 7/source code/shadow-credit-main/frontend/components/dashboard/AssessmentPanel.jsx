'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import styles from './AssessmentPanel.module.css';

const DECISION_CONFIG = {
  approved: {
    label:      'Approved',
    color:      'var(--success)',
    bg:         'rgba(34,197,94,0.08)',
    border:     'rgba(34,197,94,0.25)',
  },
  declined: {
    label:      'Declined',
    color:      'var(--danger)',
    bg:         'rgba(239,68,68,0.07)',
    border:     'rgba(239,68,68,0.22)',
  },
  review: {
    label:      'Under Review',
    color:      'var(--warning)',
    bg:         'rgba(234,179,8,0.07)',
    border:     'rgba(234,179,8,0.22)',
  },
  pending: {
    label:      'Pending',
    color:      'var(--text-muted)',
    bg:         'var(--bg-raised)',
    border:     'var(--border-default)',
  },
  running: {
    label:      'Analyzing…',
    color:      'var(--brand-primary)',
    bg:         'rgba(99,102,241,0.07)',
    border:     'rgba(99,102,241,0.2)',
  },
};

function formatINR(amount) {
  if (!amount) return '—';
  return new Intl.NumberFormat('en-IN', {
    style:                 'currency',
    currency:              'INR',
    maximumFractionDigits: 0,
  }).format(amount);
}

function ScoreRing({ score }) {
  if (!score) return <span className={styles.scoreDash}>—</span>;

  const MAX    = 900;
  const MIN    = 300;
  const R      = 36;
  const STROKE = 4;
  const CIRC   = 2 * Math.PI * R;
  const pct    = Math.max(0, Math.min(1, (score - MIN) / (MAX - MIN)));
  const dash   = CIRC * pct;
  const color  = score >= 700 ? 'var(--success)'
               : score >= 550 ? 'var(--warning)'
               :                'var(--danger)';

  return (
    <div className={styles.ringWrap}>
      <svg
        width={R * 2 + STROKE * 2}
        height={R * 2 + STROKE * 2}
        viewBox={`0 0 ${R * 2 + STROKE * 2} ${R * 2 + STROKE * 2}`}
        style={{ transform: 'rotate(-90deg)' }}
      >
        <circle
          cx={R + STROKE}
          cy={R + STROKE}
          r={R}
          fill="none"
          stroke="var(--bg-overlay)"
          strokeWidth={STROKE}
        />
        <circle
          cx={R + STROKE}
          cy={R + STROKE}
          r={R}
          fill="none"
          stroke={color}
          strokeWidth={STROKE}
          strokeDasharray={`${dash} ${CIRC}`}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 800ms cubic-bezier(0.16,1,0.3,1)' }}
        />
      </svg>
      <div className={styles.ringInner}>
        <span className={styles.ringScore} style={{ color }}>
          {score}
        </span>
        <span className={styles.ringMax}>/900</span>
      </div>
    </div>
  );
}

export default function AssessmentPanel({ session, sessionId, onOverride }) {
  const [overrideLoading, setOverrideLoading] = useState(null);
  const [overrideError,   setOverrideError]   = useState(null);
  const [overrideDone,    setOverrideDone]     = useState(null);
  const [noteOpen,        setNoteOpen]         = useState(false);
  const [noteText,        setNoteText]         = useState('');

  const result   = session?.result ?? null;
  const status   = session?.status ?? 'pending';
  const decision = result?.decision ?? status;
  const config   = DECISION_CONFIG[decision] ?? DECISION_CONFIG.pending;

  const isAnalyzing  = status === 'running';
  const isComplete   = ['approved','declined','review'].includes(status);
  const canOverride  = isComplete && !overrideDone;

  async function handleOverride(newDecision) {
    if (!canOverride) return;
    setOverrideError(null);
    setOverrideLoading(newDecision);
    try {
      await api.post(
        `/api/v1/sessions/${sessionId}/override`,
        { decision: newDecision, note: noteText.trim() || null }
      );
      setOverrideDone(newDecision);
      onOverride?.(newDecision);
    } catch (err) {
      setOverrideError('Override failed. Try again.');
    } finally {
      setOverrideLoading(null);
    }
  }

  return (
    <div className={styles.wrap}>

      {/* ── SECTION: Decision ─────────────────────────────────── */}
      <div className={styles.section}>
        <span className={styles.sectionLabel}>AI Decision</span>

        <div
          className={styles.decisionCard}
          style={{
            background:   config.bg,
            borderColor:  config.border,
          }}
        >
          <span
            className={styles.decisionLabel}
            style={{ color: config.color }}
          >
            {config.label}
          </span>
          {isAnalyzing && <span className={styles.analyzingDots}><span/><span/><span/></span>}
        </div>
      </div>

      {/* ── SECTION: Credit Score ─────────────────────────────── */}
      <div className={styles.section}>
        <span className={styles.sectionLabel}>Credit Score</span>
        <div className={styles.scoreRow}>
          <ScoreRing score={result?.credit_score} />
          <div className={styles.scoreRight}>
            {result?.credit_score ? (
              <>
                <span className={styles.scoreTier}>
                  {result.credit_score >= 750 ? 'Excellent'
                 : result.credit_score >= 700 ? 'Good'
                 : result.credit_score >= 600 ? 'Fair'
                 :                              'Poor'}
                </span>
                <span className={styles.scoreRange}>Range 300–900</span>
              </>
            ) : (
              <span className={styles.scoreWaiting}>
                {isAnalyzing ? 'Computing…' : 'Not yet scored'}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* ── SECTION: Recommended Limit ────────────────────────── */}
      {result?.recommended_limit && (
        <div className={styles.section}>
          <span className={styles.sectionLabel}>Recommended Limit</span>
          <span className={styles.limitValue}>
            {formatINR(result.recommended_limit)}
          </span>
        </div>
      )}

      {/* ── SECTION: Verdict ──────────────────────────────────── */}
      {result?.verdict_text && (
        <div className={styles.section}>
          <span className={styles.sectionLabel}>AI Verdict</span>
          <p className={styles.verdictText}>{result.verdict_text}</p>
        </div>
      )}

      {/* ── SECTION: Override Actions ─────────────────────────── */}
      {isComplete && (
        <div className={styles.section}>
          <span className={styles.sectionLabel}>RM Override</span>

          {overrideDone ? (
            <div className={styles.overrideDone}>
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                <path d="M2 7l4 4 5-5.5"
                  stroke="var(--success)"
                  strokeWidth="1.6"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              Override recorded:{' '}
              <strong>
                {overrideDone === 'approved' ? 'Approved' : 'Declined'}
              </strong>
            </div>
          ) : (
            <>
              {/* Analyst note toggle */}
              <button
                className={styles.noteToggle}
                onClick={() => setNoteOpen(v => !v)}
              >
                {noteOpen ? '− Hide note' : '+ Add analyst note'}
              </button>

              {noteOpen && (
                <textarea
                  className={styles.noteArea}
                  placeholder="Reason for override (optional)…"
                  value={noteText}
                  onChange={e => setNoteText(e.target.value)}
                  rows={3}
                />
              )}

              {overrideError && (
                <span className={styles.overrideError}>{overrideError}</span>
              )}

              <div className={styles.overrideBtns}>
                <button
                  className={`${styles.overrideBtn} ${styles.approveBtn}`}
                  onClick={() => handleOverride('approved')}
                  disabled={!!overrideLoading}
                >
                  {overrideLoading === 'approved'
                    ? <span className={styles.spinner} />
                    : (
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                        <path
                          d="M2 6.5l3 3 5-5"
                          stroke="currentColor"
                          strokeWidth="1.6"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    )
                  }
                  Approve
                </button>

                <button
                  className={`${styles.overrideBtn} ${styles.declineBtn}`}
                  onClick={() => handleOverride('declined')}
                  disabled={!!overrideLoading}
                >
                  {overrideLoading === 'declined'
                    ? <span className={styles.spinner} />
                    : (
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                        <path
                          d="M3 3l6 6M9 3l-6 6"
                          stroke="currentColor"
                          strokeWidth="1.6"
                          strokeLinecap="round"
                        />
                      </svg>
                    )
                  }
                  Decline
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {/* ── SECTION: Meta ─────────────────────────────────────── */}
      <div className={styles.section}>
        <span className={styles.sectionLabel}>Session Meta</span>
        <div className={styles.metaGrid}>
          <span className={styles.metaKey}>Session</span>
          <span className={styles.metaVal}>
            {sessionId?.slice(0, 12)}…
          </span>

          <span className={styles.metaKey}>Business</span>
          <span className={styles.metaVal}>
            {session?.business_name ?? '—'}
          </span>

          <span className={styles.metaKey}>Type</span>
          <span className={styles.metaVal}>
            {session?.business_type ?? '—'}
          </span>

          <span className={styles.metaKey}>Submitted</span>
          <span className={styles.metaVal}>
            {session?.created_at
              ? new Date(session.created_at).toLocaleDateString('en-IN', {
                  day: '2-digit', month: 'short', year: 'numeric',
                })
              : '—'}
          </span>

          <span className={styles.metaKey}>Owner</span>
          <span className={styles.metaVal}>
            {session?.owner_name ?? '—'}
          </span>

          <span className={styles.metaKey}>Phone</span>
          <span className={styles.metaVal}>
            {session?.phone ?? '—'}
          </span>
        </div>
      </div>

    </div>
  );
}
