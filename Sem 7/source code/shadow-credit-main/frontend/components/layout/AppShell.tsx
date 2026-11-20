import React from 'react';
import { TopBar } from './TopBar';
import { Sidebar } from './Sidebar';

interface AppShellProps {
  children: React.ReactNode;
  title: string;
  isConnected: boolean;
}

export const AppShell: React.FC<AppShellProps> = ({ children, title, isConnected }) => {
  return (
    <div className="min-h-screen bg-bg-base">
      <TopBar title={title} isConnected={isConnected} />
      <Sidebar />
      <main className="ml-0 min-h-[calc(100vh-48px)] pt-12 md:ml-[220px]">
        {children}
      </main>
    </div>
  );
};
