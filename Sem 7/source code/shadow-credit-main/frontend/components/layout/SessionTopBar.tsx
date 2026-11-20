import React from 'react';
import { ChevronLeft } from 'lucide-react';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { StopWatch } from '../ui/StopWatch';

interface SessionTopBarProps {
  caseId: string;
  applicantName: string;
  businessName: string;
  location: string;
  status: 'new' | 'processing' | 'clarification' | 'complete' | 'approved' | 'rejected' | 'neutral';
  analysisRunning: boolean;
  onRunAnalysis: () => void;
  onBack?: () => void;
}

export const SessionTopBar: React.FC<SessionTopBarProps> = ({
  caseId,
  applicantName,
  businessName,
  location,
  status,
  analysisRunning,
  onRunAnalysis,
  onBack,
}) => {
  return (
    <div className="sticky top-0 z-40 flex h-11 items-center justify-between border-b border-border-subtle bg-bg-surface px-4">
      {/* Left Section */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={onBack} className="h-8 w-8 p-0">
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <span className="font-mono text-[12px] text-text-tertiary">#{caseId}</span>
      </div>

      {/* Center Section */}
      <div className="flex items-center gap-2 text-[14px] text-text-secondary">
        <span className="font-medium text-text-primary">{applicantName}</span>
        <span className="text-text-tertiary">/</span>
        <span>{businessName}</span>
        <span className="text-text-tertiary">/</span>
        <span>{location}</span>
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-3">
        <Badge variant={status}>{status}</Badge>
        <div className="w-px h-4 bg-border-subtle mx-1" />
        <StopWatch running={analysisRunning} />
        <Button 
          variant="primary" 
          size="sm" 
          onClick={onRunAnalysis}
          loading={analysisRunning}
          disabled={analysisRunning}
        >
          Run Analysis
        </Button>
      </div>
    </div>
  );
};
