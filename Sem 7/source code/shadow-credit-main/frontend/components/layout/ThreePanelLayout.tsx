import React from 'react';

interface ThreePanelLayoutProps {
  leftPanel: React.ReactNode;
  centerPanel: React.ReactNode;
  rightPanel: React.ReactNode;
}

export const ThreePanelLayout: React.FC<ThreePanelLayoutProps> = ({
  leftPanel,
  centerPanel,
  rightPanel,
}) => {
  return (
    <div className="flex h-[calc(100vh-48px)] w-full overflow-hidden">
      {/* Left Panel */}
      <div className="w-[300px] flex-shrink-0 overflow-y-auto border-r border-border-subtle bg-bg-base">
        {leftPanel}
      </div>

      {/* Center Panel */}
      <div className="flex-1 overflow-y-auto border-r border-border-subtle bg-[#090D14]">
        {centerPanel}
      </div>

      {/* Right Panel */}
      <div className="w-[340px] xl:w-[380px] flex-shrink-0 overflow-y-auto bg-bg-base">
        {rightPanel}
      </div>
    </div>
  );
};
