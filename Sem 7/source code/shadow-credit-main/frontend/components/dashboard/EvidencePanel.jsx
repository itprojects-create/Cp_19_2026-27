'use client';

import { useState } from 'react';
import {
  MessageSquare, Smartphone, Zap, FileText,
  Landmark, Paperclip, ChevronDown, Upload,
  Lock, ShieldCheck,
} from 'lucide-react';
import StatusBadge from './StatusBadge';
import styles from './EvidencePanel.module.css';

/* ── Icon map by artifact type ── */
const TYPE_ICON = {
  WHATSAPP_EXPORT:  { icon: MessageSquare, color: '#22C55E'  },
  UPI_SCREENSHOT:   { icon: Smartphone,    color: '#6366F1'  },
  ELECTRICITY_BILL: { icon: Zap,           color: '#F59E0B'  },
  SUPPLIER_INVOICE: { icon: FileText,      color: '#6366F1'  },
  BANK_STATEMENT:   { icon: Landmark,      color: '#8B5CF6'  },
  OTHER:            { icon: Paperclip,     color: 'var(--text-muted)' },
};

/* ── Audit dot color by event type ── */
const AUDIT_DOT_COLOR = {
  SESSION_CREATED:       'var(--text-muted)',
  ARTIFACT_UPLOADED:     'var(--brand-primary)',
  AGENT_STARTED:         'rgba(99,102,241,0.6)',
  AGENT_COMPLETED:       '#22C55E',
  CLARIFICATION_ASKED:   '#F59E0B',
  ASSESSMENT_GENERATED:  '#22C55E',
};

/* ── Audit event → readable label ── */
const AUDIT_LABEL = {
  SESSION_CREATED:      'Session Created',
  ARTIFACT_UPLOADED:    'File Uploaded',
  AGENT_STARTED:        'Agent Started',
  AGENT_COMPLETED:      'Agent Completed',
  CLARIFICATION_ASKED:  'Clarification Requested',
  ASSESSMENT_GENERATED: 'Assessment Generated',
};

/* ── Helpers ── */
function formatBytes(bytes) {
  if (!bytes) return '—';
  if (bytes < 1024)    return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

function formatArtifactDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short',
    hour: '2-digit', minute: '2-digit',
  });
}

function formatAuditDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short',
    year: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

function formatExtractedPill(key, value) {
  if (key === 'transaction_count') return `${value} transactions`;
  if (key === 'total_inflow')      return `₹${(value/1000).toFixed(0)}k inflow`;
  if (key === 'total_outflow')     return `₹${(value/1000).toFixed(0)}k outflow`;
  if (key === 'date_range')        return String(value);
  if (key === 'credit_limit')      return `₹${value.toLocaleString('en-IN')} limit`;
  return `${key.replace(/_/g, ' ')}: ${value}`;
}

function formatFieldValue(key, value) {
  const rupeeKeys = ['inflow', 'outflow', 'amount', 'limit', 'credit'];
  if (rupeeKeys.some(k => key.includes(k)) && typeof value === 'number') {
    return `₹${value.toLocaleString('en-IN')}`;
  }
  if (typeof value === 'number') return value.toLocaleString('en-IN');
  return String(value);
}

/* ── ArtifactCard sub-component ── */
function ArtifactCard({ artifact }) {
  const [expanded, setExpanded] = useState(false);

  const typeCfg    = TYPE_ICON[artifact.type] || TYPE_ICON['OTHER'];
  const Icon       = typeCfg.icon;
  const fields     = artifact.extracted_fields
    ? Object.entries(artifact.extracted_fields)
    : [];
  const pillFields = fields.slice(0, 3);
  const hasFields  = artifact.status === 'COMPLETE' && fields.length > 0;
  const truncName  = artifact.filename?.length > 22
    ? artifact.filename.slice(0, 22) + '…'
    : (artifact.filename || 'Unknown file');

  return (
    <div
      className={styles.artifactCard}
      onClick={() => setExpanded(e => !e)}
      role="button"
      aria-expanded={expanded}
    >
      {/* Row 1: icon + name + status + chevron */}
      <div className={styles.artifactRow1}>
        <div className={styles.artifactLeft}>
          <Icon size={16} strokeWidth={1.5} style={{ color: typeCfg.color, flexShrink: 0 }} />
          <span className={styles.artifactName}>{truncName}</span>
        </div>
        <div className={styles.artifactRight}>
          <StatusBadge status={artifact.status} />
          <ChevronDown
            size={14}
            strokeWidth={2}
            className={`${styles.chevron} ${expanded ? styles.chevronOpen : ''}`}
          />
        </div>
      </div>

      {/* Row 2: size + date */}
      <div className={styles.artifactRow2}>
        <span>{formatBytes(artifact.file_size_bytes)}</span>
        <span className={styles.artifactDot}>·</span>
        <span>{formatArtifactDate(artifact.uploaded_at)}</span>
      </div>

      {/* Row 3: extracted field pills — complete only */}
      {hasFields && !expanded && (
        <div className={styles.artifactPills}>
          {pillFields.map(([key, value]) => (
            <span key={key} className={styles.fieldPill}>
              {formatExtractedPill(key, value)}
            </span>
          ))}
        </div>
      )}

      {/* Expanded: full extracted fields */}
      {expanded && hasFields && (
        <div className={styles.expandedFields}>
          {fields.map(([key, value], i) => (
            <div
              key={key}
              className={`${styles.fieldRow} ${i < fields.length - 1 ? styles.fieldRowBorder : ''}`}
            >
              <span className={styles.fieldKey}>
                {key.replace(/_/g, ' ')}
              </span>
              <span className={styles.fieldValue}>
                {formatFieldValue(key, value)}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Expanded: no fields message */}
      {expanded && !hasFields && (
        <div className={styles.noFieldsMsg}>
          {artifact.status === 'COMPLETE'
            ? 'No fields extracted from this file.'
            : 'Extraction pending — fields will appear after processing.'}
        </div>
      )}
    </div>
  );
}

/* ── AuditEntry sub-component ── */
function AuditEntry({ entry, isFirst, isLast }) {
  const dotColor = AUDIT_DOT_COLOR[entry.event_type] || 'var(--text-muted)';
  const label    = AUDIT_LABEL[entry.event_type] || entry.event_type;

  return (
    <div className={styles.auditEntry}>
      {/* Timeline line */}
      <div
        className={styles.timelineLine}
        style={{
          top:    isFirst ? '50%' : 0,
          bottom: isLast  ? '50%' : 0,
        }}
      />
      {/* Timeline dot */}
      <div
        className={styles.timelineDot}
        style={{ background: dotColor }}
      />
      {/* Content */}
      <div className={styles.auditContent}>
        <div className={styles.auditRow1}>
          <span className={styles.auditLabel}>{label}</span>
          {entry.immutable && (
            <span className={styles.immutableBadge}>
              <Lock size={9} strokeWidth={2.5} />
              Immutable
            </span>
          )}
        </div>
        {entry.description && (
          <p className={styles.auditDescription}>{entry.description}</p>
        )}
        <span className={styles.auditTime}>{formatAuditDate(entry.timestamp)}</span>
      </div>
    </div>
  );
}

/* ── Main EvidencePanel component ── */
export default function EvidencePanel({ artifacts, auditLog }) {
  const safeArtifacts = artifacts || [];
  const safeAuditLog  = auditLog  || [];

  return (
    <div className={styles.panel}>

      {/* ── Panel header ── */}
      <div className={styles.panelHeader}>
        <span className={styles.panelTitle}>Evidence</span>
        <span className={styles.fileCount}>
          {safeArtifacts.length} file{safeArtifacts.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* ── Artifacts list ── */}
      <div className={styles.artifactsList}>
        {safeArtifacts.length === 0 ? (
          <div className={styles.emptyArtifacts}>
            <Upload size={22} strokeWidth={1.3} className={styles.emptyIcon} />
            <span className={styles.emptyText}>No files uploaded</span>
          </div>
        ) : (
          safeArtifacts.map(artifact => (
            <ArtifactCard key={artifact.artifact_id} artifact={artifact} />
          ))
        )}
      </div>

      {/* ── Audit trail section divider ── */}
      <div className={styles.sectionDivider}>
        <span className={styles.sectionTitle}>Audit Trail</span>
        <div className={styles.immutableHeader}>
          <ShieldCheck size={10} strokeWidth={2.5} className={styles.immutableIcon} />
          <span className={styles.immutableText}>Immutable</span>
        </div>
      </div>

      {/* ── Audit log ── */}
      <div className={styles.auditList}>
        {safeAuditLog.length === 0 ? (
          <div className={styles.emptyAudit}>
            <span className={styles.emptyText}>No audit events yet</span>
          </div>
        ) : (
          safeAuditLog.map((entry, i) => (
            <AuditEntry
              key={entry.log_id || i}
              entry={entry}
              isFirst={i === 0}
              isLast={i === safeAuditLog.length - 1}
            />
          ))
        )}
      </div>

    </div>
  );
}
