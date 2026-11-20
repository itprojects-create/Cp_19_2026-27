'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

const AGENTS = [
  { id: 'AGENT00MAPS', name: 'Biz Verify', icon: '📍' },
  { id: 'AGENT01OCR', name: 'OCR Scan', icon: '📄' },
  { id: 'AGENT02WHATSAPP', name: 'Chat Parse', icon: '💬' },
  { id: 'AGENT04WARMTH', name: 'Credit Score', icon: '📊' },
  { id: 'AGENT05RECON', name: 'Reconcile', icon: '🔍' },
  { id: 'AGENT06COMPLIANCE', name: 'Compliance', icon: '✅' },
  { id: 'AGENT07REPORT', name: 'Credit Memo', icon: '📋' },
];

const PERSONAS = {
  meena: {
    name: 'Meena Fashion House',
    location: 'Kalyani Nagar, Pune',
    type: 'Tailor / Stitching Shop',
    documents: 'WhatsApp + UPI + Electricity Bill',
    result: {
      creditgrade: 'A-',
      finallimit: 45000,
      warmthscore: 0.74,
      flags: ['Business NOT found on Google Maps — address confirmed via electricity bill instead'],
      reconciliationstatus: 'NORMALCASH',
    },
    script: [
      { t: 2, agent: 'AGENT00MAPS', color: '#1F6FEB', msg: 'Searching Google Maps for Meena Fashion House, Kalyani Nagar, Pune...' },
      { t: 5, agent: 'AGENT00MAPS', color: '#F5A623', msg: '⚠️ Business NOT found at stated address. Similar name found 1km away. mapsconfidence: 0.22' },
      { t: 8, agent: 'AGENT01OCR', color: '#0EA5E9', msg: 'Scanning uploaded documents for UPI screenshots and electricity bill...' },
      { t: 11, agent: 'AGENT01OCR', color: '#3FB950', msg: '✅ 2 UPI screenshots detected (PhonePe/GPay). Electricity bill found — MSEDCL, name matches applicant, commercial tariff.' },
      { t: 14, agent: 'AGENT02WHATSAPP', color: '#10B981', msg: 'Parsing WhatsApp export — 134 messages loaded...' },
      { t: 17, agent: 'AGENT02WHATSAPP', color: '#10B981', msg: 'Pre-filter: 61 financial signals found, 73 noise dropped (54%)' },
      { t: 21, agent: 'AGENT02WHATSAPP', color: '#10B981', msg: 'Classified: 34 payment events. Cash ratio: 40%. UPI screenshots available for cross-verification of 22 events.' },
      { t: 25, agent: 'AGENT04WARMTH', color: '#8B5CF6', msg: 'Computing CreditWarmthScore — 7 behavioral signals...' },
      { t: 29, agent: 'AGENT04WARMTH', color: '#8B5CF6', msg: 'CreditWarmthScore: 0.74 | Grade: A- | Data diversity: MEDIUM (3/5 sources — WhatsApp + UPI + Bill). Multi-source boost applied.' },
      { t: 33, agent: 'AGENT05RECON', color: '#EF4444', msg: 'Reconciling WhatsApp stated revenue against UPI screenshots...' },
      { t: 37, agent: 'AGENT05RECON', color: '#3FB950', msg: '✅ Revenue CONFIRMED. WhatsApp states ₹48,000/mo — UPI screenshots verify ₹44,200/mo digitally (92% match). Classification: NORMALCASH' },
      { t: 40, agent: 'AGENT06COMPLIANCE', color: '#F97316', msg: 'Running 12-item RBI MSME compliance checklist...' },
      { t: 43, agent: 'AGENT06COMPLIANCE', color: '#F97316', msg: 'PARTIAL: Maps address mismatch. PASS: UPI history, Electricity bill, Data diversity, DPDP consent. 10/12 PASS.' },
      { t: 46, agent: 'AGENT07REPORT', color: '#3B82F6', msg: 'Generating Credit Memo PDF — UPI + bill verified, address flag noted...' },
      { t: 49, agent: 'AGENT07REPORT', color: '#3B82F6', msg: '✅ Credit Memo ready — ₹45,000 limit | Grade A- | SHA-256 signed.' },
    ],
  },
  suresh: {
    name: 'Mahadev Enterprises',
    location: 'Sadashiv Peth, Pune',
    type: 'Kirana / General Store',
    documents: 'WhatsApp only',
    result: {
      creditgrade: 'B+',
      finallimit: 52000,
      warmthscore: 0.68,
      flags: ['No UPI screenshots — digital income unverified', 'No electricity bill — address unconfirmed'],
      reconciliationstatus: 'NORMALCASH',
    },
    script: [
      { t: 2, agent: 'AGENT00MAPS', color: '#1F6FEB', msg: 'Searching Google Maps for Mahadev Enterprises, Sadashiv Peth, Pune...' },
      { t: 5, agent: 'AGENT00MAPS', color: '#3FB950', msg: '✅ Business FOUND on Google Maps. 4.1★ rating, 34 reviews, OPERATIONAL. mapsconfidence: 0.80' },
      { t: 8, agent: 'AGENT01OCR', color: '#0EA5E9', msg: 'Scanning uploaded documents for UPI screenshots and electricity bill...' },
      { t: 11, agent: 'AGENT01OCR', color: '#F5A623', msg: '⚠️ No UPI screenshots found. No electricity bill uploaded. Cannot confirm commercial connection type.' },
      { t: 14, agent: 'AGENT02WHATSAPP', color: '#10B981', msg: 'Parsing WhatsApp export — 420 messages loaded, Jan–Mar 2024...' },
      { t: 17, agent: 'AGENT02WHATSAPP', color: '#10B981', msg: 'Pre-filter: 198 financial signals found, 222 noise dropped (53%)' },
      { t: 21, agent: 'AGENT02WHATSAPP', color: '#10B981', msg: 'Classified: 156 payment events, 8 unique counterparties. WhatsApp stated revenue: ₹70,500/mo average' },
      { t: 24, agent: 'AGENT02WHATSAPP', color: '#10B981', msg: 'Behavioral signals: Peak hours 87%, Activity ratio 0.92, Response time avg 8 min. HIGH engagement.' },
      { t: 27, agent: 'AGENT04WARMTH', color: '#8B5CF6', msg: 'Computing CreditWarmthScore — 7 behavioral signals...' },
      { t: 31, agent: 'AGENT04WARMTH', color: '#8B5CF6', msg: 'CreditWarmthScore: 0.68 | Grade: B+ | Income regularity: HIGH. Data diversity: LOW (2/5 sources, Maps + WA).' },
      { t: 34, agent: 'AGENT05RECON', color: '#EF4444', msg: 'Reconciling WhatsApp revenue — no UPI to cross-verify, Maps location confirmed...' },
      { t: 38, agent: 'AGENT05RECON', color: '#D29922', msg: '⚠️ Revenue stated ₹70,500/mo — unverified digitally. Google Maps business CONFIRMED. Gap: 100% cash-based. Classification: NORMALCASH per RBI MSME norms.' },
      { t: 41, agent: 'AGENT06COMPLIANCE', color: '#F97316', msg: 'Running 12-item RBI MSME compliance checklist...' },
      { t: 44, agent: 'AGENT06COMPLIANCE', color: '#F97316', msg: 'PARTIAL: UPI history missing, Electricity bill missing. PASS: Maps verified, Business continuity 12+ months, DPDP consent. 9/12 PASS.' },
      { t: 47, agent: 'AGENT07REPORT', color: '#3B82F6', msg: 'Generating Credit Memo PDF — Maps-verified business, cash-based income pattern...' },
      { t: 50, agent: 'AGENT07REPORT', color: '#3B82F6', msg: '✅ Credit Memo ready — ₹52,000 limit | Grade B+ | Recommends UPI + Bill for higher limit.' },
    ],
  },
  raju: {
    name: 'Raju Tent & Decoration',
    location: 'Pimpri, Pune',
    type: 'Tent / Event Decoration',
    documents: 'UPI + Electricity Bill',
    result: {
      creditgrade: 'A-',
      finallimit: 58000,
      warmthscore: 0.79,
      flags: ['No WhatsApp export attached — revenue derived from UPI + electricity bill only'],
      reconciliationstatus: 'NORMALCASH',
    },
    script: [
      { t: 2, agent: 'AGENT00MAPS', color: '#1F6FEB', msg: 'Searching Google Maps for Raju Tent & Decoration, Pimpri, Pune...' },
      { t: 5, agent: 'AGENT00MAPS', color: '#3FB950', msg: '✅ Business FOUND. 4.3★ rating, 52 reviews, OPERATIONAL. mapsconfidence: 0.85. Event/Tent category confirmed.' },
      { t: 8, agent: 'AGENT01OCR', color: '#0EA5E9', msg: 'Scanning uploaded documents...' },
      { t: 11, agent: 'AGENT01OCR', color: '#3FB950', msg: '✅ 3 UPI screenshots found. Electricity bill found — MSEDCL, name matches applicant, commercial tariff.' },
      { t: 14, agent: 'AGENT02WHATSAPP', color: '#8B949E', msg: '⚠️ No WhatsApp export attached. Falling back to UPI transaction history for revenue timeline...' },
      { t: 18, agent: 'AGENT02WHATSAPP', color: '#10B981', msg: 'Parsing 3 UPI screenshots — Oct 2023 to Mar 2024 coverage. Events: bookings, advances, final payments, supplier payments.' },
      { t: 22, agent: 'AGENT02WHATSAPP', color: '#10B981', msg: 'Classified: Oct ₹84,000 | Nov ₹1,20,000 | Dec ₹2,25,000 | Jan ₹1,10,000 | Feb ₹1,05,000 | Mar ₹30,000' },
      { t: 26, agent: 'AGENT02WHATSAPP', color: '#D29922', msg: '⚠️ SEASONAL PATTERN DETECTED: Peak Oct–Feb, sharp drop Mar. Data confirms monsoon gap (Jun–Sep zero). seasonaldetected: TRUE' },
      { t: 29, agent: 'AGENT04WARMTH', color: '#8B5CF6', msg: 'Computing CreditWarmthScore — applying seasonal underwriting model...' },
      { t: 33, agent: 'AGENT04WARMTH', color: '#8B5CF6', msg: 'CreditWarmthScore: 0.79 | Grade: A- | Seasonal adjustment applied. Annual median used (not 90-day). 6-month total ₹6,74,000.' },
      { t: 36, agent: 'AGENT05RECON', color: '#EF4444', msg: 'Forensic reconciliation — cross-checking UPI screenshots against electricity bill address...' },
      { t: 40, agent: 'AGENT05RECON', color: '#3FB950', msg: '✅ Revenue pattern CONSISTENT with tent/event industry seasonal norms. Holi & Diwali spike confirmed. Classification: NORMALCASH' },
      { t: 43, agent: 'AGENT06COMPLIANCE', color: '#F97316', msg: 'Running 12-item RBI MSME compliance checklist — seasonal business adjustment...' },
      { t: 46, agent: 'AGENT06COMPLIANCE', color: '#F97316', msg: 'PASS: Maps verified, UPI history, Electricity bill, 12+ months history, seasonal pattern documented. PARTIAL: WhatsApp not provided. 10/12 PASS.' },
      { t: 49, agent: 'AGENT07REPORT', color: '#3B82F6', msg: 'Generating Credit Memo — seasonal underwriting, annualized median ₹97,000/mo...' },
      { t: 52, agent: 'AGENT07REPORT', color: '#3B82F6', msg: '✅ Credit Memo ready — ₹58,000 limit | Grade A- | Seasonal business note included. SHA-256 signed.' },
    ],
  },
};

function fmt(sec) {
  const mm = String(Math.floor(sec / 60)).padStart(2, '0');
  const ss = String(sec % 60).padStart(2, '0');
  return `${mm}:${ss}`;
}

export default function AgentsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session') || '';

  // ── Persona resolution — LOUD on failure, never silent ───────────────────
  // The persona param MUST be set by /apply/page.jsx before navigating here.
  // If it's missing or invalid, we log a clear error and show a visible banner
  // so this bug cannot hide in production.
  const VALID_PERSONA_KEYS = Object.keys(PERSONAS); // ['meena','suresh','raju']
  const personaKeyRaw = searchParams.get('persona');
  const personaKeyIsValid = VALID_PERSONA_KEYS.includes(personaKeyRaw);
  const personaFallbackActive = !personaKeyIsValid;

  if (personaFallbackActive) {
    console.error(
      '[Shadow Credit / AgentsContent] ⚠️ Invalid or missing ?persona param.',
      '\nReceived:', JSON.stringify(personaKeyRaw),
      '\nValid keys:', VALID_PERSONA_KEYS.join(', '),
      '\nFalling back to \'meena\'. Fix /apply/page.jsx to pass ?persona=<key>.'
    );
  }

  const personaKey = personaKeyIsValid ? personaKeyRaw : 'meena';
  const persona = PERSONAS[personaKey];
  const SCRIPT = persona.script;

  const [elapsed, setElapsed] = useState(0);
  const [logs, setLogs] = useState([]);
  const [done, setDone] = useState(false);
  const [sessionData, setSessionData] = useState({
    businessName: '',
    location: '',
    businessType: '',
    ownerName: '',
  });
  const [agentState, setAgentState] = useState(
    AGENTS.reduce((acc, item) => {
      acc[item.id] = 'idle';
      return acc;
    }, {})
  );
  const logRef = useRef(null);
  const displayBusinessName = sessionData.businessName || persona.name;
  const displayLocation = sessionData.location || persona.location;
  const displayBusinessType = sessionData.businessType || persona.type;
  const displayOwnerName = sessionData.ownerName;
  const displayPersona = sessionData.businessName ? 'Derived' : personaKey;

  const personalizedScript = useMemo(
    () =>
      SCRIPT.map((entry) => ({
        ...entry,
        msg: entry.msg
          .replaceAll(persona.name, displayBusinessName)
          .replaceAll(persona.location, displayLocation),
      })),
    [SCRIPT, persona.name, persona.location, displayBusinessName, displayLocation]
  );

  const LAST_EVENT_BY_AGENT = useMemo(
    () =>
      personalizedScript.reduce((acc, entry) => {
        acc[entry.agent] = entry.t;
        return acc;
      }, {}),
    [personalizedScript]
  );

  const finalTime = personalizedScript[personalizedScript.length - 1].t;
  const completionSecond = finalTime + 3;

  // FIX #2: re-read sessionStorage every time the persona changes,
  // not just once on mount. Previously stale sessionData from an
  // earlier persona could leak into a newly selected one.
  useEffect(() => {
    const stored = sessionStorage.getItem('shadowcredit_session');
    if (!stored) {
      setSessionData({ businessName: '', location: '', businessType: '', ownerName: '' });
      return;
    }
    try {
      const parsed = JSON.parse(stored);
      setSessionData({
        businessName: parsed.businessName || '',
        location: parsed.cityArea || '',
        businessType: parsed.businessType || '',
        ownerName: parsed.ownerName || '',
      });
    } catch {
      setSessionData({
        businessName: '',
        location: '',
        businessType: '',
        ownerName: '',
      });
    }
  }, [personaKey]);

  // Reset the run state whenever persona changes.
  useEffect(() => {
    setElapsed(0);
    setLogs([]);
    setDone(false);
    setAgentState(
      AGENTS.reduce((acc, item) => {
        acc[item.id] = 'idle';
        return acc;
      }, {})
    );
  }, [personaKey]);

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [personaKey]);

  useEffect(() => {
    const events = personalizedScript.filter((e) => e.t === elapsed);
    if (!events.length) return;

    setLogs((prev) => [
      ...prev,
      ...events.map((e) => ({ t: e.t, agentId: e.agent, message: e.msg, color: e.color })),
    ]);

    setAgentState((prev) => {
      const next = { ...prev };
      events.forEach((e) => {
        next[e.agent] = 'running';
      });
      return next;
    });
  }, [elapsed, personalizedScript]);

  useEffect(() => {
    setAgentState((prev) => {
      const next = { ...prev };
      AGENTS.forEach((a) => {
        const firstEvent = personalizedScript.find((t) => t.agent === a.id)?.t;
        const lastT = LAST_EVENT_BY_AGENT[a.id];
        if (lastT == null) {
          next[a.id] = 'idle';
        } else if (elapsed > lastT) {
          next[a.id] = 'complete';
        } else if (elapsed < firstEvent) {
          next[a.id] = 'idle';
        }
      });
      return next;
    });
  }, [elapsed, LAST_EVENT_BY_AGENT, personalizedScript]);

  useEffect(() => {
    if (elapsed < completionSecond || done) return;
    setDone(true);
    const to = setTimeout(() => {
      router.push('/apply/result?persona=' + personaKey + '&session=' + sessionId);
    }, 2000);
    return () => clearTimeout(to);
  }, [elapsed, done, router, sessionId, personaKey, completionSecond]);

  useEffect(() => {
    if (!logRef.current) return;
    logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  const progress = Math.min(100, Math.round((elapsed / completionSecond) * 100));
  const completeCount = useMemo(
    () => Object.values(agentState).filter((s) => s === 'complete').length,
    [agentState]
  );

  return (
    <div style={{ minHeight: '100vh', background: '#0D1117', color: '#fff', display: 'flex', flexDirection: 'column' }}>

      {/* ⚠️ Debug banner — visible whenever persona param is missing/invalid.
           This banner means /apply/page.jsx did NOT pass ?persona=<key> in
           the navigation URL. Fix redirectToProcessing() in apply/page.jsx. */}
      {personaFallbackActive && (
        <div style={{
          background: '#7C1D1D',
          border: '1px solid #F87171',
          color: '#FCA5A5',
          fontFamily: 'monospace',
          fontSize: 12,
          padding: '10px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}>
          <span style={{ fontSize: 16 }}>⚠️</span>
          <span>
            <strong>DEV WARNING:</strong> No valid <code>?persona=</code> param in URL
            (received: <code>{JSON.stringify(personaKeyRaw)}</code>).
            Defaulted to <strong>meena</strong>.
            Check <code>redirectToProcessing()</code> in <code>apply/page.jsx</code>.
          </span>
        </div>
      )}

      <div style={{ borderBottom: '1px solid #21262D', padding: '14px 20px', display: 'flex', justifyContent: 'space-between' }}>
        <span style={{ color: '#8B949E', fontFamily: 'monospace', fontSize: 13 }}>SHADOW CREDIT</span>
        <span style={{ color: '#8B949E', fontFamily: 'monospace', fontSize: 13 }}>
          {done ? '✅ Complete' : `Analyzing your business • ${elapsed}s`}
        </span>
      </div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <aside style={{ width: 280, borderRight: '1px solid #21262D', padding: 16, overflowY: 'auto' }}>
          <p style={{ color: '#8B949E', fontSize: 11, letterSpacing: 1, textTransform: 'uppercase', marginBottom: 12 }}>7 AI Agents</p>
          {AGENTS.map((agent) => {
            const status = agentState[agent.id];
            const border = status === 'complete' ? '#3FB950' : status === 'running' ? '#1F6FEB' : '#21262D';
            const bg = status === 'complete' ? 'rgba(63,185,80,0.08)' : status === 'running' ? 'rgba(31,111,235,0.08)' : 'transparent';
            return (
              <div key={agent.id} style={{ border: `1px solid ${border}`, background: bg, opacity: status === 'idle' ? 0.45 : 1, borderRadius: 8, padding: 12, marginBottom: 10 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span>{agent.icon}</span>
                  <span style={{ fontSize: 14 }}>{agent.name}</span>
                  <span style={{ marginLeft: 'auto', fontSize: 12 }}>
                    {status === 'complete' ? '✓' : status === 'running' ? '⟳' : '○'}
                  </span>
                </div>
                <div style={{ color: '#8B949E', fontSize: 11, fontFamily: 'monospace', marginTop: 4 }}>{agent.id}</div>
              </div>
            );
          })}
        </aside>

        <main ref={logRef} style={{ flex: 1, overflowY: 'auto', padding: 16, background: '#090D14', fontFamily: 'monospace', fontSize: 12 }}>
          <p style={{ color: '#8B949E', marginBottom: 12 }}>LIVE LOG — {logs.length} entries</p>
          {logs.map((entry, i) => (
            <div key={`${entry.agentId}-${entry.t}-${i}`} style={{ display: 'flex', gap: 10, marginBottom: 8, color: entry.color || '#D4E6FF' }}>
              <span style={{ color: '#8B949E', flexShrink: 0 }}>[{fmt(entry.t)}]</span>
              <span style={{ color: '#3FB950', flexShrink: 0 }}>[{entry.agentId}]</span>
              <span>{entry.message}</span>
            </div>
          ))}
          {done && (
            <div style={{ marginTop: 14, border: '1px solid rgba(63,185,80,0.35)', borderRadius: 8, padding: 12, color: '#3FB950', background: 'rgba(63,185,80,0.08)' }}>
              ✅ SESSION COMPLETE — Redirecting to results...
            </div>
          )}
        </main>

        <aside style={{ width: 280, borderLeft: '1px solid #21262D', padding: 16 }}>
          <p style={{ color: '#8B949E', fontSize: 11, letterSpacing: 1, textTransform: 'uppercase', marginBottom: 12 }}>Progress</p>

          <div style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14, marginBottom: 6 }}>
              <span>Analysis</span>
              <span style={{ color: '#1F6FEB' }}>{progress}%</span>
            </div>
            <div style={{ height: 8, borderRadius: 6, background: '#21262D' }}>
              <div style={{ height: 8, borderRadius: 6, background: '#1F6FEB', width: `${progress}%`, transition: 'width 1s linear' }} />
            </div>
          </div>

          <div style={{ border: '1px solid rgba(31,111,235,0.35)', borderRadius: 8, background: 'rgba(31,111,235,0.08)', padding: 12, marginBottom: 16 }}>
            <div style={{ color: '#8B949E', fontSize: 11 }}>Session</div>
            <div style={{ fontSize: 14, marginTop: 4 }}>{displayBusinessName}</div>
            <div style={{ color: '#8B949E', fontSize: 12, marginTop: 2 }}>{displayLocation}</div>
            {displayOwnerName && (
              <div style={{ color: '#8B949E', fontSize: 12, marginTop: 2 }}>
                Owner: {displayOwnerName}
              </div>
            )}
            <div style={{ color: '#8B949E', fontSize: 12, marginTop: 2 }}>{displayBusinessType}</div>
            <div style={{ color: '#8B949E', fontSize: 12, marginTop: 2 }}>{persona.documents}</div>
          </div>

          <div style={{ fontSize: 12, display: 'grid', gap: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#8B949E' }}>Persona</span>
              <span>{displayPersona}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#8B949E' }}>Session ID</span>
              <span style={{ maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis' }}>{sessionId || 'demo-session'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#8B949E' }}>Agents complete</span>
              <span>{completeCount}/7</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#8B949E' }}>Flags raised</span>
              <span style={{ color: '#F5A623' }}>{persona.result.flags.length}</span>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}