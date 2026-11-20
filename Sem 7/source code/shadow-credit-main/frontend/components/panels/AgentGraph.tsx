import React, { useMemo } from 'react';
import { cn } from '../../lib/cn';

export interface AgentNode {
  id: string;
  status: 'idle' | 'running' | 'complete' | 'error';
  label: string;
}

interface AgentGraphProps {
  agents: AgentNode[];
  activeEdges: Array<{ from: string; to: string }>;
}

// Define fixed node positions
const NODE_CONFIG = {
  // Row 1
  MAPS: { x: '10%', y: 40, r: 16 },
  OCR: { x: '25%', y: 40, r: 16 },
  WA: { x: '40%', y: 40, r: 16 },
  SMS: { x: '55%', y: 40, r: 16 },
  KHATA: { x: '70%', y: 40, r: 16 },
  // Row 2
  SUPERVISOR: { x: '50%', y: 100, r: 20 },
  // Row 3 - visualized on graph but conceptually next stage
  WARMTH: { x: '20%', y: 140, r: 16 },
  RECON: { x: '50%', y: 140, r: 16 },
  COMPLIANCE: { x: '70%', y: 140, r: 16 },
  REPORT: { x: '85%', y: 140, r: 16 },
} as const;

// Define edges for visualization
const GRAPH_EDGES = [
  { from: 'MAPS', to: 'SUPERVISOR' },
  { from: 'OCR', to: 'SUPERVISOR' },
  { from: 'WA', to: 'SUPERVISOR' },
  { from: 'SMS', to: 'SUPERVISOR' },
  { from: 'KHATA', to: 'SUPERVISOR' },
  { from: 'SUPERVISOR', to: 'WARMTH' },
  { from: 'SUPERVISOR', to: 'RECON' },
  { from: 'SUPERVISOR', to: 'COMPLIANCE' },
  { from: 'RECON', to: 'REPORT' },
  { from: 'COMPLIANCE', to: 'REPORT' },
];

export const AgentGraph: React.FC<AgentGraphProps> = ({ agents, activeEdges }) => {
  const getStatus = (id: string) => agents.find((a) => a.id === id)?.status || 'idle';

  return (
    <div className="h-[140px] w-full bg-[#090D14] overflow-hidden">
      <svg width="100%" height="100%" className="block">
        <defs>
          <style>
            {`
              @keyframes dash {
                to {
                  stroke-dashoffset: -12;
                }
              }
              .edge-active {
                animation: dash 500ms linear infinite;
              }
              @keyframes pulse-ring {
                0% { transform: scale(0.8); opacity: 1; }
                100% { transform: scale(1.5); opacity: 0; }
              }
              .pulse-circle {
                transform-origin: center;
                animation: pulse-ring 1.2s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
              }
            `}
          </style>
        </defs>

        {/* Edges */}
        {GRAPH_EDGES.map((edge) => {
          const start = NODE_CONFIG[edge.from as keyof typeof NODE_CONFIG];
          const end = NODE_CONFIG[edge.to as keyof typeof NODE_CONFIG];
          
          // Check if this edge is active in props
          const isActive = activeEdges.some(
            (e) => e.from === edge.from && e.to === edge.to
          );

          return (
            <line
              key={`${edge.from}-${edge.to}`}
              x1={start.x}
              y1={start.y}
              x2={end.x}
              y2={end.y}
              stroke={isActive ? '#1F6FEB' : '#21262D'}
              strokeWidth={isActive ? 1.5 : 1}
              strokeDasharray={isActive ? '8 4' : '4 4'}
              className={isActive ? 'edge-active' : ''}
            />
          );
        })}

        {/* Nodes */}
        {Object.entries(NODE_CONFIG).map(([key, config]) => {
          const status = getStatus(key);
          const isSupervisor = key === 'SUPERVISOR';
          const isRunning = status === 'running';
          const isComplete = status === 'complete';
          const isError = status === 'error';
          
          const strokeColor = isSupervisor && isRunning 
            ? '#7C3AED' // Purple for Supervisor
            : isRunning 
              ? '#1F6FEB' // Blue for others
              : '#21262D'; // Subtle for idle

          const fillColor = isComplete 
            ? '#3FB950' 
            : isError 
              ? '#F85149' 
              : '#1C2128';

          return (
            <g key={key}>
              {/* Pulse Ring (only when running) */}
              {isRunning && (
                <circle
                  cx={config.x}
                  cy={config.y}
                  r={config.r}
                  fill="none"
                  stroke={isSupervisor ? '#7C3AED' : '#1F6FEB'}
                  strokeWidth="1.5"
                  className="pulse-circle"
                />
              )}

              {/* Main Node */}
              <circle
                cx={config.x}
                cy={config.y}
                r={config.r}
                fill={fillColor}
                stroke={isComplete || isError ? 'none' : strokeColor}
                strokeWidth={isRunning ? 1.5 : 1}
              />

              {/* Icons for Complete/Error */}
              {isComplete && (
                <path
                  d="M-5 -1 L-2 3 L5 -5"
                  stroke="white"
                  strokeWidth="2"
                  fill="none"
                  transform={`translate(${typeof config.x === 'number' ? config.x : 0}, ${config.y})`}
                  style={{ transformBox: 'fill-box', transformOrigin: 'center' }}
                  // Note: percentage x coordinates make direct transform tricky in pure SVG without JS calc
                  // Using nested SVG for icon centering to handle percentage coordinates
                />
              )}
              
              {/* Using foreignObject or text for icons to handle % coordinates easier, 
                  or just simple SVG paths assuming we can center them. 
                  Let's use a simpler approach: text checkmark/x for robust centering */}
               {(isComplete || isError) && (
                <text
                  x={config.x}
                  y={config.y}
                  dy="0.35em"
                  textAnchor="middle"
                  fill="white"
                  fontSize="14px"
                  fontWeight="bold"
                >
                  {isComplete ? '✓' : '✕'}
                </text>
              )}

              {/* Label */}
              <text
                x={config.x}
                y={config.y + config.r + 14}
                textAnchor="middle"
                fill={status === 'idle' ? '#6E7681' : isComplete ? '#3FB950' : isError ? '#F85149' : '#E6EDF3'}
                fontSize="10px"
                fontFamily="monospace"
              >
                {key}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};
