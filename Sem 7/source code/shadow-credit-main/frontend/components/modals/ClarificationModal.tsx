import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Zap } from 'lucide-react';
import { cn } from '../../lib/cn';
import { Button } from '../ui/Button';

export interface ClarificationData {
  clarificationId: string;
  question: string;
  options: Array<{ label: string; value: string }>;
}

interface ClarificationModalProps {
  data: ClarificationData | null;
  onAnswer: (clarificationId: string, value: string) => Promise<void>;
}

export const ClarificationModal: React.FC<ClarificationModalProps> = ({ data, onAnswer }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (data) {
      setIsOpen(true);
      document.body.style.overflow = 'hidden';
    } else {
      const timer = setTimeout(() => setIsOpen(false), 200); // Allow fade out
      document.body.style.overflow = '';
      return () => clearTimeout(timer);
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [data]);

  const handleSelect = async (value: string) => {
    if (!data || isSubmitting) return;
    
    setSelectedOption(value);
    setIsSubmitting(true);

    // Visual feedback delay
    await new Promise(resolve => setTimeout(resolve, 150));
    
    try {
      await onAnswer(data.clarificationId, value);
    } finally {
      setIsSubmitting(false);
      setSelectedOption(null);
    }
  };

  if (!isOpen && !data) return null;

  // Use a portal to render at document body level
  return createPortal(
    <div 
      className={cn(
        "fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-[4px] transition-opacity duration-200",
        data ? "opacity-100" : "opacity-0 pointer-events-none"
      )}
    >
      <div 
        className={cn(
          "w-[480px] max-w-[calc(100vw-32px)] transform rounded-xl border border-border-default bg-bg-elevated p-8 shadow-modal transition-all duration-200",
          data ? "scale-100 opacity-100" : "scale-96 opacity-0"
        )}
      >
        {/* Header */}
        <div className="mb-5">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-accent fill-accent" />
            <span className="text-[11px] font-bold uppercase tracking-[0.08em] text-accent">
              Supervisor Agent
            </span>
          </div>
          <div className="mt-1 text-[13px] text-text-secondary">
            Pipeline paused — input required
          </div>
        </div>

        <div className="my-5 h-px bg-border-subtle" />

        {/* Question */}
        <h2 className="mb-6 text-[18px] font-medium leading-relaxed text-text-primary">
          {data?.question}
        </h2>

        {/* Options */}
        <div className="flex flex-col gap-3">
          {data?.options.map((option) => (
            <button
              key={option.value}
              onClick={() => handleSelect(option.value)}
              disabled={isSubmitting}
              className={cn(
                "flex h-11 w-full items-center justify-center rounded-md border text-[14px] font-medium transition-all duration-150 ease-out",
                selectedOption === option.value
                  ? "bg-accent border-accent text-white shadow-sm" // Selected state
                  : "bg-transparent border-border-default text-text-primary hover:bg-accent/10 hover:border-accent hover:text-text-primary active:scale-[0.98]" // Default/Hover state
              )}
            >
              {option.label}
            </button>
          ))}
        </div>

        {/* Footer */}
        <div className="mt-6 text-center text-[12px] text-text-tertiary">
          Your response will resume the AI pipeline
        </div>
      </div>
    </div>,
    document.body
  );
};
