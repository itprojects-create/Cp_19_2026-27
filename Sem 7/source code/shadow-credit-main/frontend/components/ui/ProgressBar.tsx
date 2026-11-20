import React from 'react';
import { cn } from '../../lib/cn';

interface ProgressBarProps {
  value: number; // 0-100
  color?: string;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ value, color = 'bg-accent', className }) => {
  return (
    <div className={cn('h-1 w-full overflow-hidden rounded-full bg-bg-overlay', className)}>
      <div
        className={cn('h-full transition-all duration-400 ease-out', color)}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
};
