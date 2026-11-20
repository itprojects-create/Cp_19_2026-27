import React, { useEffect, useState } from 'react';
import { cn } from '../../lib/cn';

interface StopWatchProps {
  running: boolean;
  resetTrigger?: number;
}

export const StopWatch: React.FC<StopWatchProps> = ({ running, resetTrigger = 0 }) => {
  const [seconds, setSeconds] = useState(0);
  const [flashSuccess, setFlashSuccess] = useState(false);

  useEffect(() => {
    setSeconds(0);
    setFlashSuccess(false);
  }, [resetTrigger]);

  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (running) {
      interval = setInterval(() => {
        setSeconds((s) => s + 1);
      }, 1000);
    } else if (seconds > 0 && seconds < 90) {
      // Stopped and within "success" range
      setFlashSuccess(true);
      const timer = setTimeout(() => setFlashSuccess(false), 2000);
      return () => clearTimeout(timer);
    }

    return () => clearInterval(interval);
  }, [running, seconds]);

  const formatTime = (totalSeconds: number) => {
    const m = Math.floor(totalSeconds / 60);
    const s = totalSeconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <span
      className={cn(
        'font-mono text-[13px] transition-colors duration-300',
        flashSuccess ? 'text-status-success' : 'text-text-tertiary'
      )}
    >
      {formatTime(seconds)}
    </span>
  );
};
