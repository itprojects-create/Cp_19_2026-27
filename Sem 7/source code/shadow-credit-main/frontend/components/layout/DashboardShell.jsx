'use client';

import DashboardSidebar from './DashboardSidebar';
import DashboardTopBar from './DashboardTopBar';
import styles from './DashboardShell.module.css';

export default function DashboardShell({ children, pageTitle = '', pageSubtitle = '' }) {
  return (
    <div className={styles.shell}>
      <DashboardSidebar />
      <div className={styles.body}>
        <DashboardTopBar title={pageTitle} subtitle={pageSubtitle} />
        <main className={styles.main}>
          {children}
        </main>
      </div>
    </div>
  );
}
