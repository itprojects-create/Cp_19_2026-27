import React from 'react';
import { cn } from '../../lib/cn';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: string;
}

export const Card = ({ children, className, padding = 'p-4' }: CardProps) => {
  return (
    <div className={cn('rounded-lg border border-border-subtle bg-bg-elevated', padding, className)}>
      {children}
    </div>
  );
};

export const CardHeader = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={cn('mb-4 text-sm font-medium text-text-secondary', className)}>
    {children}
  </div>
);

export const CardDivider = ({ className }: { className?: string }) => (
  <div className={cn('my-4 h-px bg-border-subtle', className)} />
);
