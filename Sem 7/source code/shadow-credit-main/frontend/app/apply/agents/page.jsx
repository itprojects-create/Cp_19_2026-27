'use client';

import { Suspense } from 'react';
import AgentsContent from './AgentsContent';

export default function AgentsPage() {
  return (
    <Suspense fallback={<div style={{ background: '#0D1117', height: '100vh' }} />}>
      <AgentsContent />
    </Suspense>
  );
}
