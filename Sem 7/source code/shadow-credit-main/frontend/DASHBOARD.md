# Shadow Credit — RM Dashboard

## Overview

Professional financial tool for Bank Relationship Managers. Dark mode interface optimized for 8-hour daily usage. Processes 20 credit cases per day with speed, clarity, and trust.

## Design Philosophy

**NOT a startup landing page. NOT a SaaS marketing site.**

This is a professional financial tool. Reference standards:
- **Linear**: Information density
- **Notion**: Hierarchy
- **Stripe Dashboard**: Data clarity
- **Vercel**: Dark mode craft

## Design System

### Dark Mode Color Palette

**Backgrounds (layered depth)**
- Base: `#0D1117` (deepest canvas)
- Surface: `#161B22` (panels, sidebar)
- Elevated: `#1C2128` (cards, table rows)
- Overlay: `#21262D` (hover states)

**Accent**
- Primary: `#1F6FEB` (electric blue — GitHub's trusted action color)
- Subtle: `#1F6FEB1A` (tinted backgrounds)
- Hover: `#388BFD`

**Status Colors**
- Success: `#3FB950` (HIGH confidence, complete)
- Warning: `#D29922` (MEDIUM confidence, needs review)
- Error: `#F85149` (LOW confidence, error)
- Neutral: `#8B949E` (processing, pending)

### Typography

**Font Stack**
- UI: Inter (14px base — power-user density)
- Mono: JetBrains Mono (log stream only)
- Serif: Georgia (narrative section only)

**Scale**
- XS: 11px / 500 (labels, badges)
- SM: 12px / 400 (metadata)
- Base: 14px / 400 (default data)
- MD: 15px / 400 (body content)
- LG: 18px / 600 (section headings)
- XL: 24px / 700 (panel headers)
- Hero: 36px / 700 (credit limit display)

### Spacing

8px base grid: 4px, 8px, 12px, 16px, 20px, 24px, 32px, 40px, 48px

### Components

**Button (Desktop)**
- Height: 32px (smaller than mobile)
- Primary: Electric blue background
- Secondary: Transparent with border
- Ghost: No background, text only
- Danger: Red border on hover

**Table Row**
- Height: 44px
- Hover: Overlay background
- Selected: Accent subtle background + left border

**Status Badge**
- Height: 20px
- Uppercase, 11px, 600 weight
- Variants: NEW, PROCESSING, COMPLETE, CLARIFICATION

**Confidence Badge**
- Inline pill with colored dot
- HIGH (≥0.85): Green
- MEDIUM (0.50-0.85): Amber
- LOW (<0.50): Red
- Clickable → opens ProvenanceViewer

## Layout Architecture

### Global Shell

```
┌─────────────────────────────────────────────┐
│ Top Bar (48px)                              │
├──────────┬──────────────────────────────────┤
│          │                                   │
│ Sidebar  │ Main Content                      │
│ (220px)  │ (flex-1, scrollable)              │
│          │                                   │
└──────────┴──────────────────────────────────┘
```

### Top Bar
- Left: SC monogram + "Shadow Credit"
- Center: Current page title
- Right: "New Assessment +" button + connection status dot

### Sidebar
- Navigation items (40px height each)
- Active: Overlay background + left accent border
- Footer: Version number

## Case Queue (/dashboard)

### Header
- Title: "Cases"
- Search input + filter dropdown
- "New Assessment +" button

### Filter Bar
- Tabs: All, New, Processing, Ready, Requires Input
- Active tab: Accent underline
- Live count badges from WebSocket

### Table Columns
1. Case ID (80px) — monospace, muted
2. Applicant (200px) — 14px, 500 weight
3. Business (140px) — 13px, secondary
4. Location (160px) — 13px, secondary
5. Submitted (100px) — relative time ("2 hours ago")
6. Status (120px) — StatusBadge component
7. Score (80px) — monospace, color-coded
8. Limit (100px) — tabular-nums, ₹1,05,000 format
9. Action (40px) — "Review →" on hover

### Live Updates
- New sessions slide in from top
- Highlighted in accent-subtle for 3 seconds
- WebSocket connection status in top bar

### Empty State
- Centered clipboard icon
- "No cases yet" title
- "Start a New Assessment" button

## Session View (/dashboard/[id])

### Three-Panel Layout

```
┌────────────────────────────────────────────────────────────┐
│ Session Top Bar (44px)                                     │
├──────────┬─────────────────────────┬───────────────────────┤
│          │                         │                       │
│ Evidence │   Agent Activity        │   Assessment          │
│ (300px)  │   (flex-1)              │   (380px)             │
│          │                         │                       │
│ Scroll   │   Scroll                │   Scroll              │
│          │                         │                       │
└──────────┴─────────────────────────┴───────────────────────┘
```

### Session Top Bar
- Left: ← Back + Case ID
- Center: Applicant + business + location
- Right: Status badge + stopwatch + "▶ Run Analysis"

### Left Panel — Evidence
- Header: "Evidence" + source count
- Artifact cards (thumbnails, confidence bars)
- Google Maps card (static image + details)
- Privacy toggle (bottom, sticky): "Blur PII"

### Center Panel — Agent Activity
- Background: `#090D14` (darker — terminal feel)
- Agent graph (top 140px, fixed)
  - Horizontal node flow
  - Supervisor node below (40px, purple glow)
  - Animated edges during data flow
- Log stream (remaining height, scrollable)
  - Monospace, 12px
  - Color-coded by agent
  - Supervisor lines indented + purple
  - Auto-scroll with pause on user scroll

### Right Panel — Assessment
- Independently scrollable
- Progressive build (sections appear as agents complete)

**Sections:**
1. Evidence Summary (after Phase A)
2. Financial Summary (after Agent 05)
3. CreditWarmthScore™ (after Agent 04)
   - Circular gauge + grade badge
   - 6+1 signal bars with SHAP values
4. Credit Assessment (after Agent 07)
   - Formula breakdown (clickable factors)
   - Credit limit display (36px, animated count-up)
   - AI narrative (serif font, 1.8 line-height)
   - RM decision buttons
   - Export buttons (PDF, Passport, JSON)
5. Compliance (after Agent 06)
   - 12-item grid with status icons
6. Scenario Analysis (always visible after complete)
   - 4 tabs: Current, +GST, +AA, +GST & AA
   - Animated delta on tab switch

## Agent Colors

- Supervisor: `#7C3AED` (purple — visually distinctive)
- Maps: `#1F6FEB` (blue)
- OCR: `#0EA5E9` (sky)
- WhatsApp: `#10B981` (emerald)
- SMS: `#6EE7B7` (light emerald)
- Khata: `#F59E0B` (amber)
- Scoring: `#8B5CF6` (violet)
- Reconciliation: `#EF4444` (red)
- Compliance: `#F97316` (orange)
- Report: `#3B82F6` (blue)

## Clarification Modal

**Trigger**: CLARIFICATION_REQUIRED WebSocket event

**Behavior**: Full-screen overlay, cannot close without answering

**Design**:
- Backdrop: rgba(0,0,0,0.75) + blur(4px)
- Modal: 480px width, centered
- Header: ◈ SUPERVISOR AGENT (purple, uppercase)
- Question: 18px, 500 weight (max 20 words)
- Answer buttons: Full width, 44px height
- Footer: "Your response will resume the AI pipeline"

## Provenance Viewer

**Trigger**: Clicking any field value with ConfidenceBadge

**Type**: Side drawer, slides in from right (360px)

**Sections**:
1. Extracted Value (large display)
2. Source Trail (vertical timeline with dots)
3. Artifact Preview (thumbnail + highlight box)
4. Audit Trail Link

## Animations

**USE animation for:**
- Agent node pulse (proves it's live)
- Data flow edges (proves data moving)
- Section entrance (slide up + fade, 200ms)
- Credit limit count-up (800ms, easeOutQuart)
- Signal bar fill (600ms, ease-out)
- New case row entrance (slide from top, 200ms)

**DO NOT use animation for:**
- Hover states (color/border only)
- Text changes (instant)
- Loading spinners > 16px
- Page transitions
- Scroll effects

## Quality Checklist

- [ ] All three panels visible on 1280px width
- [ ] All three panels independently scrollable
- [ ] WebSocket reconnects automatically
- [ ] Privacy blur applies to all panels
- [ ] Credit limit count-up smooth (60fps)
- [ ] Agent graph nodes pulse during execution
- [ ] Log stream auto-scrolls with pause
- [ ] Clarification modal cannot be dismissed
- [ ] Provenance drawer no layout shift
- [ ] Indian number notation (₹1,05,000)
- [ ] Serif font in narrative section
- [ ] Scenario tabs animate credit limit
- [ ] Export buttons show loading state
- [ ] Status badges update real-time
- [ ] New cases appear without refresh

## The Final Test

A bank credit officer with 10 years of experience should sit down, open the dashboard, and within 60 seconds understand:

1. What a case is, how to open it
2. Where the evidence is, whether it's trustworthy
3. What the AI concluded and why
4. How to answer the AI's clarification question
5. How to get the PDF

If they are confused at any point, the design has failed.

If they feel it was built by a company that takes credit seriously — not students at a hackathon — you have won.

## Development

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000/dashboard

## Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

## File Structure

```
frontend/
├── app/
│   └── dashboard/
│       ├── page.tsx              # Case queue
│       ├── layout.tsx            # Shell (sidebar, topbar)
│       └── [sessionId]/
│           └── page.tsx          # Three-panel session view
├── components/
│   ├── ui/                       # Atomic components
│   │   ├── DataRow.tsx
│   │   ├── SignalBar.tsx
│   │   ├── ConfidenceBadge.tsx
│   │   └── Card.tsx
│   ├── layout/
│   │   ├── Sidebar.tsx
│   │   ├── TopBar.tsx
│   │   └── SessionTopBar.tsx
│   ├── panels/
│   │   ├── EvidencePanel.tsx
│   │   ├── LogStreamPanel.tsx
│   │   └── AssessmentPanel.tsx
│   ├── ClarificationModal.tsx
│   ├── ProvenanceDrawer.tsx
│   └── AgentGraph.tsx
├── hooks/
│   ├── useWebSocket.ts
│   ├── useSession.ts
│   └── useProvenance.ts
└── styles/
    └── tokens-dark.css
```

## TODO: Remaining Components

- [ ] SessionTopBar component
- [ ] EvidencePanel (left)
- [ ] LogStreamPanel (center) with agent graph
- [ ] AssessmentPanel (right) with progressive sections
- [ ] ClarificationModal
- [ ] ProvenanceDrawer
- [ ] AgentGraph SVG component
- [ ] SignalBar component
- [ ] CreditWarmthGauge component
- [ ] WebSocket hook with reconnection
- [ ] Session data fetching
- [ ] Export PDF/JSON endpoints

## Notes

This is a professional financial tool. Every design decision prioritizes:
1. **Speed** — RMs process 20 cases/day
2. **Clarity** — Financial data must be instantly readable
3. **Trust** — This tool makes ₹10L credit decisions

No gradients. No illustrations. No decorative elements. Data is the design.
