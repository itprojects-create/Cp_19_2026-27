'use client';

import { useRef } from 'react';
import styles from './LogStream.module.css';

/*
  Log entry shape:
  {
    id:        string   — unique key
    timestamp: string   — "HH:MM:SS"
    level:     string   — "INFO" | "WARN" | "ERROR" | "AGENT_START" | "AGENT_COMPLETE"
    agent_id:  string | null
    message:   string
  }

  Entries are stored newest-first (index 0 = latest).
  We render them in order — newest at top, no scroll needed for latest.
*/

function getLineClass(level) {
  switch (level) {
    case 'ERROR':          return styles.lineError;
    case 'WARN':           return styles.lineWarn;
    case 'AGENT_START':    return styles.lineAgentStart;
    case 'AGENT_COMPLETE': return styles.lineAgentComplete;
    default:               return styles.lineInfo;
  }
}

function getLevelTag(level) {
  switch (level) {
    case 'ERROR':          return 'ERR';
    case 'WARN':           return 'WRN';
    case 'AGENT_START':    return 'AGT';
    case 'AGENT_COMPLETE': return 'AGT';
    default:               return 'INF';
  }
}

function getLevelTagClass(level) {
  switch (level) {
    case 'ERROR':          return styles.tagError;
    case 'WARN':           return styles.tagWarn;
    case 'AGENT_START':    return styles.tagAgentStart;
    case 'AGENT_COMPLETE': return styles.tagAgentComplete;
    default:               return styles.tagInfo;
  }
}

export default function LogStream({ logs }) {
  const containerRef = useRef(null);

  return (
    <div className={styles.stream} ref={containerRef}>
      {logs.length === 0 ? (
        <div className={styles.empty}>
          <span className={styles.emptyCursor}>_</span>
          <span className={styles.emptyText}>Waiting for analysis stream...</span>
        </div>
      ) : (
        logs.map((log) => (
          <div
            key={log.id}
            className={`${styles.line} ${getLineClass(log.level)}`}
          >
            {/* Timestamp */}
            <span className={styles.timestamp}>[{log.timestamp}]</span>

            {/* Level tag */}
            <span className={`${styles.tag} ${getLevelTagClass(log.level)}`}>
              {getLevelTag(log.level)}
            </span>

            {/* Agent ID — only if present */}
            {log.agent_id && (
              <span className={styles.agentId}>
                {log.agent_id.replace('agent_', 'ag-')}
              </span>
            )}

            {/* Message */}
            <span className={styles.message}>{log.message}</span>
          </div>
        ))
      )}
    </div>
  );
}
