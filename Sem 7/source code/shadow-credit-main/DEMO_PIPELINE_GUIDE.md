# 3-Persona Demo Pipeline - Implementation Complete

## Overview
Implemented a realistic 3-persona mock analysis pipeline for Shadow Credit demos with different business characteristics and outcomes.

## Personas

### 1. **Suresh Kirana Store** (Clean Happy Path)
- **Location**: Sadashiv Peth, Pune
- **Outcome**: Grade A, ₹65,000 limit
- **Characteristics**:
  - Consistent monthly inflow: ₹44,000
  - Warmth score: 0.84
  - All reconciliation checks pass
  - 4 sources verified
- **Demo Duration**: ~45 seconds
- **Use Case**: Show the ideal scenario - all green, smooth approval

### 2. **Meena Fashion House** (Clarification Required) ⭐
- **Location**: Kalyani Nagar, Pune
- **Outcome**: Grade B, ₹38,000 limit
- **Characteristics**:
  - Cash gap detected: ₹18,000 (36%)
  - WhatsApp shows ₹48,000 but UPI only ₹28,000
  - **Pipeline PAUSES mid-stream**
  - Clarification modal fires: "Does your business accept significant cash payments?"
  - RM answers → Pipeline resumes
  - Warmth score: 0.67
- **Demo Duration**: ~55 seconds (includes 8s pause)
- **Use Case**: ⭐ **BEST FOR PRESENTATION** - Shows agentic AI stopping to ask questions

### 3. **Raju Tent & Decoration** (Seasonal Business)
- **Location**: Pimpri, Pune
- **Outcome**: Grade A-, ₹58,000 limit
- **Characteristics**:
  - Seasonal pattern detected (peak Oct-Mar)
  - AI adjusts to annual median automatically
  - Monthly inflow: ₹52,000
  - Warmth score: 0.79
- **Demo Duration**: ~48 seconds
- **Use Case**: Show intelligent pattern recognition and adaptation

## Technical Implementation

### Files Created/Modified

1. **`backend/api/mock_pipeline.py`** (NEW)
   - Complete 3-persona pipeline with realistic agent events
   - Uses event_bus for all communications
   - 7 agents: Maps, OCR, WhatsApp, Warmth, Reconciliation, Compliance, Report

2. **`backend/api/sessions.py`** (MODIFIED)
   - Integrated mock pipeline for demo mode
   - Maps persona_id to mock personas:
     - `persona01_clean` → Suresh
     - `persona02_discrepancy` → Meena
     - `persona03_seasonal` → Raju
   - Real mode still uses SupervisorAgent

3. **`backend/api/websocket.py`** (ALREADY UPDATED)
   - Subscribes to event_bus
   - Streams all agent events to frontend
   - Auto-closes on SESSION_COMPLETE

## Usage

### Frontend Request
```json
POST /api/v1/sessions/{session_id}/analyze
{
  "persona_id": "persona02_discrepancy"  // for Meena
}
```

### Persona Mapping
- `"persona01_clean"` or `null` → **Suresh** (default)
- `"persona02_discrepancy"` → **Meena** (recommended for demos)
- `"persona03_seasonal"` → **Raju**

## Agent Event Timeline (Meena - Most Dramatic)

| Time | Agent | Event | Message |
|------|-------|-------|---------|
| 0s | - | - | WebSocket connects |
| 1.5s | AGENT_00_MAPS | STARTED | Verifying business on Google Maps |
| 4.5s | AGENT_00_MAPS | COMPLETE | 4.2★ rating, 47 reviews |
| 5s | AGENT_01_OCR | STARTED | Reading electricity bill & UPI |
| 9s | AGENT_01_OCR | COMPLETE | 6 UPI transactions extracted |
| 9.5s | AGENT_02_WHATSAPP | STARTED | Parsing WhatsApp chat |
| 15.5s | AGENT_02_WHATSAPP | COMPLETE | HIGH cash payment ratio detected |
| 16s | AGENT_04_WARMTH | STARTED | Computing CreditWarmthScore |
| 20s | AGENT_04_WARMTH | COMPLETE | Score: 0.67, Grade: B |
| 20.5s | AGENT_05_RECON | STARTED | Forensic gap analysis |
| 25.5s | AGENT_05_RECON | PROGRESS | **Gap detected: ₹20,000** |
| 27s | SUPERVISOR | **CLARIFICATION_REQUIRED** | **🛑 PIPELINE PAUSED** |
| 35s | SUPERVISOR | COMPLETE | Pipeline resumed |
| 35.5s | AGENT_06_COMPLIANCE | STARTED | RBI compliance checklist |
| 38.5s | AGENT_06_COMPLIANCE | COMPLETE | 10/12 checks pass |
| 39s | AGENT_07_REPORT | STARTED | Generating reports |
| 43s | AGENT_07_REPORT | COMPLETE | PDF & JSON generated |
| 44s | - | SESSION_COMPLETE | Grade B, ₹38,000 limit |

## Demo Recommendations

**For Judges/Presentations**: Use **Meena (persona02_discrepancy)**
- Shows the AI's reasoning capability
- Dramatic pause at 27 seconds
- Clarification modal is visually impressive
- Demonstrates human-in-the-loop agentic workflow
- Clear before/after when pipeline resumes

**For Quick Demos**: Use **Suresh (persona01_clean)**
- Fast, clean execution
- No pauses or complications
- Shows ideal happy path

**For Technical Audiences**: Use **Raju (persona03_seasonal)**
- Shows pattern recognition
- Demonstrates adaptive algorithms
- More sophisticated than simple approval

## Event Structure

All events follow this schema:
```python
{
  "event_type": "AGENT_STARTED" | "AGENT_COMPLETE" | "SESSION_COMPLETE",
  "session_id": "uuid",
  "timestamp": "ISO8601",
  "data": {
    "agent_id": "AGENT_02_WHATSAPP",
    "status": "STARTED",
    "message": "Human readable message",
    "confidence": 0.84,  # optional
    "latency_ms": 4200   # optional
  }
}
```

## Testing

1. Create a demo session with `demo_mode: true`
2. Call analyze endpoint with desired persona
3. Connect WebSocket to `/ws/{session_id}`
4. Watch events stream in real-time
5. For Meena, modal will appear at ~27 seconds

## Notes

- All personas use realistic Indian business names and locations
- Timing is carefully choreographed for demo impact
- Messages include actual Indian context (MSEDCL, RBI norms, ₹ amounts)
- Confidence scores vary by persona complexity
- Mock pipeline does NOT touch database (safe for demos)
