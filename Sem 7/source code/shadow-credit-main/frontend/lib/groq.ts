/**
 * Groq API Interfaces
 * 
 * These types reflect the response shapes returned by the backend's Groq integration.
 * The frontend never calls Groq directly; all calls are proxied through the backend.
 */

export interface GroqNarrativeResponse {
  narrative: string;
  model: string;
  tokensUsed: number;
  latencyMs: number;
}

export interface GroqClassification {
  lineId: number;
  classification: string;
  amount: number | null;
  counterparty: string | null;
  date: string | null; // ISO Date string
  confidence: number;
}

export interface GroqEntityExtraction {
  entityType: 'PERSON' | 'ORG' | 'LOCATION' | 'DATE' | 'MONEY';
  text: string;
  confidence: number;
  startIndex: number;
  endIndex: number;
}

export interface GroqComplianceCheck {
  checkId: string;
  status: 'PASS' | 'FAIL' | 'WARN';
  reasoning: string;
  evidence: string[]; // Quotes from source documents
}
