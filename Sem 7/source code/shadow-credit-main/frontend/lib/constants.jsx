export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const WS_BASE_URL  = process.env.NEXT_PUBLIC_WS_URL  || 'ws://localhost:8000';
export const API_PREFIX   = '/api/v1';

export const AGENT_LABELS = {
  identity_verifier:  'Identity',
  whatsapp_analyzer:  'WhatsApp',
  upi_analyzer:       'UPI',
  bill_analyzer:      'Bills',
  cash_flow_analyzer: 'Cash Flow',
  risk_assessor:      'Risk',
  credit_scorer:      'Scorer',
};

export const AGENT_REGISTRY = {
  identity_verifier: {
    id: 'identity_verifier',
    name: 'Identity',
    description: 'Verifies Aadhaar, PAN & business registration',
  },
  whatsapp_analyzer: {
    id: 'whatsapp_analyzer',
    name: 'WhatsApp',
    description: 'Extracts payment confirmations from chat exports',
  },
  upi_analyzer: {
    id: 'upi_analyzer',
    name: 'UPI',
    description: 'Analyzes transaction patterns & cash flow',
  },
  bill_analyzer: {
    id: 'bill_analyzer',
    name: 'Bills',
    description: 'Validates utility payments & address proof',
  },
  cash_flow_analyzer: {
    id: 'cash_flow_analyzer',
    name: 'Cash Flow',
    description: 'Computes income regularity & seasonality',
  },
  risk_assessor: {
    id: 'risk_assessor',
    name: 'Risk',
    description: 'Detects fraud signals & concentration risk',
  },
  credit_scorer: {
    id: 'credit_scorer',
    name: 'Scorer',
    description: 'Produces final credit limit & confidence score',
  },
  // Numbered aliases for backward compatibility
  agent_00: { id: 'agent_00', name: 'Identity', description: 'Verifies business identity' },
  agent_01: { id: 'agent_01', name: 'WhatsApp', description: 'Extracts payment confirmations' },
  agent_02: { id: 'agent_02', name: 'UPI', description: 'Analyzes UPI transactions' },
  agent_02b: { id: 'agent_02b', name: 'Bills', description: 'Validates utility payments' },
  agent_03: { id: 'agent_03', name: 'Cash Flow', description: 'Computes income regularity' },
  agent_04: { id: 'agent_04', name: 'Risk', description: 'Detects fraud signals' },
  agent_05: { id: 'agent_05', name: 'Compliance', description: 'Regulatory checks' },
  agent_07: { id: 'agent_07', name: 'Scorer', description: 'Produces credit limit' },
};

export const STATUS_COLORS = {
  PENDING:    'pending',
  PROCESSING: 'processing',
  ANALYZING:  'processing',
  COMPLETE:   'complete',
  COMPLETED:  'complete',
  FAILED:     'failed',
  APPROVED:   'approved',
  DECLINED:   'declined',
  REVIEW:     'review',
};

export const DEMO_SESSION_ID = 'phase3-test';
