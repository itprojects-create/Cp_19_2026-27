'use client';

import { useState, useEffect, useRef } from 'react';
import styles from './ClarificationModal.module.css';

export default function ClarificationModal({
  agent,
  question,
  options,
  allowText,
  onSubmit,
  onDismiss,
}) {
  const [selected,  setSelected]  = useState(null);
  const [freeText,  setFreeText]  = useState('');
  const [submitting, setSubmitting] = useState(false);
  const textRef = useRef(null);

  // Focus textarea if no options
  useEffect(() => {
    if (!options?.length && textRef.current) {
      textRef.current.focus();
    }
  }, [options]);

  // Close on Escape
  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') onDismiss?.();
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onDismiss]);

  const answer = selected ?? (allowText ? freeText.trim() : '');
  const canSubmit = !!answer && !submitting;

  async function handleSubmit() {
    if (!canSubmit) return;
    setSubmitting(true);
    await onSubmit(answer);
    setSubmitting(false);
  }

  return (
    <div className={styles.backdrop} onClick={e => {
      if (e.target === e.currentTarget) onDismiss?.();
    }}>
      <div className={styles.modal} role="dialog" aria-modal="true">

        {/* ── Header ─────────────────────────────────────────── */}
        <div className={styles.modalHeader}>
          <div className={styles.headerLeft}>
            <span className={styles.agentPill}>{agent}</span>
            <span className={styles.eyebrow}>Needs clarification</span>
          </div>
          <button
            className={styles.closeBtn}
            onClick={onDismiss}
            aria-label="Dismiss"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path
                d="M3 3l8 8M11 3l-8 8"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </div>

        {/* ── Question ───────────────────────────────────────── */}
        <p className={styles.question}>{question}</p>

        {/* ── Options (radio pills) ──────────────────────────── */}
        {options?.length > 0 && (
          <div className={styles.options}>
            {options.map(opt => (
              <button
                key={opt}
                className={`${styles.optionBtn} ${selected === opt ? styles.optionSelected : ''}`}
                onClick={() => {
                  setSelected(prev => prev === opt ? null : opt);
                  setFreeText('');
                }}
              >
                <span className={`${styles.radio} ${selected === opt ? styles.radioChecked : ''}`} />
                {opt}
              </button>
            ))}
          </div>
        )}

        {/* ── Free text (shown when no option selected or options absent) */}
        {(allowText && (!options?.length || !selected)) && (
          <textarea
            ref={textRef}
            className={styles.textarea}
            placeholder="Type your answer…"
            value={freeText}
            onChange={e => setFreeText(e.target.value)}
            rows={3}
            onKeyDown={e => {
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleSubmit();
            }}
          />
        )}

        {/* ── Footer ─────────────────────────────────────────── */}
        <div className={styles.footer}>
          <span className={styles.hint}>
            {options?.length
              ? 'Select an option or type a custom answer'
              : 'Ctrl + Enter to submit'}
          </span>
          <div className={styles.footerBtns}>
            <button
              className={styles.cancelBtn}
              onClick={onDismiss}
              disabled={submitting}
            >
              Skip
            </button>
            <button
              className={styles.submitBtn}
              onClick={handleSubmit}
              disabled={!canSubmit}
            >
              {submitting
                ? <span className={styles.spinner} />
                : (
                  <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                    <path
                      d="M2 6.5h9M7.5 3l4 3.5-4 3.5"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                )
              }
              Submit Answer
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
