'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { AGENT_REGISTRY } from '@/lib/constants.jsx';
import styles from './Step5Consent.module.css';

export default function Step5Consent({ onBack, sessionData, onRedirect }) {
  const [consented, setConsented] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // ── Data collection with localStorage fallback ──────────────────
  const sessionId = sessionData?.sessionId
    || (typeof window !== 'undefined' && localStorage.getItem('sc_session_id'));
  
  const ownerName = sessionData?.ownerName
    || (typeof window !== 'undefined' && localStorage.getItem('sc_owner_name'))
    || 'Business Owner';
  
  const shopName = sessionData?.shopName
    || (typeof window !== 'undefined' && localStorage.getItem('sc_shop_name'))
    || 'Your Business';
  
  const businessType = sessionData?.businessType
    || (typeof window !== 'undefined' && localStorage.getItem('sc_business_type'))
    || '';
  
  const location = sessionData?.locationDistrict
    || (typeof window !== 'undefined' && localStorage.getItem('sc_location'))
    || '';

  // Count uploaded artifacts
  const filesUploaded = [
    sessionData?.whatsappUploaded,
    (sessionData?.upiCount || 0) > 0,
    sessionData?.billUploaded,
  ].filter(Boolean).length;

  // ── 8 agents from AGENT_REGISTRY ──────────────────────────────
  const agents = [
    AGENT_REGISTRY.agent_00,
    AGENT_REGISTRY.agent_01,
    AGENT_REGISTRY.agent_02,
    AGENT_REGISTRY.agent_02b,
    AGENT_REGISTRY.agent_03,
    AGENT_REGISTRY.agent_04,
    AGENT_REGISTRY.agent_05,
    AGENT_REGISTRY.agent_07,
  ];

  // ── Launch analysis ───────────────────────────────────────────
  async function handleLaunch() {
    if (!consented) return;
    
    setLoading(true);
    setError('');

    try {
      await api.analyzeSession(sessionId);
      // Call parent redirect function
      if (onRedirect) {
        onRedirect(sessionId);
      }
    } catch (err) {
      // Even if analyze call fails, redirect — processing page
      // will retry and show the real state via WebSocket
      if (onRedirect) {
        onRedirect(sessionId);
      }
    }
  }

  return (
    <div className={styles.step}>

      {/* Heading */}
      <div className={styles.heading}>
        <h2 className={styles.title}>Ready to analyze</h2>
        <p className={styles.subtitle}>
          Review your submission and start the AI analysis.
        </p>
      </div>

      {/* Application summary card */}
      <div className={styles.summaryCard}>
        <div className={styles.summaryHeader}>
          <span className={styles.summaryEyebrow}>Your Application</span>
          <span className={styles.summaryStatus}>Ready</span>
        </div>

        <div className={styles.summaryDivider} />

        <div className={styles.summaryGrid}>
          <div className={styles.summaryRow}>
            <span className={styles.summaryKey}>Business</span>
            <span className={styles.summaryVal}>{shopName}</span>
          </div>
          <div className={styles.summaryRow}>
            <span className={styles.summaryKey}>Owner</span>
            <span className={styles.summaryVal}>{ownerName}</span>
          </div>
          {businessType && (
            <div className={styles.summaryRow}>
              <span className={styles.summaryKey}>Type</span>
              <span className={styles.summaryVal}>{businessType}</span>
            </div>
          )}
          {location && (
            <div className={styles.summaryRow}>
              <span className={styles.summaryKey}>Location</span>
              <span className={styles.summaryVal}>{location}</span>
            </div>
          )}
          <div className={styles.summaryRow}>
            <span className={styles.summaryKey}>Documents</span>
            <span className={`${styles.summaryVal} ${
              filesUploaded > 0 ? styles.summaryValGreen : styles.summaryValMuted
            }`}>
              {filesUploaded > 0
                ? `${filesUploaded} file${filesUploaded !== 1 ? 's' : ''} uploaded`
                : 'Proceeding without documents'}
            </span>
          </div>
        </div>
      </div>

      {/* What happens next — agent pills */}
      <div className={styles.agentsBlock}>
        <span className={styles.agentsLabel}>
          8 AI agents will run in parallel
        </span>
        <div className={styles.agentPills}>
          {agents.map((agent) => (
            <span key={agent.id || agent.name} className={styles.agentPill}>
              <span className={styles.agentPillDot} />
              {agent.name}
            </span>
          ))}
        </div>
        <span className={styles.agentsTime}>
          Estimated time: <strong>90 seconds</strong>
        </span>
      </div>

      {/* Consent checkbox */}
      <label className={styles.consentLabel} htmlFor="consent">
        <div className={styles.checkboxWrap}>
          <input
            id="consent"
            type="checkbox"
            className={styles.checkboxInput}
            checked={consented}
            onChange={(e) => setConsented(e.target.checked)}
          />
          <span className={`${styles.checkbox} ${consented ? styles.checkboxChecked : ''}`}>
            {consented && (
              <svg
                width="10"
                height="8"
                viewBox="0 0 10 8"
                fill="none"
                className={styles.checkmark}
              >
                <path
                  d="M1 4L3.5 6.5L9 1"
                  stroke="white"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            )}
          </span>
        </div>
        <span className={styles.consentText}>
          I consent to Shadow Credit analyzing my documents to assess
          creditworthiness. My data is protected under India's{' '}
          <strong className={styles.consentHighlight}>DPDP Act 2023</strong>
          {' '}and will not be shared with third parties without my explicit
          permission.
        </span>
      </label>

      {/* Error */}
      {error && (
        <div className={styles.errorMsg}>
          <span className={styles.errorDot} />
          {error}
        </div>
      )}

      {/* Launch button — 60px, the largest button in the apply flow */}
      <button
        className={`${styles.launchBtn} ${!consented ? styles.launchBtnDisabled : ''}`}
        onClick={handleLaunch}
        disabled={!consented || loading}
        type="button"
      >
        {loading ? (
          <>
            <span className={styles.spinner} aria-hidden="true" />
            <span>Initializing analysis...</span>
          </>
        ) : (
          <>
            <span>Start AI Analysis</span>
            <span className={styles.launchArrow}>→</span>
          </>
        )}
      </button>

      {/* Trust badges */}
      <div className={styles.trustBadges}>
        <span className={styles.trustBadge}>🔒 DPDP Act 2023</span>
        <span className={styles.trustBadge}>⚡ 90 Second Analysis</span>
        <span className={styles.trustBadge}>🏦 Bank Ready Output</span>
      </div>

    </div>
  );
}
