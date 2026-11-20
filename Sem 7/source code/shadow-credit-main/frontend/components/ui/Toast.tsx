import React from 'react';
import { createPortal } from 'react-dom';
import { Check, X } from 'lucide-react';
import { useToastStore } from '../../hooks/useToast';
import { cn } from '../../lib/cn';

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useToastStore();

  if (typeof document === 'undefined') return null;

  return createPortal(
    <div className="fixed bottom-4 right-4 z-[60] flex flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          onClick={() => removeToast(toast.id)}
          className={cn(
            "flex w-[320px] cursor-pointer items-start gap-3 rounded-lg border bg-bg-elevated px-4 py-3 shadow-modal transition-all duration-200 animate-in slide-in-from-right-full fade-in",
            toast.type === 'success' 
              ? "border-l-[3px] border-l-status-success border-y-border-subtle border-r-border-subtle" 
              : "border-l-[3px] border-l-status-error border-y-border-subtle border-r-border-subtle"
          )}
        >
          {toast.type === 'success' ? (
            <Check className="mt-0.5 h-4 w-4 text-status-success" />
          ) : (
            <X className="mt-0.5 h-4 w-4 text-status-error" />
          )}
          <p className="text-[13px] font-medium text-text-primary">{toast.message}</p>
        </div>
      ))}
    </div>,
    document.body
  );
};
