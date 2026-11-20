'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';

const PERSONAS = {
  'meena-session-001': {
    caseId: 'SC-4F2A1B',
    applicant: 'Meena Devi',
    business: 'Meena Saree & Cloth Store',
    location: 'Kalyani Nagar, Pune',
    type: 'Tailor / Clothing',
    status: 'COMPLETE',
    score: 0.74,
    grade: 'B+',
    limit: 120000,
    monthlyRevenue: 44000,
    weeklyAvg: 11200,
    counterparties: 23,
    gapPct: '8%',
    gapClass: 'NORMAL_CASH',
    sourcesVerified: 4,
    totalSources: 5,
    confidenceBand: 'HIGH',
    artifacts: [
      { type: 'WHATSAPP', label: 'WhatsApp Chat', file: 'persona1_meena_whatsapp.txt', conf: 0.87, status: 'COMPLETE', icon: '💬' },
      { type: 'UPI', label: 'UPI Screenshots', file: 'upi_meena_3imgs.png', conf: 0.91, status: 'COMPLETE', icon: '💳' },
      { type: 'BILL', label: 'MSEDCL Bill', file: 'msedcl_meena_march.jpg', conf: 0.88, status: 'COMPLETE', icon: '⚡' },
    ],
    maps: { name: 'Meena Saree & Cloth Store', address: 'Kalyani Nagar, Pune', rating: 4.3, reviews: 31, verified: true },
    signals: [
      { name: 'Income Regularity', value: 0.84, shap: '+0.28' },
      { name: 'Claim Consistency', value: 0.74, shap: '+0.18' },
      { name: 'Business Continuity', value: 0.89, shap: '+0.19' },
      { name: 'Seasonal Pattern', value: 0.82, shap: '+0.14' },
      { name: 'Network Reliability', value: 0.61, shap: '+0.06' },
      { name: 'Data Diversity', value: 0.9, shap: '+0.05' },
      { name: 'Behavioral Signals', value: 0.78, shap: '+0.04' },
    ],
    narrative:
      'Meena Devi operates a tailor and saree retail outlet with continuity over 94 days across 4 independent sources. UPI receipts confirm most WhatsApp stated inflows and variance is consistent with normal cash usage. Recommended limit reflects regularity and continuity adjustment.',
    flags: [
      { type: 'warn', text: 'Minor GST discrepancy — 8% variance within threshold.' },
      { type: 'info', text: 'Seasonal uplift +34% in Oct–Nov confirmed.' },
      { type: 'ok', text: '2 community guarantors identified with clean history.' },
    ],
    compliance: { score: 83, passed: 10, total: 12 },
    scenarios: {
      current: { limit: 120000, delta: null },
      gst: { limit: 150000, delta: 30000 },
      aa: { limit: 144000, delta: 24000 },
      gstaa: { limit: 180000, delta: 60000 },
    },
    logs: [
      { time: '10:42:01.221', agent: 'AGENT00MAPS', color: '#1F6FEB', msg: 'Searching Google Maps for Meena Saree & Cloth Store, Kalyani Nagar...', conf: null },
      { time: '10:42:03.441', agent: 'AGENT00MAPS', color: '#1F6FEB', msg: 'Place found — rating 4.3, 31 reviews, OPERATIONAL.', conf: 0.87 },
      { time: '10:42:05.882', agent: 'AGENT01OCR', color: '#0EA5E9', msg: 'Extracted bill: COMMERCIAL connection, ₹1,840 amount.', conf: 0.88 },
      { time: '10:42:08.334', agent: 'AGENT02WA', color: '#10B981', msg: 'Classified 28 financial events from WhatsApp.', conf: 0.87 },
      { time: '10:42:10.881', agent: 'AGENT04WARMTH', color: '#8B5CF6', msg: 'WarmthScore: 0.740 Grade: B+.', conf: 0.74 },
      { time: '10:42:13.445', agent: 'AGENT05RECON', color: '#EF4444', msg: 'FORENSIC: gap 8% — NORMAL_CASH.', conf: 0.91 },
      { time: '10:42:15.221', agent: 'AGENT06COMPLY', color: '#F97316', msg: 'Compliance check: 10/12 PASS.', conf: null },
      { time: '10:42:17.334', agent: 'AGENT07REPORT', color: '#3B82F6', msg: 'Credit memo and Credit Passport generated.', conf: null },
      { time: '10:42:17.441', agent: 'SUPERVISOR', color: '#7C3AED', msg: '◆ SESSION COMPLETE — target met under 90s.', conf: null },
    ],
  },
  'suresh-session-001': {
    caseId: 'SC-8B3D2E',
    applicant: 'Suresh Sharma',
    business: 'Mahadev Enterprises',
    location: 'Sadashiv Peth, Pune',
    type: 'Kirana / General Store',
    status: 'COMPLETE',
    score: 0.61,
    grade: 'B',
    limit: 95000,
    monthlyRevenue: 31500,
    weeklyAvg: 7875,
    counterparties: 18,
    gapPct: '22%',
    gapClass: 'NORMAL_CASH',
    sourcesVerified: 2,
    totalSources: 5,
    confidenceBand: 'MEDIUM',
    artifacts: [{ type: 'WHATSAPP', label: 'WhatsApp Chat', file: 'persona2_suresh_whatsapp.txt', conf: 0.81, status: 'COMPLETE', icon: '💬' }],
    maps: { name: 'Mahadev Enterprises', address: 'Sadashiv Peth, Pune', rating: 4.1, reviews: 19, verified: true },
    signals: [
      { name: 'Income Regularity', value: 0.71, shap: '+0.21' },
      { name: 'Claim Consistency', value: 0.63, shap: '+0.14' },
      { name: 'Business Continuity', value: 0.74, shap: '+0.16' },
      { name: 'Seasonal Pattern', value: 0.68, shap: '+0.10' },
      { name: 'Network Reliability', value: 0.55, shap: '+0.05' },
      { name: 'Data Diversity', value: 0.48, shap: '-0.08' },
      { name: 'Behavioral Signals', value: 0.72, shap: '+0.03' },
    ],
    narrative:
      'Suresh Sharma runs Mahadev Enterprises. Assessment is based mainly on WhatsApp and Maps verification; missing UPI and utility bill reduce confidence band to MEDIUM. Recommended limit includes conservative adjustment.',
    flags: [
      { type: 'warn', text: 'No UPI screenshots provided — digital revenue unverified.' },
      { type: 'warn', text: 'No utility bill — premises unverified via alternate document.' },
      { type: 'info', text: 'Google Maps verified business profile active.' },
    ],
    compliance: { score: 67, passed: 8, total: 12 },
    scenarios: {
      current: { limit: 95000, delta: null },
      gst: { limit: 118000, delta: 23000 },
      aa: { limit: 112000, delta: 17000 },
      gstaa: { limit: 140000, delta: 45000 },
    },
    logs: [
      { time: '11:15:02.110', agent: 'AGENT00MAPS', color: '#1F6FEB', msg: 'Maps verified Mahadev Enterprises (4.1★).', conf: 0.8 },
      { time: '11:15:04.672', agent: 'AGENT02WA', color: '#10B981', msg: 'Parsed WhatsApp: 18 counterparties, stable activity.', conf: 0.81 },
      { time: '11:15:06.330', agent: 'AGENT05RECON', color: '#EF4444', msg: 'Revenue gap 22% — NORMAL_CASH for kirana pattern.', conf: 0.76 },
      { time: '11:15:08.921', agent: 'AGENT06COMPLY', color: '#F97316', msg: 'Compliance: 8/12 PASS.', conf: null },
      { time: '11:15:12.112', agent: 'AGENT07REPORT', color: '#3B82F6', msg: 'Memo generated with medium confidence notes.', conf: null },
      { time: '11:15:14.991', agent: 'SUPERVISOR', color: '#7C3AED', msg: '◆ SESSION COMPLETE — MEDIUM confidence, RM review suggested.', conf: null },
    ],
  },
  'raju-session-001': {
    caseId: 'SC-2C9F4A',
    applicant: 'Raju Patil',
    business: 'Raju General Store',
    location: 'Chinchwad, Pune',
    type: 'Kirana / General Store',
    status: 'REVIEW',
    score: 0.58,
    grade: 'B-',
    limit: 72000,
    monthlyRevenue: 24000,
    weeklyAvg: 6000,
    counterparties: 14,
    gapPct: '36%',
    gapClass: 'DATA_GAP',
    sourcesVerified: 3,
    totalSources: 5,
    confidenceBand: 'MEDIUM',
    artifacts: [
      { type: 'WHATSAPP', label: 'WhatsApp Chat', file: 'persona3_raju_whatsapp.txt', conf: 0.76, status: 'COMPLETE', icon: '💬' },
      { type: 'UPI', label: 'UPI Screenshots', file: 'upi_raju_2imgs.png', conf: 0.82, status: 'COMPLETE', icon: '💳' },
      { type: 'BILL', label: 'MSEDCL Bill', file: 'msedcl_raju.jpg', conf: 0.79, status: 'COMPLETE', icon: '⚡' },
    ],
    maps: { name: 'Raju General Store', address: 'Chinchwad, Pune', rating: 3.9, reviews: 11, verified: true },
    signals: [
      { name: 'Income Regularity', value: 0.52, shap: '+0.14' },
      { name: 'Claim Consistency', value: 0.61, shap: '+0.12' },
      { name: 'Business Continuity', value: 0.68, shap: '+0.15' },
      { name: 'Seasonal Pattern', value: 0.43, shap: '-0.18' },
      { name: 'Network Reliability', value: 0.58, shap: '+0.06' },
      { name: 'Data Diversity', value: 0.71, shap: '+0.05' },
      { name: 'Behavioral Signals', value: 0.64, shap: '+0.03' },
    ],
    narrative:
      'Raju Patil shows strong seasonal variation. Off-season months lower current inflow, and 36% reconciliation gap requires RM context. Annual median considered for fair limit recommendation.',
    flags: [
      { type: 'warn', text: 'Seasonal income detected — annual median used for underwriting.' },
      { type: 'warn', text: '36% revenue gap above threshold; classification DATA_GAP.' },
      { type: 'info', text: 'Pipeline paused previously for RM clarification on tenure.' },
    ],
    compliance: { score: 72, passed: 9, total: 12 },
    scenarios: {
      current: { limit: 72000, delta: null },
      gst: { limit: 90000, delta: 18000 },
      aa: { limit: 88000, delta: 16000 },
      gstaa: { limit: 110000, delta: 38000 },
    },
    logs: [
      { time: '09:31:03.221', agent: 'AGENT00MAPS', color: '#1F6FEB', msg: 'Maps verified. Store operational with 11 reviews.', conf: 0.71 },
      { time: '09:31:07.881', agent: 'AGENT04WARMTH', color: '#8B5CF6', msg: 'WarmthScore 0.58; seasonal pattern weak signal.', conf: 0.58 },
      { time: '09:31:08.001', agent: 'AGENT05RECON', color: '#EF4444', msg: 'FORENSIC: 36% gap, seasonal cash hypothesis dominant.', conf: 0.71 },
      { time: '09:31:08.221', agent: 'SUPERVISOR', color: '#7C3AED', msg: '◆ PIPELINE PAUSED — clarification requested.', conf: null },
      { time: '09:31:45.001', agent: 'SUPERVISOR', color: '#7C3AED', msg: '◆ Clarification received: 18-month tenure preferred.', conf: null },
      { time: '09:31:49.112', agent: 'AGENT07REPORT', color: '#3B82F6', msg: 'Memo generated with seasonal adjustment note.', conf: null },
      { time: '09:31:49.221', agent: 'SUPERVISOR', color: '#7C3AED', msg: '◆ SESSION COMPLETE — REVIEW status, RM sign-off required.', conf: null },
    ],
  },
};

const scoreColor = (s) => (s >= 0.75 ? '#3FB950' : s >= 0.5 ? '#D29922' : '#F85149');
const confColor = (v) => (v >= 0.85 ? '#3FB950' : v >= 0.6 ? '#D29922' : '#F85149');
const fmtINR = (n) => `₹${n.toLocaleString('en-IN')}`;

function useCountUp(target, active, duration = 1000) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    if (!active) return;
    const start = performance.now();
    const from = val;
    const diff = target - from;
    const step = (now) => {
      const p = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setVal(Math.round(from + diff * eased));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [target, active]); // eslint-disable-line react-hooks/exhaustive-deps
  return val;
}

export default function SessionPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId;
  const p = PERSONAS[sessionId];

  const [blurPII, setBlurPII] = useState(false);
  const [scenario, setScenario] = useState('current');
  const [scenarioLimit, setScenarioLimit] = useState(p?.limit || 0);
  const [showProvenance, setShowProvenance] = useState(null);
  const [clarification, setClarification] = useState(sessionId === 'raju-session-001');
  const [clarificationText, setClarificationText] = useState('');
  const [logs, setLogs] = useState(p?.logs || []);
  const logRef = useRef(null);

  const limitDisplay = useCountUp(scenarioLimit, true, 850);

  const switchScenario = useCallback(
    (tab) => {
      setScenario(tab);
      setScenarioLimit(p?.scenarios?.[tab]?.limit || p?.limit || 0);
    },
    [p]
  );

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs]);

  useEffect(() => {
    if (!p) return;
    setScenario('current');
    setScenarioLimit(p.limit);
    setLogs(p.logs);
  }, [sessionId]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!p) {
    return (
      <div className="min-h-screen bg-[#0D1117] flex items-center justify-center text-[#8B949E]">
        <div className="text-center">
          <div className="text-4xl mb-4">🔍</div>
          <p className="text-lg">Session not found</p>
          <button onClick={() => router.push('/dashboard')} className="mt-4 text-[#1F6FEB] text-sm hover:underline">
            ← Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-[#0D1117] text-[#E6EDF3] flex flex-col overflow-hidden">
      <div className="h-12 bg-[#161B22] border-b border-[#21262D] flex items-center px-6 justify-between shrink-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 bg-[#1F6FEB] rounded-lg flex items-center justify-center text-white text-xs font-bold">SC</div>
          <span className="text-white font-semibold text-sm">Shadow Credit</span>
          <span className="text-[#6E7681] text-sm">/ Cases /</span>
          <span className="text-[#8B949E] text-sm font-mono">{p.caseId}</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-[#6E7681]">
          <div className="w-2 h-2 rounded-full bg-[#3FB950]" />
          Live
        </div>
      </div>

      <div className="h-11 bg-[#161B22] border-b border-[#21262D] flex items-center px-4 justify-between shrink-0">
        <div className="flex items-center gap-4">
          <button onClick={() => router.push('/dashboard')} className="text-[#8B949E] hover:text-white text-sm transition-colors">
            ← Back
          </button>
          <div className={`text-sm font-medium ${blurPII ? 'blur-sm select-none' : ''}`}>{p.applicant}</div>
          <div className={`text-sm text-[#8B949E] ${blurPII ? 'blur-sm select-none' : ''}`}>
            {p.business} · {p.location}
          </div>
        </div>
        <span className={`text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full ${p.status === 'COMPLETE' ? 'bg-[#3FB9501A] text-[#3FB950] border border-[#3FB95030]' : 'bg-[#D299221A] text-[#D29922] border border-[#D2992230]'}`}>
          {p.status}
        </span>
      </div>

      <div className="flex flex-1 overflow-hidden">
        <div className="w-72 shrink-0 bg-[#161B22] border-r border-[#21262D] flex flex-col overflow-hidden">
          <div className="px-4 py-3 border-b border-[#21262D] flex items-center justify-between">
            <span className="text-sm font-semibold text-[#8B949E]">Evidence</span>
            <span className="text-xs text-[#6E7681] bg-[#21262D] px-2 py-0.5 rounded-full">{p.artifacts.length + 1} sources</span>
          </div>
          <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
            {p.artifacts.map((a) => (
              <div key={a.type} className="bg-[#1C2128] border border-[#30363D] rounded-xl p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-base">{a.icon}</span>
                    <span className="text-[11px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-[#21262D] text-[#8B949E]">{a.type}</span>
                  </div>
                  <span className="text-[#3FB950] text-xs">✓</span>
                </div>
                <div className={`text-xs text-[#8B949E] mb-2 truncate ${blurPII ? 'blur-sm' : ''}`}>{a.file}</div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1 bg-[#21262D] rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-700" style={{ width: `${a.conf * 100}%`, backgroundColor: confColor(a.conf) }} />
                  </div>
                  <span className="text-[10px] font-mono" style={{ color: confColor(a.conf) }}>
                    {(a.conf * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}

            <div className="bg-[#1C2128] border border-[#30363D] rounded-xl overflow-hidden">
              <div className="h-20 bg-gradient-to-br from-[#0d2137] to-[#0a1628] flex items-center justify-center relative">
                <div className="text-3xl opacity-30">🗺️</div>
                {p.maps.verified && <div className="absolute top-2 right-2 bg-[#3FB950] text-black text-[9px] font-bold px-1.5 py-0.5 rounded">VERIFIED</div>}
              </div>
              <div className="p-3">
                <div className={`text-sm font-medium text-white mb-0.5 ${blurPII ? 'blur-sm' : ''}`}>{p.maps.name}</div>
                <div className={`text-xs text-[#8B949E] mb-2 ${blurPII ? 'blur-sm' : ''}`}>{p.maps.address}</div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    <span className="text-[#F59E0B] text-xs">★</span>
                    <span className="text-xs text-[#E6EDF3] font-medium">{p.maps.rating}</span>
                    <span className="text-xs text-[#6E7681]">({p.maps.reviews})</span>
                  </div>
                  <span className="text-[10px] text-[#3FB950]">● Operational</span>
                </div>
              </div>
            </div>
          </div>
          <div className="border-t border-[#21262D] px-4 py-3 flex items-center justify-between shrink-0">
            <div>
              <div className="text-sm text-[#E6EDF3]">Blur PII</div>
              <div className="text-[10px] text-[#6E7681]">DPDP Act 2023</div>
            </div>
            <button onClick={() => setBlurPII(!blurPII)} className={`w-10 h-5 rounded-full transition-colors relative ${blurPII ? 'bg-[#1F6FEB]' : 'bg-[#30363D]'}`}>
              <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${blurPII ? 'translate-x-5' : 'translate-x-0.5'}`} />
            </button>
          </div>
        </div>

        <div className="flex-1 bg-[#090D14] flex flex-col overflow-hidden border-r border-[#21262D]">
          <div className="h-36 border-b border-[#21262D] px-4 py-3 shrink-0">
            <div className="text-[10px] text-[#6E7681] uppercase tracking-wider mb-3 font-mono">Agent Pipeline</div>
            <div className="flex items-end gap-3 flex-wrap">
              {[
                { label: 'Maps', done: true, color: '#1F6FEB' },
                { label: 'OCR', done: p.artifacts.some((a) => ['UPI', 'BILL'].includes(a.type)), color: '#0EA5E9' },
                { label: 'WhatsApp', done: true, color: '#10B981' },
                { label: 'SMS', done: false, color: '#6EE7B7' },
                { label: 'Score', done: true, color: '#8B5CF6' },
                { label: 'Reconcile', done: true, color: '#EF4444' },
                { label: 'Comply', done: true, color: '#F97316' },
                { label: 'Report', done: true, color: '#3B82F6' },
              ].map((node) => (
                <div key={node.label} className="flex flex-col items-center gap-1">
                  <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-[10px] font-bold ${node.done ? 'text-black' : 'border-[#30363D] text-[#6E7681]'}`} style={node.done ? { backgroundColor: node.color, borderColor: node.color } : {}}>
                    {node.done ? '✓' : '○'}
                  </div>
                  <span className="text-[9px] text-[#6E7681] font-mono">{node.label}</span>
                </div>
              ))}
              <div className="flex flex-col items-center gap-1 ml-2">
                <div className="w-10 h-10 rounded-full border-2 border-[#7C3AED] flex items-center justify-center text-[10px] font-bold text-[#7C3AED]" style={{ boxShadow: '0 0 12px #7C3AED44' }}>
                  SUP
                </div>
                <span className="text-[9px] text-[#7C3AED] font-mono">Supervisor</span>
              </div>
            </div>
          </div>

          <div ref={logRef} className="flex-1 overflow-y-auto px-4 py-3 font-mono text-xs space-y-0.5">
            {logs.map((log, i) => (
              <div key={`${log.time}-${i}`} className={`flex gap-2 py-0.5 ${log.agent === 'SUPERVISOR' ? 'pl-4' : ''}`}>
                <span className="text-[#6E7681] shrink-0">{log.time}</span>
                <span className="shrink-0 font-semibold" style={{ color: log.color }}>
                  {log.agent === 'SUPERVISOR' ? '◆ ' : ''}
                  {log.agent}
                </span>
                <span className={`flex-1 ${log.agent === 'SUPERVISOR' ? 'text-[#C4B5FD]' : 'text-[#D4E6FF]'}`}>{log.msg}</span>
                {log.conf ? <span style={{ color: confColor(log.conf) }}>{log.conf.toFixed(2)}</span> : null}
              </div>
            ))}
            <div className="mt-2 px-3 py-2 bg-[#3FB9501A] border border-[#3FB95030] rounded-lg text-[#3FB950] text-xs font-mono">
              ✓ SESSION COMPLETE — All agents finished. Assessment ready for review.
            </div>
          </div>
        </div>

        <div className="w-96 shrink-0 bg-[#161B22] flex flex-col overflow-y-auto">
          <div className="px-4 py-3 border-b border-[#21262D] shrink-0">
            <div className="text-sm font-semibold text-[#8B949E]">Assessment</div>
          </div>
          <div className="px-4 py-4 space-y-4">
            <div className="bg-[#1C2128] border border-[#30363D] rounded-xl p-4">
              <div className="text-xs font-semibold text-[#6E7681] uppercase tracking-wider mb-3">Evidence Summary</div>
              <div className="grid grid-cols-5 gap-2 mb-3">
                {[
                  { label: 'WA', active: true },
                  { label: 'UPI', active: p.artifacts.some((a) => a.type === 'UPI') },
                  { label: 'SMS', active: false },
                  { label: 'Bill', active: p.artifacts.some((a) => a.type === 'BILL') },
                  { label: 'Maps', active: p.maps.verified },
                ].map((s) => (
                  <div key={s.label} className="flex flex-col items-center gap-1">
                    <div className={`w-2 h-2 rounded-full ${s.active ? 'bg-[#3FB950]' : 'bg-[#30363D]'}`} />
                    <span className="text-[9px] text-[#6E7681]">{s.label}</span>
                  </div>
                ))}
              </div>
              <div className="text-xs text-[#8B949E]">
                <span style={{ color: scoreColor(p.score) }}>{p.sourcesVerified}/{p.totalSources} sources</span> verified — <span style={{ color: scoreColor(p.score) }}>{p.confidenceBand}</span> confidence
              </div>
            </div>

            <div className="bg-[#1C2128] border border-[#30363D] rounded-xl p-4">
              <div className="text-xs font-semibold text-[#6E7681] uppercase tracking-wider mb-3">Financial Summary</div>
              {[
                { k: 'Monthly Revenue', v: fmtINR(p.monthlyRevenue), conf: 0.87 },
                { k: 'Weekly Average', v: fmtINR(p.weeklyAvg), conf: 0.85 },
                { k: 'Counterparties', v: p.counterparties, conf: 0.92 },
                { k: 'Revenue Gap', v: p.gapPct, conf: null },
                { k: 'Gap Classification', v: p.gapClass, conf: null },
              ].map((row) => (
                <div key={row.k} className="flex items-center justify-between py-2 border-b border-[#21262D] last:border-0 cursor-pointer hover:bg-[#21262D] -mx-1 px-1 rounded" onClick={() => setShowProvenance(row.k)}>
                  <span className="text-xs text-[#8B949E]">{row.k}</span>
                  <div className="flex items-center gap-2">
                    {row.conf ? (
                      <span className="text-[9px] px-1.5 py-0.5 rounded-full border" style={{ color: confColor(row.conf), borderColor: `${confColor(row.conf)}40`, backgroundColor: `${confColor(row.conf)}15` }}>
                        {row.conf}
                      </span>
                    ) : null}
                    <span className="text-xs font-medium text-[#E6EDF3]">{String(row.v)}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="bg-[#1C2128] border border-[#30363D] rounded-xl p-4">
              <div className="text-xs font-semibold text-[#6E7681] uppercase tracking-wider mb-3">CreditWarmthScore</div>
              <div className="flex items-center gap-4 mb-4">
                <div className="relative w-20 h-20 shrink-0">
                  <svg viewBox="0 0 80 80" className="w-full h-full -rotate-90">
                    <circle cx="40" cy="40" r="32" fill="none" stroke="#21262D" strokeWidth="7" />
                    <circle cx="40" cy="40" r="32" fill="none" stroke={scoreColor(p.score)} strokeWidth="7" strokeLinecap="round" strokeDasharray={`${p.score * 201} 201`} />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-lg font-bold text-white">{p.score.toFixed(2)}</span>
                    <span className="text-[9px] text-[#6E7681]">score</span>
                  </div>
                </div>
                <div>
                  <div className="text-2xl font-bold" style={{ color: scoreColor(p.score) }}>
                    {p.grade}
                  </div>
                  <div className="text-xs text-[#6E7681]">{p.confidenceBand} confidence</div>
                </div>
              </div>
              <div className="space-y-2">
                {p.signals.map((sig) => (
                  <div key={sig.name} className="flex items-center gap-2">
                    <span className="text-[11px] text-[#8B949E] w-36 shrink-0">{sig.name}</span>
                    <div className="flex-1 h-1.5 bg-[#21262D] rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${sig.value * 100}%`, backgroundColor: scoreColor(sig.value) }} />
                    </div>
                    <span className="text-[10px] font-mono text-[#8B949E] w-8 text-right">{sig.value.toFixed(2)}</span>
                    <span className={`text-[10px] font-mono w-10 text-right ${sig.shap.startsWith('+') ? 'text-[#3FB950]' : 'text-[#F85149]'}`}>{sig.shap}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-[#1C2128] border border-[#30363D] rounded-xl p-4">
              <div className="text-xs font-semibold text-[#6E7681] uppercase tracking-wider mb-3">Scenario Analysis</div>
              <div className="grid grid-cols-4 gap-1 mb-4 bg-[#0D1117] p-1 rounded-lg">
                {['current', 'gst', 'aa', 'gstaa'].map((tab) => (
                  <button key={tab} onClick={() => switchScenario(tab)} className={`py-1.5 rounded-md text-xs font-medium transition-all ${scenario === tab ? 'bg-[#21262D] text-white' : 'text-[#6E7681] hover:text-[#8B949E]'}`}>
                    {tab === 'current' ? 'Current' : tab.toUpperCase()}
                  </button>
                ))}
              </div>
              <div className="text-center py-3 bg-[#0D1117] rounded-xl">
                <div className="text-2xl font-bold font-mono" style={{ color: '#F5A623' }}>
                  {fmtINR(limitDisplay)}
                </div>
                {scenario !== 'current' && p.scenarios[scenario].delta ? (
                  <div className="text-xs text-[#3FB950] mt-1">+{fmtINR(p.scenarios[scenario].delta)} vs current</div>
                ) : null}
              </div>
            </div>

            <div className="bg-[#1C2128] border border-[#30363D] rounded-xl p-4">
              <div className="text-[10px] text-[#6E7681] uppercase tracking-wider mb-3">RM Decision</div>
              <div className="grid grid-cols-3 gap-2 mb-3">
                <button className="py-2.5 bg-[#3FB950] hover:bg-[#2ea043] text-black text-xs font-semibold rounded-lg">Approve</button>
                <button className="py-2.5 bg-transparent border border-[#30363D] hover:bg-[#21262D] text-[#8B949E] text-xs font-medium rounded-lg">Refer</button>
                <button className="py-2.5 bg-transparent border border-[#F8514930] hover:bg-[#F851491A] text-[#F85149] text-xs font-medium rounded-lg">Decline</button>
              </div>
              <div className="text-xs text-[#8B949E] leading-relaxed">{p.narrative}</div>
            </div>
          </div>
        </div>
      </div>

      {showProvenance ? (
        <div className="fixed right-0 top-0 h-full w-[360px] bg-[#11161d] border-l border-[#30363D] z-[70] p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-white">Provenance</h3>
            <button onClick={() => setShowProvenance(null)} className="text-[#8B949E] hover:text-white text-sm">
              Close
            </button>
          </div>
          <div className="text-xs text-[#8B949E] mb-2">Field</div>
          <div className="text-sm text-white mb-4">{showProvenance}</div>
          <div className="text-xs text-[#8B949E] leading-relaxed">
            This value is derived from multi-source reconciliation (WhatsApp, UPI, Maps, Bill). Full trace links are available in production API.
          </div>
        </div>
      ) : null}

      {clarification ? (
        <div className="fixed inset-0 bg-black/60 z-[80] flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-[#161B22] border border-[#30363D] rounded-xl p-4">
            <h3 className="text-sm font-semibold text-white mb-2">Clarification Required</h3>
            <p className="text-xs text-[#8B949E] mb-3">Raju case has seasonal variance. Confirm preferred loan tenure for final recommendation.</p>
            <input
              value={clarificationText}
              onChange={(e) => setClarificationText(e.target.value)}
              placeholder="e.g., 18-month tenure with seasonal repayment"
              className="w-full h-9 bg-[#0D1117] border border-[#30363D] rounded px-3 text-sm text-[#E6EDF3] mb-3"
            />
            <div className="flex gap-2 justify-end">
              <button onClick={() => setClarification(false)} className="px-3 py-1.5 text-xs border border-[#30363D] rounded text-[#8B949E] hover:text-white">
                Dismiss
              </button>
              <button
                onClick={() => {
                  if (!clarificationText.trim()) return;
                  setLogs((prev) => [
                    ...prev,
                    { time: '09:31:45.001', agent: 'SUPERVISOR', color: '#7C3AED', msg: `◆ Clarification received: ${clarificationText}`, conf: null },
                  ]);
                  setClarification(false);
                  setClarificationText('');
                }}
                className="px-3 py-1.5 text-xs bg-[#1F6FEB] rounded text-white"
              >
                Submit
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
