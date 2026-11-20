/**
 * Formats amount in Indian numbering system
 * 105000 → ₹1,05,000
 */
export function formatIndianCurrency(amount: number): string {
  const formatted = amount.toLocaleString('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  });
  return formatted;
}

/**
 * Formats date in readable format
 * 2026-03-27 → 27 March 2026
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

/**
 * Formats file size
 * 1024 → 1 KB
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
