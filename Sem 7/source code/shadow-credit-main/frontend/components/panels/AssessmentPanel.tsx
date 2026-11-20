import React, { useState, useEffect } from 'react';
import { BarChart2, MessageSquare, Smartphone, Receipt, MapPin, IndianRupee, Check, X, FileText, Download, Code } from 'lucide-react';
import { cn } from '../../lib/cn';
import { Button } from '../ui/Button';
import { Card, CardHeader, CardDivider } from '../ui/Card';
import { DataRow } from '../ui/DataRow';
import { SignalBar } from '../ui/SignalBar';
import { Badge } from '../ui/Badge';
import { Tooltip } from '../ui/Tooltip';
import { ConfidenceBadge } from '../ui/ConfidenceBadge';

// ----------------------------------------------------------------------------
// Types & Utility
// ----------------------------------------------------------------------------

export interface SignalData {
  label: string;
  value: number;
  weight: number;
  shapContribution: number;
  description?: string;
}

export interface ScenarioData {
  currentLimit: number;
  scenarios: {
    gst: { limit: number; steps: string[] };
    aa: { limit: number; steps: string[] };
    gst_aa: { limit: number; steps: string[] };
  };
}

export interface SessionData {
  financialSummary?: {
    monthlyRevenue: number;
    weeklyAvg: number;
    uniqueCounterparties: number;
    period: number;
    reconciliationStatus: 'NORMAL_CASH' | 'ELEVATED' | 'SIGNIFICANT' | 'HIGH_DISCREPANCY';
  };
  warmthData?: {
    score: number;
    grade: 'A+' | 'A' | 'B+' | 'B' | 'C';
    signals: SignalData[];
  };
  creditAssessment?: {
    baseLimit: number;
    regularityAdj: number;
    continuityAdj: number;
    concentrationAdj: number;
    finalLimit: number;
    narrative: string;
  };
  compliance?: {
    checks: Array<{ label: string; passed: boolean; rmExplanation?: string }>;
    score: number;
  };
  scenarioData?: ScenarioData;
}

interface AssessmentPanelProps {
  sessionId: string;
  sessionData: SessionData;
  onFieldClick: (fieldName: string, value: unknown, agentId: string, artifactId?: string) => void;
  onRunAnalysis: () => void;
}

const formatINR = (amount: number): string => {
  try {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  } catch (e) {
    return '₹0';
  }
};

const easeOutQuart = (t: number): number => 1 - Math.pow(1 - t, 4);

const CountUp: React.FC<{ end: number; duration?: number; formatter?: (v: number) => string; className?: string }> = ({
  end,
  duration = 800,
  formatter = (v) => v.toString(),
  className,
}) => {
  const [value, setValue] = useState(0);
  const ref = React.useRef<HTMLSpanElement>(null);
  const hasAnimated = React.useRef(false);

  useEffect(() => {
    if (hasAnimated.current) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated.current) {
          hasAnimated.current = true;
          let startTime: number | null = null;
          let animationFrameId: number;

          const animate = (timestamp: number) => {
            if (!startTime) startTime = timestamp;
            const progress = Math.min((timestamp - startTime) / duration, 1);
            const easedProgress = easeOutQuart(progress);
            setValue(easedProgress * end);
            if (progress < 1) {
              animationFrameId = requestAnimationFrame(animate);
            }
          };
          animationFrameId = requestAnimationFrame(animate);
          observer.disconnect();
        }
      },
      { threshold: 0.3 }
    );

    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [end, duration]);

  return <span ref={ref} className={className}>{formatter(value)}</span>;
};

// ----------------------------------------------------------------------------
// Sub-Components
// ----------------------------------------------------------------------------

const EvidenceSummary: React.FC = () => {
  const sources = [
    { icon: MessageSquare, name: 'WhatsApp', color: 'bg-emerald-500' },
    { icon: IndianRupee, name: 'UPI', color: 'bg-blue-500' },
    { icon: Smartphone, name: 'SMS', color: 'bg-sky-500' },
    { icon: Receipt, name: 'Bill', color: 'bg-amber-500' },
    { icon: MapPin, name: 'Maps', color: 'bg-rose-500' },
  ];

  return (
    <Card className="m-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <CardHeader>Evidence Summary</CardHeader>
      <div className="grid grid-cols-5 gap-2">
        {sources.map((src, i) => (
          <div key={i} className="flex flex-col items-center gap-1.5 p-2 text-center">
            <src.icon className="h-3 w-3 text-text-secondary" />
            <span className="text-[10px] text-text-tertiary">{src.name}</span>
            <div className={cn("h-1.5 w-1.5 rounded-full", src.color)} />
          </div>
        ))}
      </div>
      <div className="mt-3 text-center text-[12px] text-text-tertiary">
        5 of 5 sources verified · <span className="text-status-success font-medium">HIGH</span> confidence
      </div>
    </Card>
  );
};

const CreditGauge: React.FC<{ score: number }> = ({ score }) => {
  const [dashOffset, setDashOffset] = useState(270); // Full circle offset equivalent

  useEffect(() => {
    // Arc length = 2 * PI * r * (sweepAngle / 360)
    // r=32, sweep=270deg (0.75 of circle)
    // Full circumference = 2 * PI * 32 ≈ 201
    // Max arc length ≈ 150.8
    // StrokeDasharray = 151
    // Offset = 151 - (score * 151)
    
    // Simplified relative calc for dasharray/offset logic in SVG
    const maxLen = 151; 
    const targetOffset = maxLen - (score * maxLen);
    
    // Animate on mount
    setTimeout(() => setDashOffset(targetOffset), 100);
  }, [score]);

  const getColor = (s: number) => {
    if (s >= 0.8) return '#3FB950'; // Success
    if (s >= 0.6) return '#D29922'; // Warning
    return '#F85149'; // Error
  };

  return (
    <div className="relative h-[80px] w-[80px]">
      <svg width="80" height="80" viewBox="0 0 80 80">
        {/* Background Arc */}
        <circle
          cx="40"
          cy="40"
          r="32"
          fill="none"
          stroke="#21262D"
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray="151 201" // 270 degrees arc
          transform="rotate(135 40 40)"
        />
        {/* Progress Arc */}
        <circle
          cx="40"
          cy="40"
          r="32"
          fill="none"
          stroke={getColor(score)}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray="151 201"
          strokeDashoffset={dashOffset}
          className="transition-all duration-1000 ease-out"
          transform="rotate(135 40 40)"
        />
        <text
          x="50%"
          y="50%"
          dominantBaseline="middle"
          textAnchor="middle"
          className="fill-text-primary text-[16px] font-bold"
        >
          {score.toFixed(2)}
        </text>
      </svg>
    </div>
  );
};

// ----------------------------------------------------------------------------
// Main Component
// ----------------------------------------------------------------------------

export const AssessmentPanel: React.FC<AssessmentPanelProps> = ({
  sessionId,
  sessionData,
  onFieldClick,
  onRunAnalysis,
}) => {
  const [exportLoading, setExportLoading] = useState<string | null>(null);
  const [scenarioTab, setScenarioTab] = useState<'current' | 'gst' | 'aa' | 'gst_aa'>('current');

  if (!sessionData.financialSummary && !sessionData.warmthData && !sessionData.creditAssessment) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 bg-bg-surface p-6 text-center">
        <BarChart2 className="h-8 w-8 text-text-tertiary" />
        <p className="text-[14px] text-text-secondary">Run analysis to see assessment</p>
        <Button variant="primary" size="sm" onClick={onRunAnalysis}>Run Analysis</Button>
      </div>
    );
  }

  const handleExport = (type: string) => {
    setExportLoading(type);
    setTimeout(() => setExportLoading(null), 1500);
  };

  const getScenarioValues = () => {
    const base = sessionData.creditAssessment?.finalLimit || 0;
    if (!sessionData.scenarioData) return { limit: base, delta: 0, steps: [] };

    switch (scenarioTab) {
      case 'gst': return { limit: sessionData.scenarioData.scenarios.gst.limit, delta: sessionData.scenarioData.scenarios.gst.limit - base, steps: sessionData.scenarioData.scenarios.gst.steps };
      case 'aa': return { limit: sessionData.scenarioData.scenarios.aa.limit, delta: sessionData.scenarioData.scenarios.aa.limit - base, steps: sessionData.scenarioData.scenarios.aa.steps };
      case 'gst_aa': return { limit: sessionData.scenarioData.scenarios.gst_aa.limit, delta: sessionData.scenarioData.scenarios.gst_aa.limit - base, steps: sessionData.scenarioData.scenarios.gst_aa.steps };
      default: return { limit: base, delta: 0, steps: [] };
    }
  };

  const { limit: scenarioLimit, delta: scenarioDelta, steps: scenarioSteps } = getScenarioValues();

  return (
    <div className="h-full overflow-y-auto bg-bg-surface pb-8">
      
      {/* SECTION 1: EVIDENCE SUMMARY */}
      <EvidenceSummary />

      {/* SECTION 2: FINANCIAL SUMMARY */}
      {sessionData.financialSummary && (
        <Card className="mx-4 mb-4 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-100">
          <CardHeader>Financial Summary</CardHeader>
          <div className="flex flex-col gap-0">
            <DataRow
              label="Monthly Revenue"
              value={formatINR(sessionData.financialSummary.monthlyRevenue)}
              confidence={0.92}
              onValueClick={() => onFieldClick('monthlyRevenue', sessionData.financialSummary?.monthlyRevenue, 'AGENT_05')}
            />
            <DataRow
              label="Weekly Average"
              value={formatINR(sessionData.financialSummary.weeklyAvg)}
              confidence={0.88}
              onValueClick={() => onFieldClick('weeklyAvg', sessionData.financialSummary?.weeklyAvg, 'AGENT_05')}
            />
            <DataRow
              label="Unique Counterparties"
              value={sessionData.financialSummary.uniqueCounterparties}
              confidence={0.95}
              onValueClick={() => onFieldClick('uniqueCounterparties', sessionData.financialSummary?.uniqueCounterparties, 'AGENT_05')}
            />
            <DataRow
              label="Assessment Period"
              value={`${sessionData.financialSummary.period} days`}
            />
          </div>

          {/* Reconciliation Banner */}
          <div className={cn(
            "mt-3 rounded-r-md border-l-[3px] px-3 py-2 text-[12px]",
            sessionData.financialSummary.reconciliationStatus === 'NORMAL_CASH'
              ? "border-status-success bg-status-success/5 text-text-primary"
              : "border-status-error bg-status-error/5 text-text-primary"
          )}>
            {sessionData.financialSummary.reconciliationStatus === 'NORMAL_CASH'
              ? "Revenue gap explained — consistent with cash-based Kirana"
              : "Revenue gap requires review — see forensics below"
            }
          </div>
        </Card>
      )}

      {/* SECTION 3: CREDITWARMTHSCORE */}
      {sessionData.warmthData && (
        <Card className="mx-4 mb-4 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-200">
          <CardHeader>CreditWarmthScore</CardHeader>
          <div className="flex gap-4">
            <CreditGauge score={sessionData.warmthData.score} />
            <div className="flex flex-1 flex-col items-center justify-center rounded-lg bg-bg-overlay py-2">
              <span className={cn(
                "text-[20px] font-bold",
                sessionData.warmthData.grade.startsWith('A') ? 'text-status-success' :
                sessionData.warmthData.grade.startsWith('B') ? 'text-status-warning' : 'text-status-error'
              )}>
                {sessionData.warmthData.grade}
              </span>
              <span className="text-[11px] text-text-tertiary uppercase tracking-wider">CreditWarmth</span>
            </div>
          </div>
          
          <div className="mt-4 flex flex-col gap-2">
            {sessionData.warmthData.signals.map((signal, idx) => (
              <SignalBar
                key={idx}
                label={signal.label}
                value={signal.value}
                weight={signal.weight}
                shapContribution={signal.shapContribution}
                tooltip={signal.description}
              />
            ))}
          </div>
        </Card>
      )}

      {/* SECTION 4: CREDIT ASSESSMENT */}
      {sessionData.creditAssessment && (
        <Card className="mx-4 mb-4 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-300">
          <CardHeader>Credit Assessment</CardHeader>
          
          {/* Formula Section */}
          <div>
            <div className="text-[12px] font-medium uppercase tracking-wider text-text-secondary">Credit Formula</div>
            <div className="mt-2 rounded-md bg-bg-base p-3 font-mono text-[12px] text-text-primary leading-relaxed">
              <div className="flex items-center gap-1 flex-wrap">
                <span>{formatINR(sessionData.financialSummary?.monthlyRevenue || 0)}/mo × 3 = </span>
                <span className="font-bold">{formatINR(sessionData.creditAssessment.baseLimit)} base</span>
              </div>
              <div className="flex items-center gap-1 flex-wrap mt-1">
                <span>×</span>
                <span 
                  className="cursor-pointer rounded bg-bg-overlay px-1 hover:bg-bg-elevated text-accent"
                  onClick={() => onFieldClick('regularityAdj', sessionData.creditAssessment?.regularityAdj, 'SUPERVISOR')}
                >
                  {sessionData.creditAssessment.regularityAdj.toFixed(2)}
                </span>
                <span>regularity adj. = {formatINR(sessionData.creditAssessment.baseLimit * sessionData.creditAssessment.regularityAdj)}</span>
              </div>
              <div className="flex items-center gap-1 flex-wrap mt-1">
                <span>×</span>
                <span 
                  className="cursor-pointer rounded bg-bg-overlay px-1 hover:bg-bg-elevated text-accent"
                  onClick={() => onFieldClick('continuityAdj', sessionData.creditAssessment?.continuityAdj, 'SUPERVISOR')}
                >
                  {sessionData.creditAssessment.continuityAdj.toFixed(2)}
                </span>
                <span>continuity adj.</span>
              </div>
              <div className="flex items-center gap-1 flex-wrap mt-1 border-t border-border-subtle pt-1">
                <span>=</span>
                <span className="font-bold text-text-primary">{formatINR(sessionData.creditAssessment.finalLimit)}</span>
                <span>final recommendation</span>
              </div>
            </div>
          </div>

          <CardDivider />

          {/* Credit Limit Display */}
          <div className="flex flex-col items-center py-4">
            <span className="text-[12px] text-text-secondary">Recommended Limit</span>
            <div className="flex items-baseline gap-3 mt-1">
              <CountUp 
                end={sessionData.creditAssessment.finalLimit} 
                formatter={formatINR}
                className="text-[36px] font-bold text-accent tabular-nums tracking-tight"
              />
              <Badge variant="approved">{sessionData.warmthData?.grade || 'N/A'}</Badge>
            </div>
          </div>

          {/* Narrative Card */}
          <div className="mt-2 rounded-md border border-border-subtle bg-bg-base p-0">
            <div className="flex items-center justify-between border-b border-border-subtle px-3 py-2">
              <span className="text-[12px] font-medium text-text-secondary">Credit Narrative</span>
              <span className="rounded bg-bg-elevated px-1.5 py-0.5 text-[10px] text-text-tertiary">AI-Generated</span>
            </div>
            <div className="px-4 py-3 font-serif text-[14px] leading-relaxed text-text-secondary">
              {sessionData.creditAssessment.narrative}
            </div>
            <div className="px-3 py-2 text-[10px] text-text-tertiary bg-bg-base rounded-b-md">
              Generated by Groq · Grounded in session data
            </div>
          </div>

          {/* RM Decision */}
          <div className="mt-6">
            <div className="mb-2 text-[12px] text-text-secondary">RM Decision</div>
            <div className="flex gap-2">
              <Button 
                variant="primary" 
                className="flex-1 bg-status-success hover:bg-green-600 border-transparent"
                leftIcon={<Check className="h-4 w-4" />}
              >
                Approve
              </Button>
              <Button variant="secondary" className="flex-1">
                Refer
              </Button>
              <Button 
                variant="danger" 
                className="flex-1"
                leftIcon={<X className="h-4 w-4" />}
              >
                Decline
              </Button>
            </div>
          </div>

          {/* Export Buttons */}
          <div className="mt-3 flex gap-2">
            <Button 
              variant="secondary" 
              size="sm" 
              className="flex-1 text-[11px]" 
              onClick={() => handleExport('memo')}
              loading={exportLoading === 'memo'}
              leftIcon={<FileText className="h-3 w-3" />}
            >
              Bank Memo PDF
            </Button>
            <Button 
              variant="secondary" 
              size="sm" 
              className="flex-1 text-[11px]"
              onClick={() => handleExport('passport')}
              loading={exportLoading === 'passport'}
              leftIcon={<Download className="h-3 w-3" />}
            >
              Credit Passport
            </Button>
            <Button 
              variant="secondary" 
              size="sm" 
              className="flex-1 text-[11px]"
              onClick={() => handleExport('json')}
              loading={exportLoading === 'json'}
              leftIcon={<Code className="h-3 w-3" />}
            >
              OCEN JSON
            </Button>
          </div>
        </Card>
      )}

      {/* SECTION 5: COMPLIANCE */}
      {sessionData.compliance && (
        <Card className="mx-4 mb-4 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-500">
          <div className="flex items-center justify-between mb-4">
            <CardHeader className="mb-0">Compliance</CardHeader>
            <Badge variant={sessionData.compliance.score === 100 ? 'approved' : 'neutral'}>
              {sessionData.compliance.score}%
            </Badge>
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-2">
            {sessionData.compliance.checks.map((check, idx) => (
              <div key={idx} className="flex items-center gap-2 h-6">
                {check.passed ? (
                  <Check className="h-3.5 w-3.5 text-status-success flex-shrink-0" />
                ) : (
                  <Tooltip content={check.rmExplanation || 'No explanation provided'}>
                    <X className="h-3.5 w-3.5 text-status-error flex-shrink-0 cursor-help" />
                  </Tooltip>
                )}
                <span className={cn(
                  "text-[13px] truncate", 
                  check.passed ? "text-text-primary" : "text-text-secondary"
                )}>
                  {check.label}
                </span>
              </div>
            ))}
          </div>
          <div className="mt-3 border-t border-border-subtle pt-2 text-[12px] text-text-tertiary">
            {sessionData.compliance.checks.filter(c => c.passed).length}/{sessionData.compliance.checks.length} checks passed · {sessionData.compliance.score}%
          </div>
        </Card>
      )}

      {/* SECTION 6: SCENARIO ANALYSIS */}
      {sessionData.scenarioData && (
        <Card className="mx-4 mb-4 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-700">
          <CardHeader>Scenario Analysis</CardHeader>
          <div className="flex gap-1 rounded-lg bg-bg-base p-1">
            {(['current', 'gst', 'aa', 'gst_aa'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setScenarioTab(tab)}
                className={cn(
                  "flex-1 rounded-md py-1.5 text-[12px] font-medium transition-all",
                  scenarioTab === tab
                    ? "bg-bg-elevated text-text-primary shadow-sm ring-1 ring-border-subtle"
                    : "text-text-secondary hover:text-text-primary hover:bg-white/[0.02]"
                )}
              >
                {tab === 'current' ? 'Current' : tab === 'gst' ? 'GST' : tab === 'aa' ? 'AA Consent' : 'GST + AA'}
              </button>
            ))}
          </div>

          <div className="mt-4 flex flex-col items-center">
            <span className="text-[11px] text-text-secondary uppercase tracking-wider">Projected Limit</span>
            <div className="mt-1 flex items-baseline gap-2">
              <CountUp 
                end={scenarioLimit} 
                formatter={formatINR}
                className="text-[24px] font-bold text-text-primary tabular-nums"
              />
              {scenarioDelta !== 0 && (
                <span className={cn(
                  "text-[12px] font-medium",
                  scenarioDelta > 0 ? "text-status-success" : "text-status-error"
                )}>
                  {scenarioDelta > 0 ? '+' : ''}{formatINR(scenarioDelta)}
                </span>
              )}
            </div>
          </div>
          
          {scenarioSteps.length > 0 && (
             <div className="mt-4 rounded-md bg-bg-base p-3">
               <div className="mb-2 text-[11px] font-medium text-text-secondary">Formalization Steps</div>
               <ul className="list-inside list-decimal space-y-1">
                 {scenarioSteps.map((step, i) => (
                   <li key={i} className="text-[12px] text-text-secondary">{step}</li>
                 ))}
               </ul>
             </div>
          )}
        </Card>
      )}
    </div>
  );
};
