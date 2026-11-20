import React from 'react';
import { cn } from '../../lib/cn';
import { ConfidenceBadge } from './ConfidenceBadge';

interface DataRowProps {
  label: string;
  value: React.ReactNode;
  confidence?: number;
  onValueClick?: () => void;
  className?: string;
}

export const DataRow: React.FC<DataRowProps> = ({ label, value, confidence, onValueClick, className }) => {
  return (
    <div
      className={cn(
        'flex h-9 items-center justify-between border-b border-border-subtle last:border-0',
        className
      )}
    >
      <span className="text-[13px] text-text-secondary">{label}</span>
      
      <div className="flex items-center gap-2">
        <span
          onClick={onValueClick}
          className={cn(
            'text-[13px] font-variant-numeric tabular-nums text-text-primary',
            onValueClick && 'cursor-pointer hover:text-accent transition-colors'
          )}
        >
          {value}
        </span>
        {confidence !== undefined && (
          <ConfidenceBadge score={confidence} onClick={onValueClick} />
        )}
      </div>
    </div>
  );
};
