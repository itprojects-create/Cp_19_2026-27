import React from 'react';
import * as Switch from '@radix-ui/react-switch';
import { Check, X, Upload, MapPin, Star, AlertCircle, FileText } from 'lucide-react';
import { cn } from '../../lib/cn';
import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';
import { Spinner } from '../ui/Spinner';

interface Artifact {
  id: string;
  type: 'WHATSAPP' | 'UPI' | 'BILL' | 'KHATA' | 'SMS' | 'MAPS';
  filename: string;
  confidence: number;
  status: 'processing' | 'complete' | 'error';
  thumbnailUrl?: string;
}

interface EvidencePanelProps {
  artifacts: Artifact[];
  mapsData?: {
    shopName: string;
    address: string;
    rating: number;
    reviewCount: number;
    staticMapUrl?: string;
  };
  privacyBlur: boolean;
  onPrivacyBlurChange: (checked: boolean) => void;
  sessionId: string;
}

const TYPE_STYLES = {
  WHATSAPP: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  UPI: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  BILL: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  KHATA: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  SMS: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
  MAPS: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
};

const getConfidenceColor = (score: number) => {
  if (score >= 0.85) return 'bg-status-success';
  if (score >= 0.50) return 'bg-status-warning';
  return 'bg-status-error';
};

export const EvidencePanel: React.FC<EvidencePanelProps> = ({
  artifacts,
  mapsData,
  privacyBlur,
  onPrivacyBlurChange,
}) => {
  return (
    <div className="flex h-full flex-col bg-bg-surface">
      {/* Header */}
      <div className="sticky top-0 z-10 flex items-center justify-between border-b border-border-subtle bg-bg-surface px-4 py-3">
        <h2 className="text-[14px] font-semibold text-text-secondary">Evidence</h2>
        <Badge variant="neutral">{artifacts.length} sources</Badge>
      </div>

      {/* Artifact List */}
      <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-3 py-3">
        {artifacts.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-text-tertiary">
            <Upload className="h-8 w-8 opacity-50" />
            <p className="text-[13px]">No artifacts uploaded</p>
          </div>
        ) : (
          artifacts.map((artifact) => (
            <div
              key={artifact.id}
              className="rounded-lg border border-border-subtle bg-bg-elevated p-3"
            >
              {/* Top Row */}
              <div className="flex items-center justify-between">
                <span
                  className={cn(
                    'inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider',
                    TYPE_STYLES[artifact.type]
                  )}
                >
                  {artifact.type}
                </span>
                {artifact.status === 'processing' && <Spinner size={14} className="text-accent" />}
                {artifact.status === 'complete' && <Check className="h-4 w-4 text-status-success" />}
                {artifact.status === 'error' && <X className="h-4 w-4 text-status-error" />}
              </div>

              {/* Thumbnail / Content */}
              <div className={cn('relative mt-3 h-20 w-full overflow-hidden rounded-md bg-bg-overlay transition-all duration-300', privacyBlur && 'blur-[4px] pointer-events-none select-none')}>
                {artifact.thumbnailUrl ? (
                  <img
                    src={artifact.thumbnailUrl}
                    alt={artifact.filename}
                    className="h-full w-full object-cover"
                    loading="lazy"
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center">
                    <FileText className="h-6 w-6 text-text-tertiary opacity-50" />
                  </div>
                )}
              </div>

              {/* Filename */}
              <div className={cn("mt-2 truncate text-[12px] text-text-tertiary", privacyBlur && 'blur-[4px]')}>
                {artifact.filename}
              </div>

              {/* Confidence Bar */}
              <div className="mt-2 flex items-center gap-2">
                <div className="h-1 flex-1 overflow-hidden rounded-full bg-bg-overlay">
                  <div
                    className={cn(
                      'h-full transition-all duration-400 ease-out',
                      getConfidenceColor(artifact.confidence)
                    )}
                    style={{ width: `${artifact.confidence * 100}%` }}
                  />
                </div>
                <div className="font-mono text-[11px] text-text-tertiary">
                  {(artifact.confidence * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          ))
        )}

        {/* Maps Card */}
        {mapsData && (
          <Card className="mt-2 overflow-hidden bg-bg-elevated p-0">
            <div className="p-3">
              {/* Map Image */}
              <div className="relative h-24 w-full overflow-hidden rounded-md bg-bg-overlay">
                {mapsData.staticMapUrl ? (
                  <img
                    src={mapsData.staticMapUrl}
                    alt="Location Map"
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center opacity-10" 
                       style={{ backgroundImage: 'radial-gradient(circle, #484F58 1px, transparent 1px)', backgroundSize: '8px 8px' }}>
                    <MapPin className="h-6 w-6 text-text-secondary" />
                  </div>
                )}
              </div>

              {/* Shop Details */}
              <div className="mt-2">
                <h3 className="text-[14px] font-medium text-text-primary">{mapsData.shopName}</h3>
                <p className={cn("mt-0.5 text-[12px] text-text-secondary transition-all duration-300", privacyBlur && "blur-[4px]")}>
                  {mapsData.address}
                </p>
              </div>

              {/* Rating Row */}
              <div className="mt-2 flex items-center justify-between border-t border-border-subtle pt-2">
                <div className="flex items-center gap-1.5">
                  <Star className="h-3.5 w-3.5 fill-status-warning text-status-warning" />
                  <span className="text-[12px] font-medium text-text-primary">{mapsData.rating}</span>
                  <span className="text-[12px] text-text-tertiary">({mapsData.reviewCount})</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="relative flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-status-success opacity-75"></span>
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-status-success"></span>
                  </span>
                  <span className="text-[11px] font-medium text-status-success">Open now</span>
                </div>
              </div>
            </div>
          </Card>
        )}
      </div>

      {/* Privacy Toggle */}
      <div className="sticky bottom-0 z-10 flex items-center justify-between border-t border-border-subtle bg-bg-surface px-4 py-3">
        <label className="text-[14px] font-medium text-text-secondary" htmlFor="privacy-mode">
          Blur PII
        </label>
        <Switch.Root
          id="privacy-mode"
          checked={privacyBlur}
          onCheckedChange={onPrivacyBlurChange}
          className={cn(
            "relative h-6 w-11 cursor-pointer rounded-full outline-none transition-colors duration-200 focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-bg-base",
            privacyBlur ? "bg-accent" : "bg-bg-overlay"
          )}
        >
          <Switch.Thumb
            className={cn(
              "block h-5 w-5 translate-x-0.5 rounded-full bg-white shadow-sm transition-transform duration-200 will-change-transform",
              privacyBlur ? "translate-x-[22px]" : ""
            )}
          />
        </Switch.Root>
      </div>
    </div>
  );
};
