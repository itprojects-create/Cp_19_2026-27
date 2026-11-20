import React from 'react';
import { X, ShieldCheck } from 'lucide-react';
import { Button } from '../ui/Button';

export type ProvenanceData = {
  extractedValue?: string;
  extractedBy?: string;
  auditTrail?: Array<{
    step: string;
    agentId?: string;
    timestamp?: string;
    note?: string;
  }>;
};

type Props = {
  isOpen: boolean;
  onClose: () => void;
  fieldName: string;
  fieldValue: unknown;
  agentId: string;
  provenanceData?: ProvenanceData;
};

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'string') return value;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  try {
    return JSON.stringify(value);
  } catch {
    return '—';
  }
}

export const ProvenanceDrawer: React.FC<Props> = ({
  isOpen,
  onClose,
  fieldName,
  fieldValue,
  agentId,
  provenanceData,
}) => {
  const trail = provenanceData?.auditTrail ?? [];
  const extractedBy = provenanceData?.extractedBy || agentId || 'SYSTEM';
  const extractedValue = provenanceData?.extractedValue || formatValue(fieldValue);

  return (
    <aside
      className={`fixed right-0 top-0 z-40 h-full w-[360px] border-l border-border-subtle bg-bg-surface shadow-2xl transition-transform duration-300 ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      }`}
      aria-hidden={!isOpen}
    >
      <div className="flex h-full flex-col">
        <div className="flex items-center justify-between border-b border-border-subtle px-4 py-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide text-text-tertiary">Provenance</div>
            <div className="text-sm font-medium text-text-primary">Field lineage</div>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close provenance drawer">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
          <section className="rounded-md border border-border-subtle p-3">
            <div className="text-xs text-text-tertiary">Field name</div>
            <div className="mt-1 text-sm font-medium text-text-primary">{fieldName || '—'}</div>
          </section>

          <section className="rounded-md border border-border-subtle p-3">
            <div className="text-xs text-text-tertiary">Extracted value</div>
            <div className="mt-1 break-words text-sm text-text-primary">{extractedValue}</div>
          </section>

          <section className="rounded-md border border-border-subtle p-3">
            <div className="text-xs text-text-tertiary">Extracted by</div>
            <div className="mt-1 text-sm text-text-primary">{extractedBy}</div>
          </section>

          <section className="rounded-md border border-border-subtle p-3">
            <div className="mb-2 text-xs text-text-tertiary">Audit trail</div>
            {trail.length === 0 ? (
              <div className="text-sm text-text-secondary">No detailed trail available for this field yet.</div>
            ) : (
              <ol className="space-y-2">
                {trail.map((item, idx) => (
                  <li key={`${item.step}-${idx}`} className="rounded border border-border-subtle/60 p-2">
                    <div className="text-sm text-text-primary">{item.step}</div>
                    <div className="mt-1 text-xs text-text-tertiary">
                      {(item.agentId || 'SYSTEM')}{item.timestamp ? ` · ${item.timestamp}` : ''}
                    </div>
                    {item.note ? <div className="mt-1 text-xs text-text-secondary">{item.note}</div> : null}
                  </li>
                ))}
              </ol>
            )}
          </section>
        </div>

        <div className="border-t border-border-subtle px-4 py-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
            <ShieldCheck className="h-3.5 w-3.5" />
            DPDP Act 2023 Compliant
          </div>
        </div>
      </div>
    </aside>
  );
};
