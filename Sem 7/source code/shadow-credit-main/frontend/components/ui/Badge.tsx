import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { cn } from '../../lib/cn';

interface BadgeProps {
  variant: 'new' | 'processing' | 'clarification' | 'complete' | 'approved' | 'rejected' | 'neutral';
  children: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ variant, children, className }) => {
  const styles = {
    new: 'bg-accent/10 text-accent border border-accent/20',
    processing: 'bg-status-info/10 text-status-info border border-status-info/20',
    clarification: 'bg-status-warning/10 text-status-warning border border-status-warning/20',
    complete: 'bg-status-success/10 text-status-success border border-status-success/20',
    approved: 'bg-status-success/10 text-status-success border border-status-success/20',
    rejected: 'bg-status-error/10 text-status-error border border-status-error/20',
    neutral: 'bg-bg-overlay text-text-secondary border border-border-default',
  };

  return (
    <span
      className={cn(
        'inline-flex h-[20px] items-center rounded-full px-2 text-[11px] font-semibold uppercase tracking-wider',
        styles[variant],
        className
      )}
    >
      {variant === 'processing' && (
        <span className="mr-1.5 flex h-2 w-2 relative">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-current opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-current"></span>
        </span>
      )}
      {variant === 'clarification' && (
        <AlertTriangle className="mr-1 h-3 w-3 animate-pulse" />
      )}
      {children}
    </span>
  );
};
