'use client';

import { useState, useMemo } from 'react';
import {
  MapPin, FileSearch, MessageSquare, TrendingUp,
  BarChart2, GitMerge, FileText,
  Check, X, Loader2, PauseCircle,
} from 'lucide-react';
import styles from './AgentGraphPanel.module.css';

const AGENT_META = [
  { id:'agent_00', icon: MapPin,        label:'Business Verify', shortId:'ag-00' },
  { id:'agent_01', icon: FileSearch,    label:'Document OCR',    shortId:'ag-01' },
  { id:'agent_02', icon: MessageSquare, label:'Chat Analysis',   shortId:'ag-02' },
  { id:'agent_03', icon: TrendingUp,    label:'UPI Flow',        shortId:'ag-03' },
  { id:'agent_04', icon: BarChart2,     label:'Seasonal Intel',  shortId:'ag-04' },
  { id:'agent_05', icon: GitMerge,      label:'Reconciliation',  shortId:'ag-05' },
  { id:'agent_06', icon: FileText,      label:'Credit Memo',     shortId:'ag-06' },
];

const LOG_FILTERS = ['All', 'INFO', 'WARN', 'ERROR', 'AGT'];

function matchesFilter(log, filter) {
  if (filter === 'All') return true;
  if (filter === 'AGT') {
    return log.level === 'AGENT_START' || log.level === 'AGENT_COMPLETE';
  }
  return log.level === filter;
}

/* ── Desktop Agent Card ── */
function AgentCard({ agent, state, paused, lastMessage }) {
  const Icon          = agent.icon;
  const effectiveState = paused ? 'paused' : state;

  return (
    <div
      className={`${styles.agentCard} ${styles[`card_${effectiveState}`]}`}
      aria-label={`${agent.label} — ${effectiveState}`}
    >
      {/* Row 1: agent icon + status icon */}
      <div className={styles.cardRow1}>
        <Icon
          size={20}
          strokeWidth={1.4}
          className={styles.agentIcon}
        />
        <div className={styles.statusIcon}>
          {effectiveState === 'running' && (
            <Loader2
              size={14}
              strokeWidth={2}
              className={styles.spinnerIcon}
            />
          )}
          {effectiveState === 'paused' && (
            <PauseCircle
              size={14}
              strokeWidth={2}
              className={styles.pauseIcon}
            />
          )}
          {effectiveState === 'complete' && (
            <Check
              size={14}
              strokeWidth={2.5}
              className={styles.checkIcon}
            />
          )}
          {effectiveState === 'error' && (
            <X
              size={14}
              strokeWidth={2.5}
              className={styles.errorIcon}
            />
          )}
        </div>
      </div>

      {/* Row 2: agent label */}
      <div className={styles.cardLabel}>{agent.label}</div>

      {/* Row 3: agent short ID */}
      <div className={styles.cardShortId}>{agent.shortId}</div>

      {/* Row 4: result summary — complete only */}
      {effectiveState === 'complete' && lastMessage && (
        <div className={styles.cardSummary}>{lastMessage}</div>
      )}
    </div>
  );
}

/* ── Log Line ── */
function LogLine({ log }) {
  const lineClass = {
    INFO:           styles.lineInfo,
    WARN:           styles.lineWarn,
    ERROR:          styles.lineError,
    AGENT_START:    styles.lineAgentStart,
    AGENT_COMPLETE: styles.lineAgentComplete,
  }[log.level] || styles.lineInfo;

  const tagLabel = {
    INFO:           'INF',
    WARN:           'WRN',
    ERROR:          'ERR',
    AGENT_START:    'AGT',
    AGENT_COMPLETE: 'AGT',
  }[log.level] || 'INF';

  const tagClass = {
    INFO:           styles.tagInfo,
    WARN:           styles.tagWarn,
    ERROR:          styles.tagError,
    AGENT_START:    styles.tagAgentStart,
    AGENT_COMPLETE: styles.tagAgentComplete,
  }[log.level] || styles.tagInfo;

  return (
    <div className={`${styles.logLine} ${lineClass}`}>
      <span className={styles.logTs}>[{log.timestamp}]</span>
      <span className={`${styles.logTag} ${tagClass}`}>{tagLabel}</span>
      {log.agent_id && (
        <span className={styles.logAgentId}>
          {log.agent_id.replace('agent_', 'ag-')}
        </span>
      )}
      <span className={styles.logMsg}>{log.message}</span>
    </div>
  );
}

/* ── Main AgentGraphPanel ── */
export default function AgentGraphPanel({
  agentStates,
  logs,
  clarification,
  onClarificationSubmit,
  sessionId,
  wsStatus,
}) {
  const [logFilter, setLogFilter]         = useState('All');
  const [clarAnswer, setClarAnswer]       = useState('');
  const [clarLoading, setClarLoading]     = useState(false);
  const [clarError, setClarError]         = useState('');

  /* Derived */
  const safeStates  = agentStates || {};
  const safeLogs    = logs        || [];

  const completedCount = Object.values(safeStates)
    .filter(s => s === 'complete').length;

  const progressPct = (completedCount / 7) * 100;

  /* Last message per agent (for result summary) */
  const lastAgentMessage = useMemo(() => {
    const map = {};
    [...safeLogs].reverse().forEach(log => {
      if (log.agent_id && log.level === 'AGENT_COMPLETE') {
        if (!map[log.agent_id]) map[log.agent_id] = log.message;
      }
    });
    return map;
  }, [safeLogs]);

  /* Filtered logs */
  const filteredLogs = useMemo(
    () => safeLogs.filter(l => matchesFilter(l, logFilter)),
    [safeLogs, logFilter]
  );

  /* Clarification submit handler */
  const handleSubmit = async () => {
    if (!clarAnswer.trim()) return;
    setClarLoading(true);
    setClarError('');
    try {
      await onClarificationSubmit(clarAnswer.trim());
      setClarAnswer('');
      setClarError('');
    } catch (err) {
      setClarError(err?.message || 'Failed to submit. Try again.');
    } finally {
      setClarLoading(false);
    }
  };

  /* WS indicator config */
  const wsCfg = {
    connecting: { dotClass: styles.wsDotAmber,   label: 'Connecting' },
    live:       { dotClass: styles.wsDotGreen,   label: 'Live'       },
    failed:     { dotClass: styles.wsDotRed,     label: 'Offline'    },
  }[wsStatus] || { dotClass: styles.wsDotAmber, label: 'Connecting' };

  return (
    <div className={styles.panel}>

      {/* ── PANEL HEADER ── */}
      <div className={styles.panelHeader}>
        <span className={styles.panelTitle}>Agent Pipeline</span>

        <div className={styles.progressWrap}>
          <span className={styles.progressLabel}>
            {completedCount}/7 complete
          </span>
          <div className={styles.progressTrack}>
            <div
              className={styles.progressFill}
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>

        <div className={styles.wsIndicator}>
          <span className={`${styles.wsDot} ${wsCfg.dotClass}`} />
          <span className={styles.wsLabel}>{wsCfg.label}</span>
        </div>
      </div>

      {/* ── AGENT GRID ── */}
      <div className={styles.agentGrid}>
        {AGENT_META.map(agent => (
          <AgentCard
            key={agent.id}
            agent={agent}
            state={safeStates[agent.id] || 'idle'}
            paused={!!clarification &&
                    safeStates[agent.id] === 'running'}
            lastMessage={lastAgentMessage[agent.id] || null}
          />
        ))}
      </div>

      {/* ── CLARIFICATION BANNER (inline — no modal on RM view) ── */}
      {clarification && (
        <div className={styles.clarBanner}>
          <div className={styles.clarLeft}>
            <span className={styles.clarEyebrow}>
              Clarification Needed
            </span>
            <p className={styles.clarQuestion}>
              {clarification.question}
            </p>
            {clarError && (
              <p className={styles.clarError}>{clarError}</p>
            )}
          </div>
          <div className={styles.clarRight}>
            <textarea
              className={styles.clarTextarea}
              placeholder="Enter answer..."
              value={clarAnswer}
              onChange={e => {
                setClarAnswer(e.target.value);
                if (clarError) setClarError('');
              }}
              rows={3}
              disabled={clarLoading}
            />
            <button
              className={styles.clarSubmit}
              onClick={handleSubmit}
              disabled={clarLoading || !clarAnswer.trim()}
            >
              {clarLoading
                ? <span className={styles.clarSpinner} />
                : 'Submit Answer →'
              }
            </button>
          </div>
        </div>
      )}

      {/* ── LOG STREAM HEADER ── */}
      <div className={styles.logHeader}>
        <span className={styles.logTitle}>Live Log</span>
        <div className={styles.logFilters}>
          {LOG_FILTERS.map(f => (
            <button
              key={f}
              className={`${styles.filterPill} ${
                logFilter === f ? styles.filterPillActive : ''
              }`}
              onClick={() => setLogFilter(f)}
            >
              {f}
            </button>
          ))}
        </div>
        <span className={styles.logCount}>
          {filteredLogs.length} entries
        </span>
      </div>

      {/* ── LOG STREAM ── */}
      <div className={styles.logStream}>
        {filteredLogs.length === 0 ? (
          <div className={styles.logEmpty}>
            <span className={styles.logCursor}>_</span>
            <span className={styles.logEmptyText}>
              Waiting for agent stream...
            </span>
          </div>
        ) : (
          filteredLogs.map(log => (
            <LogLine key={log.id} log={log} />
          ))
        )}
      </div>

    </div>
  );
}
