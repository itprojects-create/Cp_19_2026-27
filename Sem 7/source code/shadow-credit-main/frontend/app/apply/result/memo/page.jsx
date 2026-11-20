'use client';

import { useState, useEffect } from 'react';
import { useRouter }           from 'next/navigation';
import { Printer, ArrowLeft, ShieldCheck } from 'lucide-react';
import { api }                 from '@/lib/api';
import styles                  from './memo.module.css';

/* ── Helpers ── */
function formatRupees(amount) {
  if (!amount && amount !== 0) return '—';
  return new Intl.NumberFormat('en-IN', {
    style:                 'currency',
    currency:              'INR',
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'long', year: 'numeric',
  });
}

function formatShortDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function getVerdict(grade) {
  if (['A','B+','B'].includes(grade)) return 'APPROVED';
  if (grade === 'C')                  return 'CONDITIONAL';
  return 'DECLINED';
}

function getVerdictColor(grade) {
  if (['A','B+','B'].includes(grade)) return '#16A34A';
  if (grade === 'C')                  return '#D97706';
  return '#DC2626';
}

function getVerdictBg(grade) {
  if (['A','B+','B'].includes(grade)) return 'rgba(22,163,74,0.07)';
  if (grade === 'C')                  return 'rgba(217,119,6,0.07)';
  return 'rgba(220,38,38,0.07)';
}

function getVerdictBorder(grade) {
  if (['A','B+','B'].includes(grade)) return 'rgba(22,163,74,0.2)';
  if (grade === 'C')                  return 'rgba(217,119,6,0.2)';
  return 'rgba(220,38,38,0.2)';
}

const ARTIFACT_TYPE_LABEL = {
  WHATSAPP_EXPORT:  'WhatsApp Export',
  UPI_SCREENSHOT:   'UPI Screenshot',
  ELECTRICITY_BILL: 'Electricity Bill',
  SUPPLIER_INVOICE: 'Supplier Invoice',
  BANK_STATEMENT:   'Bank Statement',
  OTHER:            'Other Document',
};

export default function MemoPage() {
  const router = useRouter();

  const [sessionId,   setSessionId]   = useState(null);
  const [sessionData, setSessionData] = useState(null);
  const [loading,     setLoading]     = useState(true);
  const [error,       setError]       = useState('');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const id     = params.get('session');
    if (!id) { router.replace('/apply'); return; }
    setSessionId(id);

    api.getSession(id)
      .then(data => setSessionData(data))
      .catch(() => setError('Could not load memo. Please go back and try again.'))
      .finally(() => setLoading(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── Derived data ── */
  const session    = sessionData?.session          || {};
  const assessment = sessionData?.credit_assessments?.[0] || null;
  const artifacts  = sessionData?.artifacts        || [];
  const hasFlags   = assessment?.risk_flags?.length > 0;

  const verdict       = assessment ? getVerdict(assessment.grade)       : '—';
  const verdictColor  = assessment ? getVerdictColor(assessment.grade)  : '#555';
  const verdictBg     = assessment ? getVerdictBg(assessment.grade)     : 'transparent';
  const verdictBorder = assessment ? getVerdictBorder(assessment.grade) : '#ccc';

  /* ── Loading state ── */
  if (loading) {
    return (
      <div className={styles.loadingRoot}>
        <div className={styles.loadingSpinner} />
        <p className={styles.loadingText}>Preparing your memo...</p>
      </div>
    );
  }

  /* ── Error state ── */
  if (error) {
    return (
      <div className={styles.loadingRoot}>
        <p className={styles.errorText}>{error}</p>
        <button className={styles.backBtnSmall} onClick={() => router.back()}>
          ← Go back
        </button>
      </div>
    );
  }

  /* ── Memo render ── */
  return (
    <div className={styles.root}>

      {/* ══ ACTION BAR (not printed) ══ */}
      <div className={styles.actionBar}>
        <button className={styles.backBtn} onClick={() => router.back()}>
          <ArrowLeft size={15} strokeWidth={2} />
          Back
        </button>

        <span className={styles.actionTitle}>Bank Credit Memo</span>

        <button
          className={styles.printBtn}
          onClick={() => window.print()}
        >
          <Printer size={15} strokeWidth={1.8} />
          Download PDF
        </button>
      </div>

      {/* ══ MEMO DOCUMENT ══ */}
      <div className={styles.memoDocument}>

        {/* ── SECTION 1: HEADER ── */}
        <div className={styles.memoHeader}>
          <div className={styles.headerLeft}>
            <div className={styles.brandName}>SHADOW CREDIT</div>
            <div className={styles.brandSub}>AI Credit Assessment System</div>
          </div>
          <div className={styles.headerRight}>
            <div className={styles.memoLabel}>CREDIT ASSESSMENT MEMO</div>
            <div className={styles.memoRef}>REF: {sessionId || '—'}</div>
            <div className={styles.memoDate}>{formatDate(session.created_at)}</div>
          </div>
        </div>
        <div className={styles.headerDivider} />

        {/* ── SECTION 2: APPLICANT DETAILS ── */}
        <div className={styles.section}>
          <div className={styles.sectionLabel}>APPLICANT DETAILS</div>
          <div className={styles.detailsGrid}>
            <div className={styles.detailRow}>
              <span className={styles.detailKey}>Full Name</span>
              <span className={styles.detailVal}>{session.owner_name || '—'}</span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailKey}>Location</span>
              <span className={styles.detailVal}>{session.location_district || '—'}</span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailKey}>Session ID</span>
              <span className={styles.detailVal}>{sessionId || '—'}</span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailKey}>Assessment Date</span>
              <span className={styles.detailVal}>{formatShortDate(session.created_at)}</span>
            </div>
          </div>
        </div>

        {/* ── SECTION 3: CREDIT DECISION ── */}
        {assessment && (
          <div className={styles.section}>
            <div className={styles.sectionLabel}>CREDIT DECISION</div>
            <div className={styles.decisionBox}>

              {/* Left column */}
              <div className={styles.decisionLeft}>
                <div className={styles.decisionVerdictLabel}>VERDICT</div>
                <div
                  className={styles.decisionVerdict}
                  style={{ color: verdictColor }}
                >
                  {verdict}
                </div>
                <span
                  className={styles.gradeBadge}
                  style={{
                    color:       verdictColor,
                    background:  verdictBg,
                    borderColor: verdictBorder,
                  }}
                >
                  Grade {assessment.grade}
                </span>
              </div>

              {/* Right column */}
              <div className={styles.decisionRight}>
                {assessment.credit_limit > 0 && (
                  <>
                    <div className={styles.limitLabel}>APPROVED LIMIT</div>
                    <div className={styles.limitValue}>
                      {formatRupees(assessment.credit_limit)}
                    </div>
                    <div className={styles.limitDetails}>
                      {assessment.interest_rate}% p.a.
                      {assessment.tenor_months
                        ? ` · ${assessment.tenor_months} months`
                        : ''}
                    </div>
                    {assessment.recommended_product && (
                      <div className={styles.productName}>
                        {assessment.recommended_product}
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* Confidence bar — full width */}
              {assessment.confidence_score != null && (
                <div className={styles.confidenceRow}>
                  <div className={styles.confidenceLabelRow}>
                    <span className={styles.confidenceLabel}>
                      AI Confidence Score
                    </span>
                    <span className={styles.confidenceValue}>
                      {Math.round(assessment.confidence_score * 100)}%
                    </span>
                  </div>
                  <div className={styles.confidenceTrack}>
                    <div
                      className={styles.confidenceFill}
                      style={{
                        width: `${assessment.confidence_score * 100}%`,
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── SECTION 4: ANALYSIS SUMMARY ── */}
        {assessment?.explanation && (
          <div className={styles.section}>
            <div className={styles.sectionLabel}>ANALYSIS SUMMARY</div>
            <p className={styles.explanationText}>{assessment.explanation}</p>
          </div>
        )}

        {/* ── SECTION 5: SUPPORTING DOCUMENTS ── */}
        <div className={styles.section}>
          <div className={styles.sectionLabel}>SUPPORTING DOCUMENTS</div>
          {artifacts.length === 0 ? (
            <p className={styles.noDocsText}>No documents uploaded.</p>
          ) : (
            <table className={styles.docsTable}>
              <thead>
                <tr>
                  <th className={styles.docTh}>Document Type</th>
                  <th className={styles.docTh}>Filename</th>
                  <th className={styles.docTh}>Status</th>
                </tr>
              </thead>
              <tbody>
                {artifacts.map((a) => (
                  <tr key={a.artifact_id} className={styles.docRow}>
                    <td className={styles.docTd}>
                      {ARTIFACT_TYPE_LABEL[a.type] || 'Document'}
                    </td>
                    <td className={styles.docTd}>{a.filename || '—'}</td>
                    <td className={styles.docTd}>
                      <span
                        className={styles.docStatus}
                        style={{
                          color: a.status === 'COMPLETE' ? '#16A34A'
                               : a.status === 'FAILED'   ? '#DC2626'
                               : '#888',
                        }}
                      >
                        {a.status === 'COMPLETE' ? '✓ Verified'
                       : a.status === 'FAILED'   ? '✗ Failed'
                       : 'Pending'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* ── SECTION 6: RISK FLAGS (only if non-empty) ── */}
        {hasFlags && (
          <div className={styles.section}>
            <div className={styles.sectionLabel}>RISK FLAGS & MITIGATIONS</div>
            <div className={styles.flagsList}>
              {assessment.risk_flags.map((flag, i) => (
                <div
                  key={i}
                  className={`${styles.flagRow} ${
                    i < assessment.risk_flags.length - 1
                      ? styles.flagRowBorder : ''
                  }`}
                >
                  <span className={styles.flagWarning}>⚠</span>
                  <span className={styles.flagText}>{flag}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── SECTION 7: COMPLIANCE FOOTER ── */}
        <div className={styles.complianceFooter}>
          <div className={styles.footerRow1}>
            <span className={styles.footerLeft}>
              Prepared by Shadow Credit AI Assessment Engine
            </span>
            <span className={styles.footerRight}>
              <ShieldCheck size={12} strokeWidth={2} className={styles.footerShield} />
              DPDP Act 2023 Compliant
            </span>
          </div>
          <div className={styles.footerRow2}>
            <span className={styles.footerDisclaimer}>
              This memo is AI-generated and subject to bank verification.
            </span>
            <span className={styles.footerAudit}>
              Immutable audit log maintained.
            </span>
          </div>
        </div>

      </div>
    </div>
  );
}
