import { useState, useEffect, useCallback } from 'react';
import { StreamEvent } from './useWebSocket';
import { ClarificationData } from '../components/modals/ClarificationModal';
import { api } from '../lib/api';

interface UseClarificationReturn {
  clarification: ClarificationData | null;
  answer: (clarificationId: string, response: string) => Promise<void>;
}

export const useClarification = (
  sessionId: string, 
  latestEvent: StreamEvent | null
): UseClarificationReturn => {
  const [clarification, setClarification] = useState<ClarificationData | null>(null);

  useEffect(() => {
    if (!latestEvent) return;

    if (latestEvent.eventType === 'CLARIFICATION_REQUIRED' && latestEvent.data) {
      const payload = latestEvent.data as Record<string, unknown>;
      const options = Array.isArray(payload.options) ? payload.options : [];
      setClarification({
        clarificationId: String(payload.clarification_id || payload.clarificationId || ''),
        question: String(payload.question || latestEvent.message || 'Please confirm details'),
        options: options.map((opt) => ({ label: String(opt), value: String(opt) })),
      });
    }
  }, [latestEvent]);

  const answer = useCallback(async (clarificationId: string, response: string) => {
    try {
      await api.answerClarification(sessionId, clarificationId, response);
      setClarification(null);
    } catch (error) {
      console.error('Error submitting clarification:', error);
      // Optional: keep modal open and show error state
    }
  }, [sessionId]);

  return { clarification, answer };
};
