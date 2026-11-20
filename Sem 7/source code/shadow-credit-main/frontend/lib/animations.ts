/**
 * Easing function for smooth animations
 */
export function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

/**
 * Animates a number from start to end over duration
 * Uses requestAnimationFrame for smooth 60fps animation
 */
export function animateNumber(
  start: number,
  end: number,
  duration: number,
  onUpdate: (value: number) => void,
  onComplete?: () => void
): () => void {
  const startTime = performance.now();
  let rafId: number;

  function update(currentTime: number) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const easedProgress = easeOutCubic(progress);
    const currentValue = start + (end - start) * easedProgress;

    onUpdate(Math.round(currentValue));

    if (progress < 1) {
      rafId = requestAnimationFrame(update);
    } else {
      onComplete?.();
    }
  }

  rafId = requestAnimationFrame(update);

  // Return cancel function
  return () => cancelAnimationFrame(rafId);
}
