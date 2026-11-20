import React, { useEffect, useState } from 'react';
import { cn } from '../../lib/cn';
import { Tooltip } from './Tooltip';

interface SignalBarProps {
  label: string;
  value: number; // 0-1
  weight: number;
  shapContribution: number;
  tooltip?: string;
}

export const SignalBar: React.FC<SignalBarProps> = ({
  label,
  value,
  weight,
  shapContribution,
  tooltip,
}) => {
  const [width, setWidth] = useState(0);

  useEffect(() => {
    // Animate on mount
    const timer = setTimeout(() => setWidth(value * 100), 100);
    return () => clearTimeout(timer);
  }, [value]);

  const getBarColor = (val: number) => {
    if (val < 0.5) return 'bg-status-error';
    if (val < 0.75) return 'bg-status-warning';
    return 'bg-status-success';
  };

  const content = (
    <div className="flex h-9 w-full items-center gap-4">
      <span className="w-[160px] truncate text-[13px] text-text-secondary" title={label}>
        {label}
      </span>
      
      <div className="flex flex-1 items-center">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-bg-overlay">
          <div
            className={cn('h-full transition-all duration-600 ease-out', getBarColor(value))}
            style={{ width: `${width}%` }}
          />
        </div>
      </div>

      <span className="w-[60px] text-right font-mono text-[11px] text-text-secondary">
        {(value * 100).toFixed(0)}%
      </span>

      <span
        className={cn(
          'w-[60px] text-right font-mono text-[11px]',
          shapContribution > 0 ? 'text-status-success' : 'text-status-error'
        )}
      >
        {shapContribution > 0 ? '+' : ''}
        {shapContribution.toFixed(2)}
      </span>
    </div>
  );

  if (tooltip) {
    return (
      <Tooltip content={tooltip} side="left">
        <div className="w-full cursor-help">{content}</div>
      </Tooltip>
    );
  }

  return <div className="w-full">{content}</div>;
};
