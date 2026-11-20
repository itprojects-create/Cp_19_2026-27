import React from 'react';
import { cn } from '../../lib/cn';
import { Button } from '../ui/Button';

interface TopBarProps {
  title: string;
  isConnected: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({ title, isConnected }) => {
  return (
    <header className="fixed left-0 right-0 top-0 z-50 flex h-12 items-center justify-between border-b border-border-subtle bg-bg-surface px-4">
      {/* Left section */}
      <div className="flex items-center gap-3">
        <span className="text-[18px] font-bold text-accent">SC</span>
        <span className="text-[14px] font-medium text-text-secondary">Shadow Credit</span>
      </div>

      {/* Center section */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
        <h1 className="text-[14px] font-medium text-text-primary">{title}</h1>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-3">
        <div
          className={cn(
            'h-2 w-2 rounded-full',
            isConnected ? 'bg-status-success' : 'bg-text-tertiary'
          )}
          title={isConnected ? 'Connected' : 'Disconnected'}
        />
        <Button variant="primary" size="sm">
          New Assessment
        </Button>
      </div>
    </header>
  );
};
