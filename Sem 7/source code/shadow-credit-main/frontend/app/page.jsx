'use client';

import { useEffect, useState } from 'react';

export default function LandingPage() {
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.querySelectorAll('.signal-bar-fill').forEach((bar) => {
              const w = bar.style.width;
              bar.style.width = '0%';
              setTimeout(() => {
                bar.style.width = w;
              }, 100);
            });
            observer.unobserve(e.target);
          }
        });
      },
      { threshold: 0.3 }
    );

    document.querySelectorAll('.signals-list').forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  function toggleTheme() {
    setTheme((t) => (t === 'light' ? 'dark' : 'light'));
  }

  return (
    <>
      <nav>
        <a href="#" className="nav-logo">
          <div className="nav-logo-mark">SC</div>
          <span className="nav-logo-name">Shadow Credit</span>
        </a>
        <div className="nav-right">
          <button className="theme-toggle" onClick={toggleTheme} id="themeBtn" title="Toggle theme">
            {theme === 'light' ? '☀' : '☽'}
          </button>
          <a href="/dashboard/meena-session-001" className="btn-ghost">Bank Portal</a>
          <a href="/apply" className="btn-primary">Apply Now</a>
        </div>
      </nav>

      <section className="hero">
        <div className="hero-tag">Built for India&apos;s informal economy</div>
        <h1 className="hero-h1">Credit for businesses<br />banks can&apos;t see.</h1>
        <p className="hero-sub">63 million kirana stores, tailors, and street vendors earn real money but have no CIBIL score. Shadow Credit reads their WhatsApp chats, UPI history, and bills — and produces a bank-ready credit memo in under 90 seconds.</p>
        <div className="hero-ctas">
          <a href="/apply" className="btn-hero-primary">Apply for Credit →</a>
          <a href="/dashboard" className="btn-hero-secondary">Bank RM Dashboard</a>
        </div>
        <p className="hero-trust">Protected under India&apos;s <a href="#">DPDP Act 2023</a> · No data stored beyond session · Zero CIBIL dependency</p>
      </section>

      <div className="stats-bar">
        <div className="stat">
          <div className="stat-num">63M+</div>
          <div className="stat-label">MSMEs invisible to banks</div>
          <div className="stat-sub">across India</div>
        </div>
        <div className="stat">
          <div className="stat-num">90s</div>
          <div className="stat-label">From upload to credit memo</div>
          <div className="stat-sub">end to end</div>
        </div>
        <div className="stat">
          <div className="stat-num">7</div>
          <div className="stat-label">AI agents working in parallel</div>
          <div className="stat-sub">per application</div>
        </div>
      </div>

      <section className="problem-section">
        <div className="section-eyebrow">The Problem</div>
        <h2 className="section-title">63 million businesses are invisible to banks.</h2>
        <p className="section-sub">They earn real money. They have real customers. The bank just literally cannot see them.</p>
        <div className="problem-inner">
          <div className="problem-story">
            A kirana owner in Pune runs his shop for <strong>8 years</strong>. Makes <strong>₹70,000 a month</strong>. Never misses a supplier payment. The bank says <strong>NO</strong> — because he can&apos;t show a salary slip or GST filing. His money is real. His business is real. The bank just literally cannot see it.
          </div>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-card-num">63M</div>
              <div className="stat-card-label">MSMEs with no formal credit history</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-num">11%</div>
              <div className="stat-card-label">Micro-enterprises with access to formal credit</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-num">₹25L Cr</div>
              <div className="stat-card-label">Unmet credit demand in informal sector</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-num">80%+</div>
              <div className="stat-card-label">Informal MSME loan applications rejected by banks</div>
            </div>
          </div>
        </div>
      </section>

      <section>
        <div className="section-eyebrow">Process</div>
        <h2 className="section-title">How it works</h2>
        <p className="section-sub">Three steps. No branch visit. No paperwork.</p>
        <div className="steps-grid">
          <div className="step">
            <span className="step-num">01</span>
            <div className="step-title">Upload your documents</div>
            <div className="step-body">Export your WhatsApp business chat, take screenshots of your UPI history, and photograph your electricity or rent bill. That is everything the system needs.</div>
            <div className="step-tags">
              <span className="tag">WhatsApp export</span>
              <span className="tag">UPI screenshots</span>
              <span className="tag">Electricity bill</span>
            </div>
          </div>
          <div className="step">
            <span className="step-num">02</span>
            <div className="step-title">Seven agents analyze</div>
            <div className="step-body">Eight specialized AI agents run in parallel — verifying your business, reading documents, detecting patterns, and reconciling every rupee into one verified income picture.</div>
            <div className="step-tags">
              <span className="tag">Identity</span>
              <span className="tag">OCR</span>
              <span className="tag">NLP</span>
              <span className="tag">Forensic</span>
            </div>
          </div>
          <div className="step">
            <span className="step-num">03</span>
            <div className="step-title">Bank memo in 90 seconds</div>
            <div className="step-body">A professional credit memo with your verified income, credit grade, and recommended limit — formatted for direct submission to any scheduled commercial bank or NBFC.</div>
            <div className="step-tags">
              <span className="tag">OCEN 4.0</span>
              <span className="tag">SHA-256 signed</span>
              <span className="tag">RBI compliant</span>
            </div>
          </div>
        </div>
      </section>

      <section style={{ background: 'var(--surface2)' }}>
        <div className="section-eyebrow">Transparency</div>
        <h2 className="section-title">What runs when you apply</h2>
        <p className="section-sub">Every agent has exactly one job. Nothing is a black box.</p>
        <div className="agents-grid">
          <div className="agent-card"><span className="agent-id">agent_00</span><div className="agent-name">Identity</div><div className="agent-desc">Verifies business on Google Maps — 47 reviews = real shop. Confirms identity against public records.</div></div>
          <div className="agent-card"><span className="agent-id">agent_01</span><div className="agent-name">WhatsApp</div><div className="agent-desc">Reads 400+ Hinglish messages. Extracts payment confirmations, vendor names, and financial events.</div></div>
          <div className="agent-card"><span className="agent-id">agent_02</span><div className="agent-name">UPI</div><div className="agent-desc">OCR on UPI screenshots. Analyzes transaction patterns, cash flow, and income consistency.</div></div>
          <div className="agent-card"><span className="agent-id">agent_02b</span><div className="agent-name">Bills</div><div className="agent-desc">Validates utility payments and uses electricity bill as address proof and business continuity signal.</div></div>
          <div className="agent-card"><span className="agent-id">agent_03</span><div className="agent-name">Cash Flow</div><div className="agent-desc">Parses OkCredit/Khatabook CSV — highest-confidence source. Computes income regularity and seasonality.</div></div>
          <div className="agent-card"><span className="agent-id">agent_04</span><div className="agent-name">Risk</div><div className="agent-desc">7 behavioral signals → CreditWarmthScore. Detects fraud signals and concentration risk across sources.</div></div>
          <div className="agent-card"><span className="agent-id">agent_05</span><div className="agent-name">Compliance</div><div className="agent-desc">12-item RBI MSME checklist. DPDP Act consent. Catches the WhatsApp vs UPI gap with RBI-cited explanation.</div></div>
          <div className="agent-card"><span className="agent-id">agent_07</span><div className="agent-name">Scorer</div><div className="agent-desc">Produces final credit limit recommendation and confidence score. Generates bank-facing PDF + owner Credit Passport.</div></div>
        </div>
      </section>

      <section className="cwscore-section">
        <div className="section-eyebrow">The Differentiator</div>
        <h2 className="section-title">CreditWarmthScore™</h2>
        <p className="section-sub">The same architecture used to catch fraudsters — applied in reverse.</p>
        <div className="cwscore-inner">
          <div className="cwscore-callout"><strong>Fraudsters warm up accounts before committing fraud.</strong> Legitimate businesses warm up toward creditworthiness. We read the same temporal signals — in reverse. Output: Score 0–1 → Grade A / A+ / B / B+ / C with full SHAP attribution on every signal.</div>
          <div className="signals-list">
            <div className="signal-row"><span className="signal-pct">28%</span><div className="signal-bar-track"><div className="signal-bar-fill" style={{ width: '28%' }} /></div><span className="signal-label">Income Regularity — is money coming in consistently?</span></div>
            <div className="signal-row"><span className="signal-pct">22%</span><div className="signal-bar-track"><div className="signal-bar-fill" style={{ width: '22%' }} /></div><span className="signal-label">Claim Consistency — does WhatsApp match UPI receipts?</span></div>
            <div className="signal-row"><span className="signal-pct">20%</span><div className="signal-bar-track"><div className="signal-bar-fill" style={{ width: '20%' }} /></div><span className="signal-label">Business Continuity — bill recency + Maps listing age</span></div>
            <div className="signal-row"><span className="signal-pct">15%</span><div className="signal-bar-track"><div className="signal-bar-fill" style={{ width: '15%' }} /></div><span className="signal-label">Seasonal Pattern — is low income seasonal or dying?</span></div>
            <div className="signal-row"><span className="signal-pct">10%</span><div className="signal-bar-track"><div className="signal-bar-fill" style={{ width: '10%' }} /></div><span className="signal-label">Network Reliability — 23 customers or 1 dominant buyer?</span></div>
            <div className="signal-row"><span className="signal-pct">5%</span><div className="signal-bar-track"><div className="signal-bar-fill" style={{ width: '5%' }} /></div><span className="signal-label">Data Source Diversity — how many sources agree?</span></div>
          </div>
        </div>
      </section>

      <section className="forensic-section">
        <div className="section-eyebrow">The Demo Moment</div>
        <h2 className="section-title">The agent that explains the gap</h2>
        <p className="section-sub">A dumb system flags discrepancies as fraud. Ours explains them with RBI data.</p>
        <div className="forensic-inner">
          <div className="forensic-demo">
            <div className="forensic-demo-header"><div className="dot dot-r" /><div className="dot dot-y" /><div className="dot dot-g" />&nbsp; agent_05 · forensic_accountant</div>
            <div className="forensic-body">
              <div className="forensic-gap">
                <div className="forensic-box"><div className="forensic-box-val">₹70,000</div><div className="forensic-box-label">WhatsApp claimed revenue</div></div>
                <div className="forensic-box red"><div className="forensic-box-val">₹44,000</div><div className="forensic-box-label">UPI confirmed receipts</div></div>
                <div className="forensic-box"><div className="forensic-box-val">37%</div><div className="forensic-box-label">Gap flagged</div></div>
              </div>
              <div className="forensic-verdict">
                <span className="forensic-verdict-label">Agent 05 verdict</span>
                <div className="forensic-verdict-text">Gap of 37% is consistent with <em>RBI MSME Survey 2023</em> cash transaction ratio for Kirana stores (25–35%). Not fraud. Cash transactions. <em>Recommend: PROCEED</em>.<br /><br />That&apos;s the difference between a bank rejecting a loan and approving it.</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section style={{ background: 'var(--surface2)' }}>
        <div className="section-eyebrow">Demo Personas</div>
        <h2 className="section-title">Three real business types</h2>
        <p className="section-sub">Every assessment adapts to the business&apos;s actual financial behavior.</p>
        <div className="personas-grid">
          <div className="persona-card"><div className="persona-header"><div className="persona-emoji">🟢</div><div><div className="persona-name">Suresh</div><div className="persona-biz">Mahadev Enterprises · Kirana · Sadashiv Peth</div></div></div><div className="persona-finding">Clean WhatsApp history. Google Maps verified with 47 reviews. Consistent ₹70k/month cash revenue. No digital UPI trail — explained by cash transactions per RBI survey data.</div><div className="persona-result"><span className="persona-limit">₹52,000</span><span className="persona-grade grade-green">Grade B+</span></div></div>
          <div className="persona-card"><div className="persona-header"><div className="persona-emoji">🟡</div><div><div className="persona-name">Meena</div><div className="persona-biz">Fashion House · Tailor · Kalyani Nagar</div></div></div><div className="persona-finding">WhatsApp-only evidence. Google Maps listing mismatch. No UPI history, no utility bill. Three flags raised but income signals still partially verifiable through chat analysis.</div><div className="persona-result"><span className="persona-limit">₹28,000</span><span className="persona-grade grade-yellow">Grade B · 3 flags</span></div></div>
          <div className="persona-card"><div className="persona-header"><div className="persona-emoji">🟢</div><div><div className="persona-name">Raju</div><div className="persona-biz">Tent &amp; Decoration · Events · Pimpri</div></div></div><div className="persona-finding">Strong October–March seasonal peak. ₹6.74L in 6 months. AI detects event business pattern, prevents penalizing low off-season income as business decline.</div><div className="persona-result"><span className="persona-limit">₹58,000</span><span className="persona-grade grade-green">Grade A−</span></div></div>
        </div>
      </section>

      <section>
        <div className="section-eyebrow">Outputs</div>
        <h2 className="section-title">Three documents. One assessment.</h2>
        <p className="section-sub">Every application produces three artifacts — for the bank, the owner, and the network.</p>
        <div className="outputs-grid">
          <div className="output-card"><div className="output-icon">📄</div><div className="output-name">Bank-Facing Credit Memo</div><div className="output-desc">SIDBI/PSU bank MSME credit appraisal format. Every number links back to the exact screenshot it came from. SHA-256 signed with QR verification code.</div><div className="output-tags"><span className="tag">PDF</span><span className="tag">SHA-256</span><span className="tag">RBI 12-item</span></div></div>
          <div className="output-card"><div className="output-icon">🪪</div><div className="output-name">Credit Passport</div><div className="output-desc">One page, bold, designed for someone who has never held a bank document. QR code: scan to verify document hasn&apos;t been tampered with. Owner hands this to any bank branch.</div><div className="output-tags"><span className="tag">Owner-facing</span><span className="tag">Tamper-evident</span><span className="tag">Hindi + English</span></div></div>
          <div className="output-card"><div className="output-icon">⚡</div><div className="output-name">OCEN 4.0 JSON</div><div className="output-desc">Open Credit Enablement Network compliant payload. Any NBFC or bank on the OCEN network can ingest directly — no custom integration required.</div><div className="output-tags"><span className="tag">OCEN 4.0</span><span className="tag">Machine-readable</span><span className="tag">Zero-integration</span></div></div>
        </div>
      </section>

      <section className="compliance-section">
        <div className="section-eyebrow">Security &amp; Compliance</div>
        <h2 className="section-title">Why judges won&apos;t question this</h2>
        <p className="section-sub">Every concern has a documented, technical answer.</p>
        <div className="compliance-table">
          <div className="compliance-row compliance-row-header"><div className="compliance-concern">Concern</div><div className="compliance-answer">Our answer</div></div>
          <div className="compliance-row"><div className="compliance-concern">Privacy</div><div className="compliance-answer">AES-256-GCM encryption on every PII field before SQLite write. Zero plaintext PII at rest.</div></div>
          <div className="compliance-row"><div className="compliance-concern">DPDP Act 2023</div><div className="compliance-answer">Explicit consent before processing. Consent hash stored immutably. Right to erasure via DELETE /sessions/{"{id}"}.</div></div>
          <div className="compliance-row"><div className="compliance-concern">Audit Trail</div><div className="compliance-answer">Immutable audit log via database trigger that prevents UPDATE/DELETE. Every agent action timestamped.</div></div>
          <div className="compliance-row"><div className="compliance-concern">Fraud Prevention</div><div className="compliance-answer">WhatsApp + UPI + SMS must cross-validate. Any discrepancy flagged with RBI-cited explanation, not rejection.</div></div>
          <div className="compliance-row"><div className="compliance-concern">Tamper-evident PDFs</div><div className="compliance-answer">SHA-256 hash of PDF stored in DB. QR code on PDF links to public verify endpoint. Signed on creation.</div></div>
          <div className="compliance-row"><div className="compliance-concern">RBI Compliance</div><div className="compliance-answer">12-item RBI MSME 2025 checklist run on every single assessment before output is generated.</div></div>
        </div>
      </section>

      <section className="diff-section">
        <div className="section-eyebrow">Why nobody else has this</div>
        <h2 className="section-title">What makes Shadow Credit different</h2>
        <p className="section-sub">Five technical properties that cannot be replicated with a chatbot wrapper.</p>
        <div className="diff-grid">
          <div className="diff-card"><span className="diff-num">01</span><div className="diff-title">Multi-source verification</div><div className="diff-body">WhatsApp says 50k. UPI confirms 32k. SMS verifies 34.5k. Google Maps shows 47 reviews. Five independent signals agreeing is evidence, not assumption.</div></div>
          <div className="diff-card"><span className="diff-num">02</span><div className="diff-title">Full provenance</div><div className="diff-body">Every number in the bank memo links back to the exact message it came from. Click ₹44,000 → see the reconciliation trail from 3 sources.</div></div>
          <div className="diff-card"><span className="diff-num">03</span><div className="diff-title">Explainable AI</div><div className="diff-body">SHAP values on every signal. The Supervisor narrates decisions in real time. Nothing is a black box — every credit decision is auditable.</div></div>
          <div className="diff-card"><span className="diff-num">04</span><div className="diff-title">OCEN-native output</div><div className="diff-body">Output plugs directly into India&apos;s Open Credit Enablement Network. Any lender can ingest without custom integration. No last-mile friction.</div></div>
          <div className="diff-card"><span className="diff-num">05</span><div className="diff-title">Agentic architecture</div><div className="diff-body">The Supervisor has a goal: maximize confidence in 90 seconds. It decides agent order, pauses for human input, resumes. Goal-directed behavior, not a fixed pipeline.</div></div>
          <div className="diff-card" style={{ background: 'var(--surface2)' }}><span className="diff-num" style={{ color: 'var(--text3)' }}>Stack</span><div className="diff-title">Technical foundation</div><div className="diff-body" style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 8 }}><span style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--text2)' }}>FastAPI · Next.js 14 · SQLite</span><span style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--text2)' }}>Groq LLaMA 3.1 70B · Claude · XGBoost</span><span style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--text2)' }}>PaddleOCR · ReportLab · OCEN 4.0</span></div></div>
        </div>
      </section>

      <section>
        <div className="section-eyebrow">Credit Formula</div>
        <h2 className="section-title">The math is transparent</h2>
        <p className="section-sub">No hidden weights. No black-box model. Every variable is traceable to a source document.</p>
        <div className="formula-block"><span className="formula-label">Credit Formula</span><span className="formula-text">Credit Limit = Median Monthly Inflow × 3 × Regularity × Continuity × Concentration Adjustment</span></div>
      </section>

      <section className="cta-section">
        <h2 className="cta-title">See it work in<br />90 seconds.</h2>
        <p className="cta-sub">Upload three files. Watch seven agents analyze. Get a bank-ready credit memo.</p>
        <div className="cta-btns">
          <a href="/apply" className="btn-hero-primary">Apply for Credit →</a>
          <a href="/dashboard" className="btn-hero-secondary">Bank RM Dashboard</a>
        </div>
      </section>

      <footer>
        <div className="footer-brand">
          <div className="footer-brand-name"><div className="nav-logo-mark" style={{ width: 28, height: 28, fontSize: 11 }}>SC</div>Shadow Credit</div>
          <div className="footer-brand-desc">AI credit reconstruction for India&apos;s informal economy. DPDP Act 2023 compliant.</div>
        </div>
        <div className="footer-middle">
          <div className="footer-event">Built for ORCHESTRON 2026</div>
          <div className="footer-event-sub">ICEM Techno Fest · 27 March 2026</div>
        </div>
        <div className="footer-links">
          <a href="/apply" className="footer-link">Apply for Credit</a>
          <a href="/dashboard/meena-session-001" className="footer-link">Bank Portal</a>
        </div>
      </footer>

      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap');
        :root[data-theme="light"] { --bg:#f0ede8;--bg2:#e8e4de;--surface:#ffffff;--surface2:#f5f2ed;--border:#d8d4ce;--text:#1a1814;--text2:#6b665e;--text3:#9a958e;--accent:#1a1814;--accent-fg:#f0ede8;--tag-bg:#e0ddd8;--mono-bg:#e8e4de;--code:#2d5a3d;--green:#2d5a3d;--green-bg:#e8f0ea;--yellow-bg:#f5f0e0;--yellow:#8a7020; }
        :root[data-theme="dark"] { --bg:#0f0e0c;--bg2:#161410;--surface:#1c1a16;--surface2:#221f1a;--border:#2e2b25;--text:#e8e4dc;--text2:#8a867e;--text3:#5a5650;--accent:#e8e4dc;--accent-fg:#0f0e0c;--tag-bg:#2e2b25;--mono-bg:#161410;--code:#7ec89a;--green:#7ec89a;--green-bg:#1a2e20;--yellow-bg:#2a2410;--yellow:#c8a840; }
        *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
        html{scroll-behavior:smooth}
        body{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text);line-height:1.6;transition:background .3s ease,color .3s ease;overflow-x:hidden}
        nav{position:sticky;top:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:18px 48px;background:var(--bg);border-bottom:1px solid var(--border)}
        .nav-logo{display:flex;align-items:center;gap:10px;text-decoration:none}.nav-logo-mark{width:36px;height:36px;background:var(--text);color:var(--bg);border-radius:8px;display:flex;align-items:center;justify-content:center;font-family:'DM Mono',monospace;font-size:13px;font-weight:500;letter-spacing:-.5px;flex-shrink:0}.nav-logo-name{font-size:15px;font-weight:500;color:var(--text)}.nav-right{display:flex;align-items:center;gap:12px}
        .theme-toggle{width:36px;height:36px;border-radius:50%;border:1px solid var(--border);background:var(--surface);cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:15px;color:var(--text)}.theme-toggle:hover{background:var(--surface2)}
        .btn-ghost{padding:8px 18px;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--text);font-size:14px;cursor:pointer;text-decoration:none}.btn-ghost:hover{background:var(--surface)}
        .btn-primary{padding:8px 20px;border-radius:6px;border:none;background:var(--accent);color:var(--accent-fg);font-size:14px;font-weight:500;cursor:pointer;text-decoration:none}.btn-primary:hover{opacity:.85}
        .hero{min-height:calc(100vh - 61px);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:80px 24px}.hero-tag{display:inline-flex;align-items:center;gap:8px;padding:6px 14px;border-radius:100px;border:1px solid var(--border);background:var(--surface);font-size:13px;color:var(--text2);margin-bottom:36px}.hero-tag::before{content:'';width:6px;height:6px;border-radius:50%;background:var(--green)}
        .hero-h1{font-family:'Playfair Display',serif;font-size:clamp(52px,8vw,96px);font-weight:900;line-height:1;letter-spacing:-2px;color:var(--text);margin-bottom:28px}
        .hero-sub{font-size:17px;color:var(--text2);max-width:540px;line-height:1.7;margin-bottom:44px;font-weight:300}.hero-ctas{display:flex;gap:12px;flex-wrap:wrap;justify-content:center}
        .btn-hero-primary{padding:13px 28px;border-radius:8px;border:none;background:var(--accent);color:var(--accent-fg);font-size:15px;font-weight:500;cursor:pointer;display:flex;align-items:center;gap:8px;text-decoration:none}.btn-hero-primary:hover{opacity:.82}
        .btn-hero-secondary{padding:13px 28px;border-radius:8px;border:1px solid var(--border);background:var(--surface);color:var(--text);font-size:15px;cursor:pointer;text-decoration:none}.btn-hero-secondary:hover{background:var(--surface2)}
        .hero-trust{margin-top:32px;font-size:12px;color:var(--text3)}.hero-trust a{color:var(--text2);text-decoration:underline;text-underline-offset:3px}
        .stats-bar{margin:0 48px 80px;border:1px solid var(--border);border-radius:12px;background:var(--surface);display:grid;grid-template-columns:1fr 1fr 1fr;overflow:hidden}
        .stat{padding:36px 40px;text-align:center;border-right:1px solid var(--border)}.stat:last-child{border-right:none}.stat-num{font-family:'Playfair Display',serif;font-size:52px;font-weight:700;letter-spacing:-2px;color:var(--text);line-height:1;margin-bottom:8px}.stat-label{font-size:14px;color:var(--text2)}.stat-sub{font-size:12px;color:var(--text3)}
        section{padding:80px 48px}.section-eyebrow{font-family:'DM Mono',monospace;font-size:11px;font-weight:500;letter-spacing:2px;text-transform:uppercase;color:var(--text3);text-align:center;margin-bottom:16px}.section-title{font-family:'Playfair Display',serif;font-size:clamp(36px,5vw,56px);font-weight:700;letter-spacing:-1.5px;color:var(--text);text-align:center;margin-bottom:14px;line-height:1.1}.section-sub{font-size:16px;color:var(--text2);text-align:center;max-width:480px;margin:0 auto 56px;font-weight:300}
        .steps-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:1px;background:var(--border);border:1px solid var(--border);border-radius:12px;overflow:hidden;max-width:960px;margin:0 auto}.step{background:var(--surface);padding:40px 36px}.step-num{font-family:'DM Mono',monospace;font-size:11px;color:var(--text3);letter-spacing:1px;margin-bottom:20px;display:block}.step-title{font-family:'Playfair Display',serif;font-size:22px;font-weight:700;color:var(--text);margin-bottom:14px;letter-spacing:-.5px}.step-body{font-size:14px;color:var(--text2);line-height:1.65;font-weight:300}.step-tags{margin-top:20px;display:flex;flex-wrap:wrap;gap:6px}.tag{padding:4px 10px;border-radius:4px;background:var(--tag-bg);font-family:'DM Mono',monospace;font-size:11px;color:var(--text2)}
        .problem-section{background:var(--surface2)}.problem-inner{max-width:800px;margin:0 auto}.problem-story{border-left:3px solid var(--border);padding:24px 32px;background:var(--surface);border-radius:0 8px 8px 0;margin-bottom:40px;font-size:16px;color:var(--text2);line-height:1.8;font-style:italic;font-weight:300}.problem-story strong{color:var(--text);font-style:normal;font-weight:500}.stats-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.stat-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:28px 24px}.stat-card-num{font-family:'Playfair Display',serif;font-size:38px;font-weight:700;color:var(--text);letter-spacing:-1.5px;margin-bottom:6px}.stat-card-label{font-size:14px;color:var(--text2);font-weight:300}
        .agents-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;max-width:1100px;margin:0 auto}.agent-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:22px 20px}.agent-id{font-family:'DM Mono',monospace;font-size:10px;color:var(--text3);letter-spacing:1px;margin-bottom:8px;display:block}.agent-name{font-size:15px;font-weight:500;color:var(--text);margin-bottom:6px}.agent-desc{font-size:13px;color:var(--text2);font-weight:300;line-height:1.5}
        .cwscore-section{background:var(--surface2)}.cwscore-inner{max-width:760px;margin:0 auto}.cwscore-callout{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:32px 36px;margin-bottom:32px;font-size:16px;color:var(--text2);line-height:1.7;font-weight:300}.cwscore-callout strong{color:var(--text);font-weight:500}.signals-list{display:flex;flex-direction:column;gap:10px}.signal-row{display:flex;align-items:center;gap:14px;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px 18px}.signal-pct{font-family:'DM Mono',monospace;font-size:13px;color:var(--text);width:42px;flex-shrink:0;font-weight:500}.signal-bar-track{flex:1;height:4px;background:var(--border);border-radius:2px;overflow:hidden}.signal-bar-fill{height:100%;background:var(--text);border-radius:2px;transition:width 1s ease}.signal-label{font-size:13px;color:var(--text2);width:190px;flex-shrink:0;font-weight:300}
        .forensic-inner{max-width:780px;margin:0 auto}.forensic-demo{background:var(--surface);border:1px solid var(--border);border-radius:12px;overflow:hidden}.forensic-demo-header{padding:14px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px;font-family:'DM Mono',monospace;font-size:11px;color:var(--text3);letter-spacing:1px;text-transform:uppercase}.dot{width:8px;height:8px;border-radius:50%}.dot-r{background:#ff5f57}.dot-y{background:#ffbd2e}.dot-g{background:#28c840}.forensic-body{padding:28px 32px}.forensic-gap{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:28px}.forensic-box{border:1px solid var(--border);border-radius:8px;padding:18px 16px;text-align:center}.forensic-box-val{font-family:'Playfair Display',serif;font-size:28px;font-weight:700;color:var(--text);letter-spacing:-1px;margin-bottom:4px}.forensic-box-label{font-size:12px;color:var(--text3);font-weight:300}.forensic-box.red .forensic-box-val{color:#c0392b}.forensic-verdict{background:var(--green-bg);border:1px solid var(--green);border-radius:8px;padding:20px 22px}.forensic-verdict-label{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:var(--green);margin-bottom:10px;display:block}.forensic-verdict-text{font-size:14px;color:var(--text);line-height:1.7;font-weight:300}.forensic-verdict-text em{font-style:normal;font-family:'DM Mono',monospace;font-size:13px;color:var(--green)}
        .personas-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;max-width:960px;margin:0 auto}.persona-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:28px 24px}.persona-header{display:flex;align-items:center;gap:12px;margin-bottom:18px}.persona-emoji{font-size:28px}.persona-name{font-size:15px;font-weight:500;color:var(--text)}.persona-biz{font-size:12px;color:var(--text3);font-weight:300;margin-top:2px}.persona-finding{font-size:13px;color:var(--text2);font-weight:300;line-height:1.6;margin-bottom:18px}.persona-result{display:flex;align-items:center;justify-content:space-between;padding:12px 14px;border-radius:8px;border:1px solid var(--border);background:var(--surface2)}.persona-limit{font-size:16px;font-weight:500;color:var(--text)}.persona-grade{font-family:'DM Mono',monospace;font-size:12px;padding:3px 8px;border-radius:4px;font-weight:500}.grade-green{background:var(--green-bg);color:var(--green)}.grade-yellow{background:var(--yellow-bg);color:var(--yellow)}
        .outputs-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;max-width:960px;margin:0 auto}.output-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:32px 28px}.output-icon{width:44px;height:44px;border-radius:10px;border:1px solid var(--border);display:flex;align-items:center;justify-content:center;font-size:20px;margin-bottom:18px}.output-name{font-size:16px;font-weight:500;color:var(--text);margin-bottom:10px}.output-desc{font-size:13px;color:var(--text2);line-height:1.6;font-weight:300}.output-tags{margin-top:16px;display:flex;flex-wrap:wrap;gap:6px}
        .compliance-section{background:var(--surface2)}.compliance-table{max-width:820px;margin:0 auto;border:1px solid var(--border);border-radius:12px;overflow:hidden;background:var(--surface)}.compliance-row{display:grid;grid-template-columns:200px 1fr;border-bottom:1px solid var(--border)}.compliance-row:last-child{border-bottom:none}.compliance-concern{padding:18px 22px;font-size:14px;font-weight:500;color:var(--text);border-right:1px solid var(--border);display:flex;align-items:center}.compliance-answer{padding:18px 22px;font-size:13px;color:var(--text2);font-weight:300;line-height:1.6;display:flex;align-items:center}.compliance-row-header .compliance-concern,.compliance-row-header .compliance-answer{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:var(--text3);font-weight:400;padding-top:14px;padding-bottom:14px}
        .diff-section{background:var(--surface2)}.diff-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;max-width:820px;margin:0 auto}.diff-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:28px 24px}.diff-num{font-family:'DM Mono',monospace;font-size:10px;color:var(--text3);letter-spacing:1px;margin-bottom:10px;display:block}.diff-title{font-size:15px;font-weight:500;color:var(--text);margin-bottom:8px}.diff-body{font-size:13px;color:var(--text2);font-weight:300;line-height:1.6}
        .formula-block{max-width:820px;margin:40px auto 0;background:var(--mono-bg);border:1px solid var(--border);border-radius:10px;padding:24px 32px;display:flex;align-items:center;gap:24px}.formula-label{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--text3);flex-shrink:0}.formula-text{font-family:'DM Mono',monospace;font-size:13px;color:var(--text)}
        .cta-section{padding:100px 48px;text-align:center}.cta-title{font-family:'Playfair Display',serif;font-size:clamp(40px,6vw,72px);font-weight:900;letter-spacing:-2px;color:var(--text);margin-bottom:24px;line-height:1.05}.cta-sub{font-size:17px;color:var(--text2);margin-bottom:44px;font-weight:300;max-width:460px;margin-left:auto;margin-right:auto}.cta-btns{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-bottom:56px}
        footer{border-top:1px solid var(--border);padding:40px 48px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:40px;align-items:start}.footer-brand-name{font-size:15px;font-weight:500;margin-bottom:8px;display:flex;align-items:center;gap:8px}.footer-brand-desc{font-size:13px;color:var(--text3);font-weight:300;line-height:1.6}.footer-middle{text-align:center}.footer-event{font-size:12px;font-weight:500;color:var(--text2);margin-bottom:4px}.footer-event-sub{font-size:12px;color:var(--text3)}.footer-links{text-align:right}.footer-link{display:block;font-size:13px;color:var(--text2);text-decoration:none;margin-bottom:6px}.footer-link:hover{color:var(--text)}
        @media (max-width:768px){nav{padding:14px 20px}section{padding:60px 20px}.stats-bar{margin:0 20px 60px;grid-template-columns:1fr}.stat{border-right:none;border-bottom:1px solid var(--border)}.stat:last-child{border-bottom:none}.steps-grid,.personas-grid,.outputs-grid,.diff-grid{grid-template-columns:1fr}.agents-grid{grid-template-columns:1fr 1fr}.compliance-row{grid-template-columns:1fr}.compliance-concern{border-right:none;border-bottom:1px solid var(--border)}footer{grid-template-columns:1fr;text-align:left}.footer-links,.footer-middle{text-align:left}.formula-block{flex-direction:column;align-items:flex-start;gap:8px}.forensic-gap{grid-template-columns:1fr}.hero-h1{letter-spacing:-1px}}
      `}</style>
    </>
  );
}
