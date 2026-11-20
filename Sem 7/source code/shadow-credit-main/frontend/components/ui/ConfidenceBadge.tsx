import React from 'react';
import { cn } from '../../lib/cn';

interface ConfidenceBadgeProps {
  score: number;
  onClick?: (e: React.MouseEvent) => void;
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({ score, onClick }) => {
  const getStatus = (s: number) => {
    if (s >= 0.85) return { color: 'text-status-success', bg: 'bg-status-success' };
    if (s >= 0.50) return { color: 'text-status-warning', bg: 'bg-status-warning' };
    return { color: 'text-status-error', bg: 'bg-status-error' };
  };

  const status = getStatus(score);

  return (
    <div
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 transition-all',
        onClick && 'cursor-pointer hover:brightness-110'
      )}
    >
      <span className={cn('h-2 w-2 rounded-full', status.bg)} />
      <span className={cn('font-mono text-[11px] font-medium', status.color)}>
        {score.toFixed(2)}
      </span>
    </div>
  );
};
