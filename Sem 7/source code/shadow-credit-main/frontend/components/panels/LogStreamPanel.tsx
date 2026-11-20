import React, { useEffect, useRef, useState, useMemo } from 'react';
import { cn } from '../../lib/cn';
import { AgentGraph, AgentNode } from './AgentGraph';
import { StreamEvent } from '../../hooks/useWebSocket';
import { ConfidenceBadge } from '../ui/ConfidenceBadge';

interface LogStreamPanelProps {
  events: StreamEvent[];
  isConnected: boolean;
  sessionId?: string;
}

const AGENT_COLORS: Record<string, string> = {
  SUPERVISOR: 'text-[#C4B5FD]',
  AGENT_00: 'text-[#1F6FEB]',
  AGENT_01: 'text-[#0EA5E9]',
  AGENT_02: 'text-[#10B981]',
  AGENT_02B: 'text-[#6EE7B7]',
  AGENT_03: 'text-[#F59E0B]',
  AGENT_04: 'text-[#8B5CF6]',
  AGENT_05: 'text-[#EF4444]',
  AGENT_06: 'text-[#F97316]',
  AGENT_07: 'text-[#3B82F6]',
};

export const LogStreamPanel: React.FC<LogStreamPanelProps> = ({ events, isConnected, sessionId }) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [userScrolled, setUserScrolled] = useState(false);
  const [showNewEvents, setShowNewEvents] = useState(false);

  // Derive graph state from events
  const { agents, activeEdges } = useMemo(() => {
    const agentMap = new Map<string, AgentNode['status']>();
    const edges: Array<{ from: string; to: string }> = [];
    
    // Default all known nodes to idle
    const knownNodes = ['MAPS', 'OCR', 'WA', 'SMS', 'KHATA', 'SUPERVISOR', 'WARMTH', 'RECON', 'COMPLIANCE', 'REPORT'];
    knownNodes.forEach(id => agentMap.set(id, 'idle'));

    events.forEach(event => {
      // Map agentId to node ID (simple mapping logic - adjust based on real data)
      // Assuming agentName or agentId corresponds to graph nodes
      const nodeId = event.agentName.toUpperCase(); // Simplified mapping
      
      if (knownNodes.includes(nodeId)) {
        if (event.eventType === 'AGENT_STARTED') agentMap.set(nodeId, 'running');
        if (event.eventType === 'AGENT_COMPLETE') agentMap.set(nodeId, 'complete');
        if (event.eventType === 'AGENT_ERROR') agentMap.set(nodeId, 'error');
      }

      // Logic to determine active edges would go here based on event context
      // For now, if supervisor is running, activate edges to it? 
      // This part requires specific business logic on how events map to edges.
      // Implementing basic logic:
      if (nodeId === 'SUPERVISOR' && event.eventType === 'AGENT_STARTED') {
         // Activate incoming edges
         edges.push({ from: 'MAPS', to: 'SUPERVISOR' });
         edges.push({ from: 'OCR', to: 'SUPERVISOR' });
      }
    });

    const agentNodes: AgentNode[] = Array.from(agentMap.entries()).map(([id, status]) => ({
      id,
      status,
      label: id
    }));

    return { agents: agentNodes, activeEdges: edges };
  }, [events]);

  // Auto-scroll logic
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    if (!userScrolled) {
      el.scrollTop = el.scrollHeight;
      setShowNewEvents(false);
    } else {
      // If user is scrolled up and new events come in
      setShowNewEvents(true);
    }
  }, [events, userScrolled]);

  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    
    const isBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 20;
    if (isBottom) {
      setUserScrolled(false);
      setShowNewEvents(false);
    } else {
      setUserScrolled(true);
    }
  };

  const scrollToBottom = () => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    setUserScrolled(false);
    setShowNewEvents(false);
  };

  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString('en-GB', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + date.getMilliseconds().toString().padStart(3, '0');
    } catch {
      return isoString;
    }
  };

  return (
    <div className="flex h-full flex-col bg-[#090D14]">
      {/* Agent Graph Section */}
      <div className="h-[140px] w-full flex-shrink-0 border-b border-border-subtle">
        <AgentGraph agents={agents} activeEdges={activeEdges} />
      </div>

      {/* Log Stream Section */}
      <div className="relative flex-1 overflow-hidden">
        <div 
          ref={scrollRef}
          onScroll={handleScroll}
          className="h-full overflow-y-auto px-4 py-3 font-mono text-[12px]"
        >
          {events.map((event, idx) => {
            const isSupervisor = event.agentId === 'SUPERVISOR';
            
            // Special Banner: Clarification
            if (event.eventType === 'CLARIFICATION_REQUIRED') {
              return (
                <div key={idx} className="my-1 animate-pulse rounded-md border border-status-warning bg-status-warning/10 px-3 py-2 text-status-warning">
                  PIPELINE PAUSED — Supervisor requires RM input
                </div>
              );
            }

            // Special Banner: Session Complete
            if (event.eventType === 'SESSION_COMPLETE') {
              const isSuccess = (event.latencyMs || 0) < 90000;
              const colorClass = isSuccess ? 'border-status-success bg-status-success/10 text-status-success' : 'border-status-warning bg-status-warning/10 text-status-warning';
              
              return (
                <div key={idx} className={cn("my-1 rounded-md border px-3 py-2", colorClass)}>
                  SESSION COMPLETE · {event.latencyMs}ms
                </div>
              );
            }

            // Standard Log Line
            return (
              <div 
                key={idx} 
                className={cn(
                  "flex animate-in fade-in slide-in-from-bottom-1 duration-150 items-baseline gap-2 py-0.5 rounded hover:bg-white/[0.02]",
                  isSupervisor && "pl-4"
                )}
              >
                <span className="flex-shrink-0 text-text-tertiary select-none">
                  {formatTime(event.timestamp)}
                </span>
                
                {isSupervisor && <span className="text-accent">→</span>}
                
                <span className={cn("flex-shrink-0 font-bold", AGENT_COLORS[event.agentId] || 'text-text-primary')}>
                  {event.agentId}
                </span>
                
                <span className="text-text-primary break-all">
                  {event.message}
                </span>

                {event.confidence !== undefined && (
                  <ConfidenceBadge score={event.confidence} />
                )}

                {event.latencyMs !== undefined && (
                  <span className="text-text-tertiary">({event.latencyMs}ms)</span>
                )}
              </div>
            );
          })}
          
          {/* Spacer for bottom scrolling */}
          <div className="h-4" />
        </div>

        {/* New Events Pill */}
        {showNewEvents && (
          <button
            onClick={scrollToBottom}
            className="absolute bottom-4 left-1/2 -translate-x-1/2 animate-in fade-in zoom-in-95 rounded-full bg-accent px-3 py-1 text-[11px] font-medium text-white shadow-lg transition-transform hover:scale-105"
          >
            ↓ New events
          </button>
        )}
      </div>

      {/* Connection Status Bar */}
      <div className="sticky bottom-0 flex h-8 flex-shrink-0 items-center gap-2 border-t border-border-subtle bg-[#090D14] px-4">
        <div 
          className={cn(
            "h-2 w-2 rounded-full transition-colors",
            isConnected ? "bg-status-success" : "bg-text-tertiary"
          )} 
        />
        <span className="text-[11px] text-text-tertiary">
          {isConnected ? `Connected · ${sessionId || 'No Session'}` : 'Reconnecting...'}
        </span>
      </div>
    </div>
  );
};
