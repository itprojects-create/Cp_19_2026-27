# Shadow Credit — Phase 3 Part 1 Complete

## Processing Screen: WebSocket Agent Stream + Live Progress

**Completed:** March 26, 2026  
**Status:** ✅ All 6 files created and verified

---

## 📋 Overview

Phase 3 Part 1 builds the **Processing Screen** — the most critical 90 seconds of the applicant's experience. After submitting consent on `/apply`, users land on `/apply/processing?session=ID` where they watch 7 AI agents analyze their business in real-time via WebSocket.

The design aesthetic is **"Bloomberg terminal crossed with surgery theater"** — precision, tension, and resolution. Every agent activation feels meaningful, every log line feels real.

---

## 🗂️ Files Created

```
frontend/
├── app/
│   └── apply/
│       └── processing/
│           ├── page.jsx                 ← Main page component (347 lines)
│           └── processing.module.css    ← Page styles (310 lines)
└── components/
    └── processing/
        ├── AgentNode.jsx                ← Agent card component (95 lines)
        ├── AgentNode.module.css         ← Agent card styles (258 lines)
        ├── LogStream.jsx                ← Log stream component (88 lines)
        └── LogStream.module.css         ← Log stream styles (175 lines)
```

**Also modified:**
- `frontend/lib/api.jsx` — Added 3 wrapper methods for processing screen

---

## 🎨 Screen Layout

```
┌────────────────────────────────────────────────────────────────┐
│  TOP BAR (48px height)                                         │
│  ┌──────────┐    ┌─────────────────────────┐    ┌──────────┐  │
│  │SHADOW    │    │ Analyzing your business │    │ ● 01:23  │  │
│  │CREDIT    │    │ ...                     │    │          │  │
│  └──────────┘    └─────────────────────────┘    └──────────┘  │
│   wordmark           status (animated)           timer        │
└────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────┐
│  RETRY BANNER (shown when connection interrupted)              │
│  "Connection interrupted — retrying (2/3)..."                  │
└────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────┐
│  AGENT SECTION                                                 │
│                                                                │
│  "3 / 7 agents complete"    "● 2 running"                     │
│                                                                │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                  │
│  │  📍    │ │  🔍    │ │  💬    │ │  📈    │                  │
│  │        │ │   ⏳   │ │   ✓    │ │        │                  │
│  │ag-00   │ │ag-01   │ │ag-02   │ │ag-03   │                  │
│  │Biz     │ │OCR     │ │Chat    │ │UPI     │                  │
│  │Verify  │ │Scan    │ │Parse   │ │Flow    │                  │
│  └────────┘ └────────┘ └────────┘ └────────┘                  │
│                                                                │
│  ┌────────┐ ┌────────┐ ┌────────┐                             │
│  │  📊    │ │  🔀    │ │  📄    │                             │
│  │        │ │        │ │        │                             │
│  │ag-04   │ │ag-05   │ │ag-06   │                             │
│  │Seasonal│ │Recon-  │ │Credit  │                             │
│  │        │ │cile    │ │Memo    │                             │
│  └────────┘ └────────┘ └────────┘                             │
└────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────┐
│  LOG SECTION                                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ LIVE LOG          42 entries         [STREAM LIVE]       │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ [12:24:15] AGT ag-02 WhatsApp analysis complete          │ │
│  │ [12:24:12] AGT ag-02 Processing 847 messages...          │ │
│  │ [12:24:10] INF      Starting document verification       │ │
│  │ [12:24:08] AGT ag-01 OCR extraction complete             │ │
│  │ [12:24:05] AGT ag-01 Found 3 UPI screenshots             │ │
│  │ [12:24:02] INF      WebSocket connected — stream live    │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

---

## 🤖 The 7 AI Agents

| Agent ID | Icon | Label | Purpose |
|----------|------|-------|---------|
| `agent_00` | MapPin | Biz Verify | Business location verification via Maps |
| `agent_01` | FileSearch | OCR Scan | Document OCR extraction |
| `agent_02` | MessageSquare | Chat Parse | WhatsApp export analysis |
| `agent_03` | TrendingUp | UPI Flow | UPI transaction flow analysis |
| `agent_04` | BarChart2 | Seasonal | Seasonal business intelligence |
| `agent_05` | GitMerge | Reconcile | Data reconciliation engine |
| `agent_06` | FileText | Credit Memo | Final credit memo generation |

---

## 🎭 Agent Card States

### 1. **Idle** (default)
- Faded appearance (55% opacity)
- Dim border: `rgba(255,255,255,0.07)`
- Dim icon color: `rgba(255,255,255,0.25)`

### 2. **Running**
- Full opacity
- Pulsing indigo border animation (`borderPulse` keyframes)
- Animated glow ring expanding outward (`ringExpand` keyframes)
- Spinning loader icon in top-right badge
- Bright icon and label colors

### 3. **Paused** (during clarification)
- Amber/warning border pulse (`pauseBorder` keyframes)
- Pause icon (two vertical bars) with blink animation
- Shows when clarification modal is open

### 4. **Complete**
- Green border: `rgba(34,197,94,0.45)`
- Green background wash: `rgba(34,197,94,0.06)`
- Green checkmark badge
- Green icon color

### 5. **Error**
- Red border: `rgba(239,68,68,0.45)`
- Red background wash: `rgba(239,68,68,0.06)`
- Red X badge
- Red icon color

---

## 📜 Log Stream Design

### Format
```
[HH:MM:SS] TAG agent-id Message text here...
```

### Level Tags & Colors
| Level | Tag | Color |
|-------|-----|-------|
| INFO | INF | `rgba(255,255,255,0.42)` (muted gray) |
| WARN | WRN | `rgba(245,158,11,0.75)` (amber) |
| ERROR | ERR | `rgba(239,68,68,0.8)` (red) |
| AGENT_START | AGT | `rgba(99,102,241,0.85)` (indigo) |
| AGENT_COMPLETE | AGT | `rgba(34,197,94,0.85)` (green) |

### Features
- Newest entries appear at top
- Max 120 entries stored (oldest discarded)
- Fade-in animation on new entries (`logEntry` keyframes)
- Hover highlight on lines
- Custom thin scrollbar
- Empty state: blinking cursor + "Waiting for analysis stream..."

---

## 🔌 WebSocket Integration

### Connection Flow
1. Page mounts → read `session` from URL query
2. If no session → redirect to `/apply`
3. Call `api.runAnalysis(sessionId)` to start pipeline
4. Connect WebSocket: `ws://localhost:8000/ws/{session_id}`

### Event Types Handled

```javascript
// Agent lifecycle
{ type: "AGENT_START",    agent_id: "agent_01", message: "..." }
{ type: "AGENT_COMPLETE", agent_id: "agent_01", message: "..." }
{ type: "AGENT_ERROR",    agent_id: "agent_01", message: "..." }

// General logs
{ type: "LOG", message: "...", level: "INFO" | "WARN" | "ERROR" }

// Clarification request
{ type: "CLARIFICATION_NEEDED", question: "...", clarification_id: "clr_xxx" }

// Completion
{ type: "ASSESSMENT_COMPLETE", credit_limit: 105000, grade: "B+" }
{ type: "SESSION_COMPLETE" }
```

### Reconnection Logic
- On connection error: retry up to 3 times
- 2 second delay between retries
- Show retry banner during reconnection
- After 3 failures: show failed banner (user can safely close tab)

---

## ❓ Clarification Modal

When `CLARIFICATION_NEEDED` event fires:

1. **Modal appears** with backdrop blur (72% black, 12px blur)
2. **Running agents pause** — show amber border pulse
3. **Modal content:**
   - Eyebrow: "Agent needs clarification" (monospace, indigo)
   - Question text (large, readable)
   - Textarea: "Type your answer here..."
   - Submit button: "Send Answer →"
4. **On submit:** POST to `/api/v1/sessions/{id}/clarify`
5. **On success:** Modal closes, agents resume
6. **On error:** Show inline error, keep modal open

---

## ✅ Completion Overlay

When `ASSESSMENT_COMPLETE` or `SESSION_COMPLETE` fires:

1. Dark overlay appears (85% black, 16px blur)
2. Green checkmark icon with pop-in animation
3. Text: "Analysis complete. Preparing your result..."
4. After 1200ms delay → redirect to `/apply/result?session={id}`

---

## 📱 Responsive Design

### Desktop (> 640px)
- Agent cards: 120px × 108px
- 7 cards in horizontal row (wraps to 2 rows)
- Full wordmark visible
- Log font: 12px

### Mobile (≤ 640px)
- Agent cards: 88px × 80px
- Wordmark hidden
- Log font: 11px
- Reduced padding throughout

---

## 🔧 API Methods Added

Added to `frontend/lib/api.jsx`:

```javascript
// Start the analysis pipeline
api.runAnalysis = async (sessionId) => {
  return sessionApi.analyze(sessionId)
}

// Get WebSocket URL
api.wsUrl = (sessionId) => {
  const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
  return `${WS_BASE}/ws/${sessionId}`
}

// Submit clarification answer
api.submitClarification = async (sessionId, payload) => {
  const result = await api.post(`/sessions/${sessionId}/clarify`, payload)
  return result.data
}
```

---

## 🧪 State Management

```javascript
// Agent states: idle | running | complete | error
const [agentStates, setAgentStates] = useState({
  agent_00: 'idle', agent_01: 'idle', agent_02: 'idle',
  agent_03: 'idle', agent_04: 'idle', agent_05: 'idle', agent_06: 'idle',
});

// Log entries (newest first, max 120)
const [logs, setLogs] = useState([]);

// Clarification modal
const [clarification, setClarification] = useState(null);
const [clarificationAnswer, setAnswer] = useState('');
const [clarLoading, setClarLoading] = useState(false);
const [clarError, setClarError] = useState('');

// Timer and connection
const [elapsed, setElapsed] = useState(0);  // seconds
const [wsStatus, setWsStatus] = useState('connecting');
const [retryCount, setRetryCount] = useState(0);
const [completed, setCompleted] = useState(false);

// Banners
const [retryBanner, setRetryBanner] = useState(false);
const [failedBanner, setFailedBanner] = useState(false);
```

---

## 🎬 CSS Animations

| Animation | Duration | Purpose |
|-----------|----------|---------|
| `dotPulse` | 1.4s | Animated ellipsis in status |
| `timerBlink` | 1s | Timer dot blink |
| `borderPulse` | 2.2s | Running agent border glow |
| `ringExpand` | 2s | Running agent outer glow ring |
| `pauseBorder` | 1.4s | Paused agent amber border |
| `pausePulse` | 1.2s | Pause icon opacity pulse |
| `spin` | 750ms | Loader spinner rotation |
| `logEntry` | 200ms | Log line fade-in slide |
| `cursorBlink` | 1s | Empty state cursor blink |
| `backdropIn` | 220ms | Modal backdrop fade |
| `modalIn` | 260ms | Modal slide-up entrance |
| `popIn` | 400ms | Completion checkmark pop |
| `fadeUp` | 400ms | Completion text fade |

---

## ✅ Verification Checklist

### Step 1: Folder Check
```bash
ls frontend/app/apply/processing/
# Expected: page.jsx  processing.module.css

ls frontend/components/processing/
# Expected: AgentNode.jsx  AgentNode.module.css
#           LogStream.jsx  LogStream.module.css
```

### Step 2: Build Check
```bash
cd frontend && npm run dev
# Expected: zero red errors
```

### Step 3: Manual Flow Test
1. Open http://localhost:3000/apply
2. Fill Step 1 (any name, city, business type)
3. Skip Steps 2, 3, 4 (optional uploads)
4. Check consent on Step 5 → click "Start Analysis"
5. Land on: http://localhost:3000/apply/processing?session=SESSION_ID

**Verify on screen:**
- [ ] Top bar: wordmark left, animated dots center, timer ticking right
- [ ] Timer increments every second (MM:SS format)
- [ ] 7 AgentNode cards rendered in grid
- [ ] All start in idle state (faded)
- [ ] Log shows: "WebSocket connected — analysis stream live"
- [ ] WS indicator reads "STREAM LIVE" in green
- [ ] Agents transition: idle → running (pulsing border + spinner)
- [ ] Completed agents: green border + checkmark
- [ ] New log lines animate in from top
- [ ] Color-coded: indigo=start, green=complete, amber=warn, red=error

**If CLARIFICATION_NEEDED fires:**
- [ ] Modal appears with backdrop blur
- [ ] Running agents show amber paused border
- [ ] Question is readable
- [ ] Can type answer and submit
- [ ] Modal closes on success

**On completion:**
- [ ] Green overlay with checkmark
- [ ] Redirects to /apply/result after 1.2s

---

## 🔗 Navigation Flow

```
/apply (Steps 1-5)
    ↓ consent submitted
/apply/processing?session=ID
    ↓ analysis complete (1.2s delay)
/apply/result?session=ID (Phase 4)
```

---

## 📝 Notes

- Screen is **always dark** — no light mode toggle on processing screen
- Background: `#0A0A0F` (nearly black with slight blue cast)
- Max log entries: 120 (prevents memory issues on long sessions)
- WebSocket auto-reconnects up to 3 times with 2s delays
- Timer continues even during clarification pauses

---

## 🚀 Next Phase

**Phase 3 Part 2** will add:
- More detailed clarification modal logic
- Enhanced timer states
- Additional redirect conditions
- Error recovery improvements

**Phase 4** will build the Result Screen at `/apply/result`.
