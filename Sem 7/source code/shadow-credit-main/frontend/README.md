# Shadow Credit — Frontend Application

## Overview

Mobile-first loan application interface for Indian MSME owners. Built with Next.js 14, TypeScript, and CSS Modules.

## Design Principles

1. **WhatsApp-level clarity** — Every action is obvious
2. **Google Pay-level trust** — Security messaging at every step
3. **Duolingo-level simplicity** — Linear flow, no confusion
4. **Light mode only** — Optimized for outdoor Android usage
5. **48px minimum touch targets** — Accessible on all devices

## Tech Stack

- Next.js 14 (App Router)
- TypeScript
- CSS Modules (no Tailwind — full design control)
- Plus Jakarta Sans font (warm, readable on low-DPI screens)

## Project Structure

```
frontend/
├── app/
│   ├── apply/
│   │   ├── page.tsx              # Step orchestrator
│   │   ├── layout.tsx            # Header + progress bar
│   │   └── steps/
│   │       ├── Step1Identity.tsx
│   │       ├── Step2Upload.tsx   # TODO
│   │       ├── Step3Maps.tsx     # TODO
│   │       ├── Step4Consent.tsx  # TODO
│   │       └── Step5Processing.tsx # TODO
│   └── globals.css
├── components/
│   ├── ui/                       # Atomic components
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── UploadCard.tsx
│   │   ├── Checkbox.tsx
│   │   ├── Badge.tsx
│   │   ├── ProgressBar.tsx
│   │   └── BottomCTA.tsx
│   └── apply/                    # Feature components
│       └── BusinessTypeChips.tsx
├── hooks/
│   ├── useApplySession.ts        # TODO
│   ├── useWebSocket.ts           # TODO
│   └── useFileUpload.ts          # TODO
├── lib/
│   ├── api.ts                    # All API calls
│   ├── formatters.ts             # Currency, dates
│   └── animations.ts             # Count-up animation
└── styles/
    └── tokens.css                # Design system tokens
```

## Design System

### Colors

- **Accent**: `#1D6B4E` (deep forest green — trust, prosperity)
- **Background**: `#FAFAF9` (warm off-white)
- **Surface**: `#FFFFFF` (cards, inputs)
- **Text Primary**: `#1A1916` (near-black, warm)
- **Error**: `#B33A2E`
- **Warning**: `#92521E`

### Typography

- **Font**: Plus Jakarta Sans (Google Fonts)
- **Hero**: 28px / 700
- **Title**: 20px / 600
- **Body**: 15px / 400
- **Label**: 13px / 500
- **Caption**: 12px / 400

### Spacing

8px base grid: 4px, 8px, 12px, 16px, 20px, 24px, 32px, 40px, 48px

### Border Radius

- Small: 8px
- Medium: 12px (buttons, inputs)
- Large: 16px (cards)
- XL: 24px (modals)
- Full: 9999px (pills)

## Components

### Button

```tsx
<Button variant="primary" loading={false} fullWidth>
  Continue
</Button>
```

Variants: `primary`, `secondary`, `ghost`

### Input

```tsx
<Input
  label="Shop Name"
  placeholder="e.g. Suresh Kirana Store"
  error="This field is required"
  leftIcon={<SearchIcon />}
/>
```

### UploadCard

```tsx
<UploadCard
  icon="💬"
  title="WhatsApp Business Chat"
  subtitle="Your chats with customers"
  badge={{ text: '+₹15k', variant: 'success' }}
  uploaded={false}
  onUpload={handleUpload}
/>
```

### Checkbox

```tsx
<Checkbox
  label="I allow analysis of my documents"
  checked={consent}
  onChange={setConsent}
/>
```

## API Integration

All API calls in `lib/api.ts`:

```ts
import { createSession, uploadFile, submitApplication } from '@/lib/api';

// Create session
const session = await createSession();

// Upload file
await uploadFile(sessionId, file, 'whatsapp');

// Submit application
await submitApplication(sessionId, consents);
```

## Animations

Smooth, subtle, production-grade:

- **Button press**: `scale(0.97)` on active
- **Step transitions**: Slide left/right (250ms)
- **Progress bar**: Smooth fill (400ms ease-out)
- **Amount count-up**: 1200ms with easeOutCubic

## Accessibility

- ✅ WCAG AA contrast ratios
- ✅ 48px minimum touch targets
- ✅ Keyboard navigation
- ✅ Screen reader labels
- ✅ Reduced motion support

## Mobile Optimizations

- No horizontal scroll on 390px viewport
- Safe area insets for iPhone notch
- Viewport height units (not 100vh)
- Backdrop blur on fixed header
- Touch-friendly spacing

## TODO: Remaining Steps

### Step 2: Document Upload
- WhatsApp export upload
- UPI screenshot upload (multiple)
- Electricity bill upload
- Bank SMS upload
- "How to export?" expandable guides

### Step 3: Google Maps Verification
- Live search with debounce
- Result cards with ratings
- "Not my shop" fallback
- Skip option with reassurance

### Step 4: Consent
- Trust badges
- English + Hindi text
- 3 checkboxes
- Submit button

### Step 5: Processing & Result
- 7-segment circular progress
- Live WebSocket updates
- Amount count-up animation
- Download/Share PDF

## Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Development

```bash
npm install
npm run dev
```

Open http://localhost:3000/apply

## Production Checklist

- [ ] All touch targets ≥ 48px
- [ ] No horizontal scroll on 390px
- [ ] WCAG AA contrast
- [ ] Keyboard doesn't jump inputs
- [ ] Back button works
- [ ] Android file picker works
- [ ] Hindi text renders correctly
- [ ] Count-up animation smooth
- [ ] Loading states on all async
- [ ] Error states on all async
- [ ] Session ID in sessionStorage
- [ ] Offline state handled

## The Final Test

Show this to a 55-year-old WhatsApp user. If they complete the flow without asking questions, you've succeeded.
