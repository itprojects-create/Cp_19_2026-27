import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutList, BarChart3, Settings } from 'lucide-react';
import { cn } from '../../lib/cn';

const NAV_ITEMS = [
  { label: 'Cases', href: '/dashboard', icon: LayoutList },
  { label: 'Analytics', href: '/analytics', icon: BarChart3, dimmed: true },
  { label: 'Settings', href: '/settings', icon: Settings, dimmed: true },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside className="fixed bottom-0 left-0 top-12 z-40 hidden w-[220px] flex-col border-r border-border-subtle bg-bg-surface md:flex">
      <nav className="flex-1 py-4">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || (item.href === '/dashboard' && pathname === '/');
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex h-10 items-center gap-3 px-4 text-[14px] transition-colors',
                isActive
                  ? 'border-l-2 border-accent bg-bg-overlay text-text-primary'
                  : 'border-l-2 border-transparent text-text-secondary hover:bg-bg-elevated hover:text-text-primary',
                item.dimmed && !isActive && 'opacity-60'
              )}
            >
              <item.icon size={16} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      
      <div className="px-4 pb-4">
        <p className="text-[11px] text-text-tertiary">v1.0.0 · ICEM 2026</p>
      </div>
    </aside>
  );
};
