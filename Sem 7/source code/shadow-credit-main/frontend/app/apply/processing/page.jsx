'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import AgentNode from '@/components/processing/AgentNode';
import LogStream from '@/components/processing/LogStream';
import styles from './processing.module.css';

const AGENT_META = [
  { id: 'agent_00', icon: 'MapPin',        label: 'Biz Verify'  },
  { id: 'agent_01', icon: 'FileSearch',    label: 'OCR Scan'    },
  { id: 'agent_02', icon: 'MessageSquare', label: 'Chat Parse'  },
  { id: 'agent_03', icon: 'TrendingUp',    label: 'UPI Flow'    },
  { id: 'agent_04', icon: 'BarChart2',     label: 'Seasonal'    },
  { id: 'agent_05', icon: 'GitMerge',      label: 'Reconcile'   },
  { id: 'agent_06', icon: 'FileText',      label: 'Credit Memo' },
];

const IDLE_STATE = Object.fromEntries(
  AGENT_META.map(a => [a.id, 'idle'])
);

function formatElapsed(s) {
  const m = String(Math.floor(s / 60)).padStart(2, '0');
  const sec = String(s % 60).padStart(2, '0');
  return `${m}:${sec}`;
}

function makeLog(level, agentId, message) {
  const now = new Date();
  const ts = now.toTimeString().slice(0, 8);
  return {
    id: `${Date.now()}-${Math.random()}`,
    timestamp: ts,
    level,
    agent_id: agentId || null,
    message,
  };
}

export default function ProcessingPage() {
  const router = useRouter();
  const [sessionId, setSessionId]             = useState(null);
  const [agentStates, setAgentStates]         = useState(IDLE_STATE);
  const [logs, setLogs]                       = useState([]);
  const [clarification, setClarification]     = useState(null);
  // null | { question: string, clarification_id: string }
  const [clarAnswer, setClarAnswer]           = useState('');
  const [clarLoading, setClarLoading]         = useState(false);
  const [clarError, setClarError]             = useState('');
  const [clarRetryCount, setClarRetryCount]   = useState(0);
  const [pausedAgents, setPausedAgents]       = useState([]);
  // tracks which agents were 'running' when clarification arrived
  const [elapsed, setElapsed]                 = useState(0);
  const [wsStatus, setWsStatus]               = useState('connecting');
  const [retryCount, setRetryCount]           = useState(0);
  const [completed, setCompleted]             = useState(false);
  const [retryBanner, setRetryBanner]         = useState(false);
  const [failedBanner, setFailedBanner]       = useState(false);

  const wsRef        = useRef(null);
  const retryRef     = useRef(0);
  const timerRef     = useRef(null);
  const sessionRef   = useRef(null);

  const addLog = useCallback((level, agentId, message) => {
    setLogs(prev => [makeLog(level, agentId, message), ...prev].slice(0, 120));
  }, []);

  const handleWsMessage = useCallback((data) => {
    switch (data.type) {
      case 'AGENT_START':
        setAgentStates(prev => ({ ...prev, [data.agent_id]: 'running' }));
        addLog('AGENT_START', data.agent_id, data.message);
        break;

      case 'AGENT_COMPLETE':
        setAgentStates(prev => ({ ...prev, [data.agent_id]: 'complete' }));
        addLog('AGENT_COMPLETE', data.agent_id, data.message);
        break;

      case 'AGENT_ERROR':
        setAgentStates(prev => ({ ...prev, [data.agent_id]: 'error' }));
        addLog('ERROR', data.agent_id, data.message);
        break;

      case 'LOG':
        addLog(data.level || 'INFO', null, data.message);
        break;

      case 'CLARIFICATION_NEEDED':
        // Capture which agents are currently running so we can
        // show them as paused and restore them after submit
        setAgentStates(prev => {
          const currentlyRunning = Object.entries(prev)
            .filter(([, s]) => s === 'running')
            .map(([id]) => id);
          setPausedAgents(currentlyRunning);
          return prev; // don't change states here — AgentNode reads 'paused' prop
        });
        setClarification({
          question:         data.question,
          clarification_id: data.clarification_id,
        });
        setClarAnswer('');
        setClarError('');
        setClarRetryCount(0);
        addLog('WARN', null, `Agent question: "${data.question}"`);
        break;

      case 'ASSESSMENT_COMPLETE':
      case 'SESSION_COMPLETE':
        addLog('INFO', null, 'Analysis complete. Preparing your result...');
        setCompleted(true);
        // Use ref not state to avoid stale closure
        const sid = sessionRef.current;
        setTimeout(() => {
          router.push(`/apply/result?session=${sid}`);
        }, 1200);
        break;

      default:
        break;
    }
  }, [addLog, router]);

  const connectWebSocket = useCallback((id) => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = new WebSocket(api.wsUrl(id));
    wsRef.current = ws;

    ws.onopen = () => {
      setWsStatus('live');
      setRetryBanner(false);
      retryRef.current = 0;
      setRetryCount(0);
      addLog('INFO', null, 'WebSocket connected — analysis stream live');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWsMessage(data);
      } catch {
        addLog('WARN', null, 'Received non-JSON message from server');
      }
    };

    ws.onerror = () => {
      addLog('ERROR', null, 'WebSocket connection error');
      handleWsError(id);
    };

    ws.onclose = (event) => {
      if (!completed && event.code !== 1000) {
        handleWsError(id);
      }
    };
  }, [addLog, handleWsMessage, completed]);

  const handleWsError = useCallback((id) => {
    const current = retryRef.current;
    if (current < 3) {
      retryRef.current = current + 1;
      setRetryCount(current + 1);
      setWsStatus('retrying');
      setRetryBanner(true);
      addLog('WARN', null, `Connection lost. Retrying (${current + 1}/3)...`);
      setTimeout(() => connectWebSocket(id || sessionRef.current), 2000);
    } else {
      setWsStatus('failed');
      setRetryBanner(false);
      setFailedBanner(true);
      addLog('ERROR', null, 'Connection failed after 3 retries.');
    }
  }, [addLog, connectWebSocket]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('session');
    if (!id) {
      router.replace('/apply');
      return;
    }
    setSessionId(id);
    sessionRef.current = id;

    // Start elapsed timer
    timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000);

    // Fire analysis
    api.runAnalysis(id).catch(() => {
      addLog('WARN', null, 'Could not start analysis — backend may be slow');
    });

    // Connect WebSocket
    connectWebSocket(id);

    return () => {
      clearInterval(timerRef.current);
      if (wsRef.current) wsRef.current.close(1000, 'component unmount');
    };
  }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  const handleClarificationSubmit = async () => {
    if (!clarAnswer.trim() || !clarification) return;

    setClarLoading(true);
    setClarError('');

    try {
      await api.submitClarification(sessionRef.current, {
        clarification_id: clarification.clarification_id,
        response:         clarAnswer.trim(),
        response_label:   'user_explanation',
      });

      // Success — clear modal and resume paused agents visually
      addLog('INFO', null, 'Answer submitted. Resuming analysis...');
      setClarification(null);
      setClarAnswer('');
      setClarError('');
      setClarRetryCount(0);
      setPausedAgents([]);
      // Note: agents visually resume because pausedAgents is now []
      // AgentNode reads paused={pausedAgents.includes(agent.id)}

    } catch (err) {
      const msg = err?.message || 'Failed to submit. Please try again.';
      setClarError(msg);
      setClarRetryCount(c => c + 1);
      addLog('ERROR', null, `Clarification submit failed: ${msg}`);
      // Keep modal open — user can retry
    } finally {
      setClarLoading(false);
    }
  };

  const hasClarification     = !!clarification;
  const runningAgents        = Object.values(agentStates).filter(s => s === 'running').length;
  const completedAgentsCount = Object.values(agentStates).filter(s => s === 'complete').length;

  return (
    <div className={styles.root}>

      {/* ── TOP BAR ─────────────────────────────────────────────── */}
      <div className={styles.topBar}>
        <span className={styles.wordmark}>SHADOW CREDIT</span>

        <div className={styles.statusCenter}>
          {wsStatus === 'failed' ? (
            <span className={styles.statusFailed}>Connection lost</span>
          ) : completed ? (
            <span className={styles.statusDone}>Analysis complete</span>
          ) : hasClarification ? (
            <span className={styles.statusClarify}>Waiting for your input</span>
          ) : (
            <span className={styles.statusLive}>
              Analyzing your business
              <span className={styles.dots}>
                <span /><span /><span />
              </span>
            </span>
          )}
        </div>

        <div className={styles.timer}>
          <span className={styles.timerDot} />
          {formatElapsed(elapsed)}
        </div>
      </div>

      {/* ── RETRY BANNER ────────────────────────────────────────── */}
      {retryBanner && (
        <div className={styles.retryBanner}>
          Connection interrupted — retrying ({retryCount}/3)...
        </div>
      )}

      {/* ── FAILED BANNER ───────────────────────────────────────── */}
      {failedBanner && (
        <div className={styles.failedBanner}>
          Analysis is taking longer than expected. You can safely close
          this tab — we'll notify you when it's ready.
        </div>
      )}

      {/* ── AGENT GRID ──────────────────────────────────────────── */}
      <div className={styles.agentSection}>
        <div className={styles.agentMeta}>
          <span className={styles.agentMetaLabel}>
            {completedAgentsCount} / 7 agents complete
          </span>
          {runningAgents > 0 && (
            <span className={styles.agentMetaRunning}>
              <span className={styles.runningDot} />
              {runningAgents} running
            </span>
          )}
        </div>

        <div className={styles.agentGrid}>
          {AGENT_META.map((agent) => (
            <AgentNode
              key={agent.id}
              id={agent.id}
              icon={agent.icon}
              label={agent.label}
              state={agentStates[agent.id]}
              paused={pausedAgents.includes(agent.id)}
            />
          ))}
        </div>
      </div>

      {/* ── LOG STREAM ──────────────────────────────────────────── */}
      <div className={styles.logSection}>
        <div className={styles.logHeader}>
          <span className={styles.logTitle}>LIVE LOG</span>
          <span className={styles.logCount}>{logs.length} entries</span>
          <span className={`${styles.wsIndicator} ${styles[`ws_${wsStatus}`]}`}>
            {wsStatus === 'live' ? 'STREAM LIVE' :
             wsStatus === 'connecting' ? 'CONNECTING' :
             wsStatus === 'retrying' ? 'RETRYING' : 'OFFLINE'}
          </span>
        </div>
        <LogStream logs={logs} />
      </div>

      {/* ── CLARIFICATION MODAL ─────────────────────────────────── */}
      {clarification && (
        <div className={styles.modalBackdrop}>
          <div className={styles.modal}>

            {/* Eyebrow */}
            <div className={styles.modalEyebrow}>
              Agent needs clarification
            </div>

            {/* Question */}
            <p className={styles.modalQuestion}>
              {clarification.question}
            </p>

            {/* Retry notice — only after first failed attempt */}
            {clarRetryCount > 0 && (
              <div className={styles.modalRetryNotice}>
                Attempt {clarRetryCount + 1} — please try again
              </div>
            )}

            {/* Answer textarea */}
            <textarea
              className={styles.modalTextarea}
              placeholder="Type your answer here..."
              value={clarAnswer}
              onChange={e => {
                setClarAnswer(e.target.value);
                if (clarError) setClarError('');
              }}
              rows={4}
              disabled={clarLoading}
              autoFocus
            />

            {/* Error message */}
            {clarError && (
              <p className={styles.modalError}>{clarError}</p>
            )}

            {/* Submit + skip row */}
            <div className={styles.modalActions}>
              <button
                className={styles.modalSubmit}
                onClick={handleClarificationSubmit}
                disabled={clarLoading || !clarAnswer.trim()}
              >
                {clarLoading ? (
                  <span className={styles.btnSpinner} />
                ) : (
                  <>
                    Send Answer
                    <span className={styles.btnArrow}>→</span>
                  </>
                )}
              </button>

              {/* Skip — only show after 2+ failed retries */}
              {clarRetryCount >= 2 && (
                <button
                  className={styles.modalSkip}
                  onClick={() => {
                    addLog('WARN', null, 'Clarification skipped by applicant.');
                    setClarification(null);
                    setClarAnswer('');
                    setClarError('');
                    setClarRetryCount(0);
                    setPausedAgents([]);
                  }}
                  disabled={clarLoading}
                >
                  Skip this question
                </button>
              )}
            </div>

            {/* Progress indicator if multiple clarifications */}
            <p className={styles.modalHint}>
              Your answer helps the AI make a more accurate assessment.
            </p>

          </div>
        </div>
      )}

      {/* ── COMPLETION OVERLAY ──────────────────────────────────── */}
      {completed && (
        <div className={styles.completeOverlay}>
          <div className={styles.completeIcon}>✓</div>
          <p className={styles.completeText}>Analysis complete. Preparing your result...</p>
        </div>
      )}

    </div>
  );
}
