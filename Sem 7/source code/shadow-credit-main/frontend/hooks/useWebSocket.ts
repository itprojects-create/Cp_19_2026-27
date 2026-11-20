import { useState, useEffect, useRef } from 'react';
import ReconnectingWebSocket from 'reconnecting-websocket';

export type StreamEvent = {
  eventType: 'AGENT_STARTED' | 'AGENT_PROGRESS' | 'AGENT_COMPLETE' | 'AGENT_ERROR' | 
             'CLARIFICATION_REQUIRED' | 'SESSION_COMPLETE';
  timestamp: string; // ISO
  agentId: string;
  agentName: string;
  message: string;
  confidence?: number;
  latencyMs?: number;
  data?: Record<string, unknown>;
};

type WireEvent = {
  type?: string;
  event_type?: string;
  timestamp?: string;
  agent_id?: string;
  message?: string;
  data?: Record<string, unknown>;
};

const normalizeEvent = (raw: WireEvent): StreamEvent | null => {
  const payload = (raw.data || {}) as Record<string, unknown>;
  const inferredFromStatus = payload.status ? `AGENT_${String(payload.status).toUpperCase()}` : '';
  const eventType = String(raw.event_type || payload.event_type || inferredFromStatus).toUpperCase();
  const mappedType =
    eventType === 'AGENT_STARTED' || eventType === 'AGENT_PROGRESS' || eventType === 'AGENT_COMPLETE' || eventType === 'AGENT_ERROR'
      ? eventType
      : eventType === 'AGENT_CLARIFICATION_REQUIRED'
      ? 'CLARIFICATION_REQUIRED'
      : eventType === 'CLARIFICATION_REQUIRED'
      ? 'CLARIFICATION_REQUIRED'
      : eventType === 'SESSION_COMPLETE'
      ? 'SESSION_COMPLETE'
      : null;

  if (!mappedType) return null;

  return {
    eventType: mappedType,
    timestamp: String(raw.timestamp || new Date().toISOString()),
    agentId: String(raw.agent_id || payload.agent_id || 'SYSTEM'),
    agentName: String(payload.agent_name || raw.agent_id || payload.agent_id || 'SYSTEM'),
    message: String(raw.message || payload.message || eventType.replaceAll('_', ' ')),
    confidence: typeof payload.confidence === 'number' ? payload.confidence : undefined,
    latencyMs: typeof payload.latency_ms === 'number' ? payload.latency_ms : undefined,
    data: payload,
  };
};

export const useWebSocket = (sessionId: string) => {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [latestEvent, setLatestEvent] = useState<StreamEvent | null>(null);
  
  // Use ref for socket to persist across renders without re-triggering
  const socketRef = useRef<ReconnectingWebSocket | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    // Use environment variable or fallback to localhost
    // Note: In Next.js client-side, we use process.env.NEXT_PUBLIC_* 
    const wsBaseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const wsUrl = `${wsBaseUrl}/ws/${sessionId}`;
    
    console.log(`Connecting to WebSocket: ${wsUrl}`);
    const rws = new ReconnectingWebSocket(wsUrl);
    socketRef.current = rws;

    rws.addEventListener('open', () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    });

    rws.addEventListener('close', () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    });

    rws.addEventListener('message', (event) => {
      try {
        const wire: WireEvent = JSON.parse(event.data);
        const parsedEvent = normalizeEvent(wire);
        if (!parsedEvent) return;
        
        setLatestEvent(parsedEvent);
        setEvents((prev) => {
          const newEvents = [...prev, parsedEvent];
          // Keep max 500 events to prevent memory leaks
          return newEvents.length > 500 ? newEvents.slice(newEvents.length - 500) : newEvents;
        });
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    });

    return () => {
      // Clean up connection when component unmounts or sessionId changes
      rws.close();
      socketRef.current = null;
    };
  }, [sessionId]);

  return { events, isConnected, latestEvent };
};

