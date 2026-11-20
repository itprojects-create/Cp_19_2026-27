'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

const SEEDED_CASES = [
  {
    id: 'SC-4F2A1B',
    sessionId: 'meena-session-001',
    applicant: 'Meena Devi',
    business: 'Meena Saree & Cloth Store',
    type: 'Tailor / Clothing',
    location: 'Kalyani Nagar, Pune',
    submitted: '2 hours ago',
    status: 'COMPLETE',
    score: 0.74,
    limit: '₹1,20,000',
    persona: 'meena',
  },
  {
    id: 'SC-8B3D2E',
    sessionId: 'suresh-session-001',
    applicant: 'Suresh Sharma',
    business: 'Mahadev Enterprises',
    type: 'Kirana / General Store',
    location: 'Sadashiv Peth, Pune',
    submitted: '45 mins ago',
    status: 'COMPLETE',
    score: 0.61,
    limit: '₹95,000',
    persona: 'suresh',
  },
  {
    id: 'SC-2C9F4A',
    sessionId: 'raju-session-001',
    applicant: 'Raju Patil',
    business: 'Raju General Store',
    type: 'Kirana / General Store',
    location: 'Chinchwad, Pune',
    submitted: '3 hours ago',
    status: 'REVIEW',
    score: 0.58,
    limit: '₹72,000',
    persona: 'raju',
  },
];

const STATUS_STYLES = {
  COMPLETE: 'bg-[#3FB9501A] text-[#3FB950] border border-[#3FB95030]',
  REVIEW: 'bg-[#D299221A] text-[#D29922] border border-[#D2992230]',
  PROCESSING: 'bg-[#D299221A] text-[#D29922] border border-[#D2992230]',
  NEW: 'bg-[#1F6FEB1A] text-[#1F6FEB] border border-[#1F6FEB30]',
  APPROVED: 'bg-[#3FB9501A] text-[#3FB950] border border-[#3FB95030]',
  REJECTED: 'bg-[#F851491A] text-[#F85149] border border-[#F8514930]',
};

const STATUS_LABELS = {
  COMPLETE: 'Ready',
  REVIEW: 'Requires Input',
  PROCESSING: 'Processing',
  NEW: 'New',
  APPROVED: 'Approved',
  REJECTED: 'Rejected',
};

const scoreColor = (s) => (s >= 0.75 ? '#3FB950' : s >= 0.5 ? '#D29922' : '#F85149');

export default function DashboardPage() {
  const router = useRouter();
  const [cases, setCases] = useState(SEEDED_CASES);
  const [filter, setFilter] = useState('ALL');
  const [search, setSearch] = useState('');
  const [wsStatus, setWsStatus] = useState('disconnected');

  useEffect(() => {
    let ws;
    try {
      ws = new WebSocket('ws://localhost:8000/ws/dashboard');
      ws.onopen = () => setWsStatus('connected');
      ws.onclose = () => setWsStatus('disconnected');
      ws.onerror = () => setWsStatus('disconnected');
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          if (msg.type === 'NEW_SESSION') {
            setCases((prev) => [
              {
                id: `SC-${String(msg.sessionId || '').slice(0, 6).toUpperCase()}`,
                sessionId: msg.sessionId,
                applicant: msg.data?.businessName || 'New Applicant',
                business: msg.data?.businessName || '—',
                type: msg.data?.businessType || '—',
                location: msg.data?.location || '—',
                submitted: 'Just now',
                status: 'NEW',
                score: 0,
                limit: '—',
                persona: 'live',
              },
              ...prev,
            ]);
          }
          if (msg.type === 'SESSION_STATUS_UPDATE') {
            setCases((prev) =>
              prev.map((c) =>
                c.sessionId === msg.sessionId
                  ? { ...c, status: msg.status, score: msg.score || c.score, limit: msg.limit || c.limit }
                  : c
              )
            );
          }
        } catch {}
      };
    } catch {}
    return () => {
      if (ws) ws.close();
    };
  }, []);

  const filtered = cases.filter((c) => {
    const matchFilter = filter === 'ALL' || c.status === filter;
    const s = search.toLowerCase();
    const matchSearch = !search || c.applicant.toLowerCase().includes(s) || c.business.toLowerCase().includes(s);
    return matchFilter && matchSearch;
  });

  const counts = {
    ALL: cases.length,
    NEW: cases.filter((c) => c.status === 'NEW').length,
    PROCESSING: cases.filter((c) => c.status === 'PROCESSING').length,
    COMPLETE: cases.filter((c) => c.status === 'COMPLETE').length,
    REVIEW: cases.filter((c) => c.status === 'REVIEW').length,
  };

  return (
    <div className="min-h-screen bg-[#0D1117] text-[#E6EDF3]">
      <div className="h-12 bg-[#161B22] border-b border-[#21262D] flex items-center px-6 justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 bg-[#1F6FEB] rounded-lg flex items-center justify-center text-white text-xs font-bold">SC</div>
          <span className="text-white font-semibold text-sm">Shadow Credit</span>
          <span className="text-[#6E7681] text-sm">/ Credit Assessment Dashboard</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-[#6E7681]">
            <div className={`w-2 h-2 rounded-full ${wsStatus === 'connected' ? 'bg-[#3FB950]' : 'bg-[#6E7681]'}`} />
            {wsStatus === 'connected' ? 'Live' : 'Offline'}
          </div>
          <button onClick={() => window.open('/apply', '_blank')} className="px-3 py-1.5 bg-[#1F6FEB] text-white text-sm rounded-lg hover:bg-[#388BFD] transition-colors">
            + New Assessment
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Cases</h1>
            <p className="text-[#8B949E] text-sm mt-0.5">{cases.length} total assessments</p>
          </div>
          <input
            type="text"
            placeholder="Search applicant or business..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-64 h-8 bg-[#0D1117] border border-[#30363D] rounded-lg px-3 text-sm text-[#E6EDF3] placeholder-[#6E7681] focus:outline-none focus:border-[#1F6FEB]"
          />
        </div>

        <div className="flex gap-1 mb-4 border-b border-[#21262D]">
          {['ALL', 'NEW', 'PROCESSING', 'COMPLETE', 'REVIEW'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 text-sm font-medium transition-colors relative ${filter === f ? 'text-white' : 'text-[#8B949E] hover:text-[#E6EDF3]'}`}
            >
              {f === 'ALL' ? 'All' : STATUS_LABELS[f] || f}
              {counts[f] > 0 && (
                <span className={`ml-1.5 text-xs px-1.5 py-0.5 rounded-full ${filter === f ? 'bg-[#1F6FEB20] text-[#1F6FEB]' : 'bg-[#21262D] text-[#6E7681]'}`}>
                  {counts[f]}
                </span>
              )}
              {filter === f && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#1F6FEB] rounded-t" />}
            </button>
          ))}
        </div>

        <div className="rounded-xl border border-[#21262D] overflow-hidden">
          <div className="grid grid-cols-[80px_1fr_140px_160px_100px_120px_80px_100px_40px] h-9 bg-[#161B22] border-b border-[#30363D] px-4 items-center">
            {['CASE ID', 'APPLICANT', 'BUSINESS', 'LOCATION', 'SUBMITTED', 'STATUS', 'SCORE', 'LIMIT', ''].map((col) => (
              <div key={col} className="text-[11px] font-semibold text-[#6E7681] uppercase tracking-wider">
                {col}
              </div>
            ))}
          </div>

          {filtered.length === 0 ? (
            <div className="py-16 text-center">
              <div className="text-3xl mb-3">📋</div>
              <div className="text-[#8B949E] text-sm">No cases found</div>
            </div>
          ) : (
            filtered.map((c) => (
              <div
                key={c.id}
                onClick={() => router.push(`/dashboard/${c.sessionId}`)}
                className="grid grid-cols-[80px_1fr_140px_160px_100px_120px_80px_100px_40px] h-11 px-4 items-center border-b border-[#21262D] last:border-b-0 hover:bg-[#21262D] cursor-pointer transition-colors group"
                style={{ borderLeft: c.status === 'PROCESSING' ? '2px solid #D29922' : '2px solid transparent' }}
              >
                <div className="text-[11px] font-mono text-[#6E7681]">{c.id}</div>
                <div className="text-sm font-medium text-white">{c.applicant}</div>
                <div className="text-sm text-[#8B949E] truncate">{c.business}</div>
                <div className="text-sm text-[#8B949E]">{c.location}</div>
                <div className="text-sm text-[#6E7681]">{c.submitted}</div>
                <div>
                  <span className={`text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full ${STATUS_STYLES[c.status] || ''}`}>
                    {c.status === 'PROCESSING' && <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#D29922] mr-1 animate-pulse" />}
                    {STATUS_LABELS[c.status] || c.status}
                  </span>
                </div>
                <div className="text-sm font-mono" style={{ color: c.score > 0 ? scoreColor(c.score) : '#6E7681' }}>
                  {c.score > 0 ? c.score.toFixed(2) : '—'}
                </div>
                <div className="text-sm font-semibold text-white">{c.limit}</div>
                <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                  <button className="text-xs text-[#8B949E] hover:text-white px-2 py-1 rounded">View</button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
