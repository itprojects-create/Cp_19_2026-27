"use client";

import React, { useEffect, useState } from "react";
import { animateCount } from "../../lib/animations";
import { formatDate, formatINR } from "../../lib/formatters";
import Button from "../ui/Button";

export default function ResultCard({
  amount,
  grade,
  sources,
  assessedAt,
  onDownload,
  onShare,
}: {
  amount: number;
  grade: string;
  sources: string;
  assessedAt: string;
  onDownload: () => void;
  onShare: () => void;
}) {
  const [display, setDisplay] = useState(0);

  useEffect(() => animateCount(0, amount, 1200, (v) => setDisplay(v)), [amount]);

  return (
    <div style={{ display: "grid", gap: 20 }}>
      <div style={{ textAlign: "center", display: "grid", gap: 8 }}>
        <div style={{ fontSize: 56 }}>✅</div>
        <div style={{ color: "var(--color-text-secondary)" }}>You qualify for</div>
        <div style={{ fontSize: 40, fontWeight: 700, color: "var(--color-accent)" }}>{formatINR(display)}</div>
        <div style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>Recommended Loan Limit</div>
      </div>
      <div style={{ border: "1px solid var(--color-border)", borderRadius: 16, background: "white" }}>
        <Row k="Assessment Grade" v={grade} accent />
        <Row k="Sources Verified" v={sources} />
        <Row k="Assessed on" v={formatDate(assessedAt)} />
      </div>
      <div style={{ border: "1px solid var(--color-border)", borderRadius: 16, background: "white", padding: 16 }}>
        <div style={{ fontWeight: 600, marginBottom: 8 }}>What happens next?</div>
        <div style={{ fontSize: 14, color: "var(--color-text-secondary)", lineHeight: 1.6 }}>
          📞 Your bank relationship manager will review this assessment and contact you within 24 hours to discuss your loan.
        </div>
      </div>
      <Button onClick={onDownload}>Download My Assessment</Button>
      <Button variant="secondary" onClick={onShare}>
        Share with Bank
      </Button>
      <div style={{ textAlign: "center", fontSize: 12, color: "var(--color-text-secondary)" }}>Shadow Credit · Powered by AI · RBI Compliant</div>
    </div>
  );
}

function Row({ k, v, accent }: { k: string; v: string; accent?: boolean }) {
  return (
    <div style={{ minHeight: 48, padding: "0 16px", borderBottom: "1px solid var(--color-border)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
      <span>{k}</span>
      <span style={{ color: accent ? "var(--color-accent)" : undefined, fontWeight: accent ? 700 : 500 }}>{v}</span>
    </div>
  );
}

