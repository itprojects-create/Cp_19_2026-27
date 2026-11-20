'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  FileText,
  Settings,
  HelpCircle,
} from 'lucide-react';
import styles from './DashboardSidebar.module.css';

const NAV_ITEMS = [
  {
    label: 'Cases',
    href: '/dashboard',
    icon: LayoutDashboard,
    exact: true,
  },
  {
    label: 'Reports',
    href: '/dashboard/reports',
    icon: FileText,
    exact: false,
  },
];

const BOTTOM_ITEMS = [
  { label: 'Settings', href: '/dashboard/settings', icon: Settings },
  { label: 'Help',     href: '/dashboard/help',     icon: HelpCircle },
];

export default function DashboardSidebar() {
  const pathname = usePathname();

  function isActive(href, exact) {
    if (exact) return pathname === href;
    return pathname.startsWith(href);
  }

  return (
    <aside className={styles.sidebar}>

      {/* Logo mark */}
      <div className={styles.logoArea}>
        <Link href="/" className={styles.logo} title="Shadow Credit Home">
          <span className={styles.logoMark}>SC</span>
        </Link>
      </div>

      <div className={styles.divider} />

      {/* Primary navigation */}
      <nav className={styles.nav}>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href, item.exact);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`${styles.navItem} ${active ? styles.navItemActive : ''}`}
              title={item.label}
            >
              {active && <span className={styles.activePip} />}
              <Icon size={18} strokeWidth={active ? 2 : 1.5} />
              <span className={styles.navLabel}>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className={styles.spacer} />

      {/* Bottom navigation */}
      <div className={styles.divider} />
      <nav className={styles.navBottom}>
        {BOTTOM_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={styles.navItem}
              title={item.label}
            >
              <Icon size={18} strokeWidth={1.5} />
              <span className={styles.navLabel}>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Bank RM identity badge */}
      <div className={styles.userBadge}>
        <div className={styles.userAvatar}>RM</div>
        <div className={styles.userInfo}>
          <span className={styles.userRole}>Bank RM</span>
          <span className={styles.userPortal}>Analyst Portal</span>
        </div>
      </div>

    </aside>
  );
}
