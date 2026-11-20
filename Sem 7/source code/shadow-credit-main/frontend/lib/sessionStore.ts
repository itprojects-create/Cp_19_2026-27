import { create } from 'zustand';
import { SessionData } from '../components/panels/AssessmentPanel';
import { StreamEvent } from '../hooks/useWebSocket';
import { ProvenanceData } from '../components/drawers/ProvenanceDrawer';
import { ClarificationData } from '../components/modals/ClarificationModal';

interface SessionState {
  sessionId: string | null;
  sessionData: SessionData;
  events: StreamEvent[];
  isConnected: boolean;
  privacyBlur: boolean;
  provenanceState: {
    isOpen: boolean;
    fieldName: string;
    fieldValue: unknown;
    agentId: string;
    data: ProvenanceData | undefined;
  };
  clarificationState: ClarificationData | null;

  // Actions
  setSessionId: (id: string) => void;
  setSessionData: (data: Partial<SessionData>) => void;
  addEvent: (event: StreamEvent) => void;
  setIsConnected: (connected: boolean) => void;
  setPrivacyBlur: (blur: boolean) => void;
  openProvenance: (fieldName: string, value: unknown, agentId: string, data?: ProvenanceData) => void;
  closeProvenance: () => void;
  setClarification: (data: ClarificationData | null) => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  sessionId: null,
  sessionData: {},
  events: [],
  isConnected: false,
  privacyBlur: false,
  provenanceState: {
    isOpen: false,
    fieldName: '',
    fieldValue: null,
    agentId: '',
    data: undefined,
  },
  clarificationState: null,

  setSessionId: (id) => set({ sessionId: id }),
  
  setSessionData: (data) => set((state) => ({
    sessionData: { ...state.sessionData, ...data }
  })),

  addEvent: (event) => set((state) => {
    const newEvents = [...state.events, event];
    // Keep last 500 events
    if (newEvents.length > 500) newEvents.shift();
    return { events: newEvents };
  }),

  setIsConnected: (connected) => set({ isConnected: connected }),
  
  setPrivacyBlur: (blur) => set({ privacyBlur: blur }),

  openProvenance: (fieldName, fieldValue, agentId, data) => set({
    provenanceState: {
      isOpen: true,
      fieldName,
      fieldValue,
      agentId,
      data
    }
  }),

  closeProvenance: () => set((state) => ({
    provenanceState: { ...state.provenanceState, isOpen: false }
  })),

  setClarification: (data) => set({ clarificationState: data }),
}));
