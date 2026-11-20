'use client'
import { Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'

const PERSONA_DATA = {
  meena: {
    name: 'Meena Patil',
    business: 'Meena Fashion House',
    location: 'Kalyani Nagar, Pune',
    type: 'Tailor / Stitching Shop',
    creditgrade: 'B',
    finallimit: 28000,
    warmthscore: 0.54,
    monthlyinflow: 48000,
    sourcesverified: 1,
    gradeColor: '#D29922',
    flags: [
      'Business NOT found at stated location (Google Maps mismatch)',
      'No UPI screenshots — digital income unverified',
      'No electricity bill — address and connection type unknown',
    ],
    nextSteps: 'Upload UPI screenshots and electricity bill to increase limit to ₹65,000+',
    assessmentdate: '27 March 2026',
  },
  suresh: {
    name: 'Suresh Sharma',
    business: 'Mahadev Enterprises',
    location: 'Sadashiv Peth, Pune',
    type: 'Kirana / General Store',
    creditgrade: 'B+',
    finallimit: 52000,
    warmthscore: 0.68,
    monthlyinflow: 70500,
    sourcesverified: 2,
    gradeColor: '#1F6FEB',
    flags: [
      'No UPI screenshots — digital income unverified',
      'No electricity bill — commercial connection unconfirmed',
    ],
    nextSteps: 'Upload UPI screenshots and MSEDCL bill to unlock Grade A and ₹85,000+ limit',
    assessmentdate: '27 March 2026',
  },
  raju: {
    name: 'Rajendra Kokate',
    business: 'Raju Tent & Decoration',
    location: 'Pimpri, Pune',
    type: 'Tent / Event Decoration',
    creditgrade: 'A-',
    finallimit: 58000,
    warmthscore: 0.79,
    monthlyinflow: 97000,
    sourcesverified: 2,
    gradeColor: '#3FB950',
    flags: [
      'Seasonal business — income concentrated Oct–Mar, near-zero Apr–Sep',
    ],
    nextSteps: 'Seasonal note included in Credit Memo. Enable AA consent for ₹90,000+ limit',
    assessmentdate: '27 March 2026',
  },
}

function formatIndianNumber(num) {
  return num.toLocaleString('en-IN')
}

function ResultContent() {
  const searchParams = useSearchParams()
  const router = useRouter()

  // ── Persona resolution — LOUD on failure, never silent ──────────────────
  const VALID_KEYS = Object.keys(PERSONA_DATA)
  const personaKeyRaw = searchParams.get('persona')

  // Recovery: if URL param is missing, try sessionStorage (e.g. after a
  // browser refresh that dropped the query string).
  let personaKey = personaKeyRaw
  if (!VALID_KEYS.includes(personaKey)) {
    try {
      const stored = sessionStorage.getItem('shadowcredit_session')
      if (stored) {
        const parsed = JSON.parse(stored)
        if (VALID_KEYS.includes(parsed.persona)) {
          personaKey = parsed.persona
        }
      }
    } catch {
      // ignore
    }
  }

  const personaFallbackActive = !VALID_KEYS.includes(personaKey)
  if (personaFallbackActive) {
    console.error(
      '[Shadow Credit / ResultPage] ⚠️ Invalid or missing ?persona param.',
      '\nReceived:', JSON.stringify(personaKeyRaw),
      '\nValid keys:', VALID_KEYS.join(', '),
      "\nFalling back to 'meena'. The agents page must pass ?persona=<key> when navigating here."
    )
    personaKey = 'meena'
  }

  const persona = PERSONA_DATA[personaKey]

  const gradeEmoji = persona.creditgrade.startsWith('A') ? '🟢' : persona.creditgrade.startsWith('B') ? '🟡' : '🔴'

  return (
    <div style={{ minHeight: '100vh', background: '#FAFAF9', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-start', padding: '24px 16px 48px' }}>

      {/* ⚠️ Debug banner — remove or gate on process.env.NODE_ENV==='development' in production */}
      {personaFallbackActive && (
        <div style={{
          width: '100%', maxWidth: 420,
          background: '#FEF2F2',
          border: '1.5px solid #FCA5A5',
          borderRadius: 8,
          padding: '10px 14px',
          marginBottom: 16,
          fontSize: 12,
          color: '#B91C1C',
          fontFamily: 'monospace',
        }}>
          <strong>⚠️ DEV WARNING:</strong> No valid <code>?persona=</code> param in URL
          (received: <code>{JSON.stringify(personaKeyRaw)}</code>). Defaulted to meena.
        </div>
      )}
      <div style={{ width: '100%', maxWidth: 420 }}>

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 32 }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: '#1A1916', letterSpacing: 1 }}>SHADOW CREDIT</span>
          <span style={{ fontSize: 11, color: '#A8A49E', background: '#F4F3F1', padding: '4px 10px', borderRadius: 99 }}>Assessment Complete</span>
        </div>

        {/* Check icon */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 20 }}>
          <div style={{ width: 64, height: 64, borderRadius: '50%', background: '#EAF3EF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 28 }}>✓</div>
        </div>

        {/* Business name */}
        <h1 style={{ fontSize: 22, fontWeight: 700, textAlign: 'center', color: '#1A1916', margin: '0 0 4px' }}>{persona.business}</h1>
        <p style={{ textAlign: 'center', color: '#6B6760', fontSize: 14, margin: '0 0 28px' }}>{persona.name} · {persona.location}</p>

        {/* Credit limit card */}
        <div style={{ background: 'white', border: '1.5px solid #E5E3DF', borderRadius: 16, padding: '24px 20px', marginBottom: 16, textAlign: 'center' }}>
          <p style={{ fontSize: 13, color: '#6B6760', margin: '0 0 6px' }}>Recommended Loan Limit</p>
          <p style={{ fontSize: 42, fontWeight: 700, color: '#1D6B4E', margin: '0 0 6px', letterSpacing: -1 }}>₹{formatIndianNumber(persona.finallimit)}</p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 8, alignItems: 'center' }}>
            <span style={{ fontSize: 13, background: '#F4F3F1', padding: '3px 10px', borderRadius: 99, color: '#1A1916', fontWeight: 600 }}>
              {gradeEmoji} Grade {persona.creditgrade}
            </span>
            <span style={{ fontSize: 12, color: '#6B6760' }}>{persona.sourcesverified} of 5 sources verified</span>
          </div>
        </div>

        {/* Flags if any */}
        {persona.flags.length > 0 && (
          <div style={{ background: '#FDF3E7', border: '1.5px solid rgba(245,166,35,0.3)', borderRadius: 12, padding: '14px 16px', marginBottom: 16 }}>
            <p style={{ fontSize: 13, fontWeight: 600, color: '#92521E', margin: '0 0 8px' }}>⚠️ Flags Requiring RM Attention</p>
            {persona.flags.map((flag, i) => (
              <p key={i} style={{ fontSize: 13, color: '#92521E', margin: '0 0 4px', paddingLeft: 12 }}>• {flag}</p>
            ))}
          </div>
        )}

        {/* Info rows */}
        <div style={{ background: 'white', border: '1.5px solid #E5E3DF', borderRadius: 12, overflow: 'hidden', marginBottom: 16 }}>
          {[
            ['Business Type', persona.type],
            ['CreditWarmth Score', `${persona.warmthscore} / 1.0`],
            ['Monthly Inflow (stated)', `₹${formatIndianNumber(persona.monthlyinflow)}`],
            ['Sources Verified', `${persona.sourcesverified} of 5`],
            ['Assessed on', persona.assessmentdate],
          ].map(([label, value], i, arr) => (
            <div key={label} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '13px 16px',
              borderBottom: i < arr.length - 1 ? '1px solid #E5E3DF' : 'none'
            }}>
              <span style={{ fontSize: 13, color: '#6B6760' }}>{label}</span>
              <span style={{ fontSize: 13, fontWeight: 500, color: '#1A1916' }}>{value}</span>
            </div>
          ))}
        </div>

        {/* How to improve */}
        <div style={{ background: 'white', border: '1.5px solid #E5E3DF', borderRadius: 12, padding: '14px 16px', marginBottom: 16 }}>
          <p style={{ fontSize: 13, fontWeight: 600, color: '#1A1916', margin: '0 0 6px' }}>💡 How to increase your limit</p>
          <p style={{ fontSize: 13, color: '#6B6760', margin: 0, lineHeight: 1.6 }}>{persona.nextSteps}</p>
        </div>

        {/* What happens next */}
        <div style={{ background: 'white', border: '1.5px solid #E5E3DF', borderRadius: 12, padding: '14px 16px', marginBottom: 24 }}>
          <p style={{ fontSize: 13, fontWeight: 600, color: '#1A1916', margin: '0 0 6px' }}>What happens next?</p>
          <p style={{ fontSize: 13, color: '#6B6760', margin: 0, lineHeight: 1.6 }}>
            Your bank relationship manager will review this assessment and contact you within 24 hours to discuss your loan options.
          </p>
        </div>

        {/* Buttons */}
        <button
          onClick={() => alert('Download feature coming soon. In production, this downloads the Credit Passport PDF.')}
          style={{ width: '100%', background: '#1D6B4E', color: 'white', border: 'none', borderRadius: 12, padding: '15px 0', fontSize: 15, fontWeight: 600, cursor: 'pointer', marginBottom: 12 }}>
          Download My Assessment
        </button>

        <button
          onClick={() => {
            if (navigator.share) {
              navigator.share({ title: 'Shadow Credit Assessment', text: `${persona.business} — ₹${formatIndianNumber(persona.finallimit)} recommended limit, Grade ${persona.creditgrade}`, url: window.location.href })
            } else {
              alert('Share: Copy this link to your bank: ' + window.location.href)
            }
          }}
          style={{ width: '100%', background: 'transparent', color: '#1A1916', border: '1.5px solid #C9C5BF', borderRadius: 12, padding: '15px 0', fontSize: 15, fontWeight: 500, cursor: 'pointer', marginBottom: 12 }}>
          Share with Bank
        </button>

        <button
          onClick={() => router.push('/apply')}
          style={{ width: '100%', background: 'transparent', color: '#6B6760', border: 'none', borderRadius: 12, padding: '12px 0', fontSize: 14, cursor: 'pointer' }}>
          ← Start New Assessment
        </button>

        {/* Footer */}
        <p style={{ textAlign: 'center', fontSize: 11, color: '#A8A49E', marginTop: 24 }}>
          Shadow Credit · Powered by AI · RBI Compliant · DPDP Act 2023
        </p>

      </div>
    </div>
  )
}

export default function ResultPage() {
  return (
    <Suspense fallback={
      <div style={{ minHeight: '100vh', background: '#FAFAF9', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: '#6B6760', fontSize: 14 }}>Loading result...</p>
      </div>
    }>
      <ResultContent />
    </Suspense>
  )
}
