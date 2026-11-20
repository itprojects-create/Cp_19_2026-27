"use client";

import React, { useRef } from "react";
import UploadCard from "../ui/UploadCard";
import Badge from "../ui/Badge";

type FileMap = {
  whatsapp?: File[];
  upi?: File[];
  bill?: File[];
  sms?: File[];
};

export default function DocumentUploadGrid({
  files,
  onFiles,
}: {
  files: FileMap;
  onFiles: (key: keyof FileMap, selected: FileList | null) => void;
}) {
  const refs = {
    whatsapp: useRef<HTMLInputElement>(null),
    upi: useRef<HTMLInputElement>(null),
    bill: useRef<HTMLInputElement>(null),
    sms: useRef<HTMLInputElement>(null),
  };

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <UploadCard title="WhatsApp Business Chat" subtitle="Your chats with customers and suppliers" icon="💬" required uploaded={Boolean(files.whatsapp?.length)} onPick={() => refs.whatsapp.current?.click()}>
        <button type="button" style={{ fontSize: 13, color: "var(--color-accent)", background: "none", border: "none", padding: 0, textDecoration: "underline" }}>
          How to export?
        </button>
      </UploadCard>
      <input ref={refs.whatsapp} type="file" accept=".txt,.zip" hidden onChange={(e) => onFiles("whatsapp", e.target.files)} />

      <UploadCard title="UPI Payment Screenshots" subtitle="PhonePe, GPay, Paytm, BHIM — any digital payment" icon="📱" required uploaded={Boolean(files.upi?.length)} onPick={() => refs.upi.current?.click()}>
        {files.upi?.length ? <div style={{ fontSize: 13 }}>{`${files.upi.length} file(s) selected`}</div> : null}
      </UploadCard>
      <input ref={refs.upi} type="file" accept="image/*" multiple hidden onChange={(e) => onFiles("upi", e.target.files)} />

      <UploadCard title="Electricity Bill" subtitle="Increases your loan amount by ₹15,000–₹20,000" icon="⚡" uploaded={Boolean(files.bill?.length)} onPick={() => refs.bill.current?.click()}>
        <Badge variant="complete">+₹15k–₹20k</Badge>
      </UploadCard>
      <input ref={refs.bill} type="file" accept="image/*,.pdf" hidden onChange={(e) => onFiles("bill", e.target.files)} />

      <UploadCard title="Bank SMS Alerts" subtitle="Optional — improves accuracy" icon="💬" uploaded={Boolean(files.sms?.length)} onPick={() => refs.sms.current?.click()}>
        <Badge variant="optional">Optional</Badge>
      </UploadCard>
      <input ref={refs.sms} type="file" accept=".txt,.csv" hidden onChange={(e) => onFiles("sms", e.target.files)} />
    </div>
  );
}

