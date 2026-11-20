import { useState, useEffect } from 'react';
import { api, ScenarioResult } from '../lib/api';
import { SessionData } from '../components/panels/AssessmentPanel';

export type ScenarioType = 'current' | 'gst' | 'aa_consent' | 'gst_aa';

interface UseScenarioReturn {
  activeScenario: ScenarioType;
  setActiveScenario: (scenario: ScenarioType) => void;
  scenarioResult: ScenarioResult | null;
  loading: boolean;
  error: string | null;
}

export const useScenario = (sessionId: string, initialData?: SessionData): UseScenarioReturn => {
  const [activeScenario, setActiveScenarioState] = useState<ScenarioType>('current');
  const [scenarioResult, setScenarioResult] = useState<ScenarioResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize with current data if available
  useEffect(() => {
    if (initialData?.creditAssessment?.finalLimit) {
      setScenarioResult({
        limit: initialData.creditAssessment.finalLimit,
        delta: 0,
        steps: []
      });
    }
  }, [initialData]);

  const setActiveScenario = async (scenario: ScenarioType) => {
    setActiveScenarioState(scenario);
    
    // If switching back to current, reset to initial if we have it, or fetch
    if (scenario === 'current' && initialData?.creditAssessment) {
      setScenarioResult({
        limit: initialData.creditAssessment.finalLimit,
        delta: 0,
        steps: []
      });
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const { data } = await api.applyScenario(sessionId, scenario);
      setScenarioResult(data);
    } catch (err) {
      console.error('Failed to apply scenario:', err);
      setError('Failed to calculate scenario');
      // Revert to previous valid state or keep error
    } finally {
      setLoading(false);
    }
  };

  return {
    activeScenario,
    setActiveScenario,
    scenarioResult,
    loading,
    error
  };
};
