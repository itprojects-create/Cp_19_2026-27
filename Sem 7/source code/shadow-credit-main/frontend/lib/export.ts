import { api } from './api';

export const downloadBlob = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

export const exportAndDownload = async (
  sessionId: string,
  format: 'memo_pdf' | 'passport_pdf' | 'ocen_json',
  setLoading?: (loading: boolean) => void,
  toast?: (message: string, type: 'success' | 'error') => void
) => {
  if (setLoading) setLoading(true);

  try {
    const blob = await api.exportDocument(sessionId, format);
    
    let filename = 'document';
    if (format === 'memo_pdf') filename = 'shadow-credit-memo.pdf';
    else if (format === 'passport_pdf') filename = 'shadow-credit-passport.pdf';
    else if (format === 'ocen_json') filename = 'credit-assessment.json';

    downloadBlob(blob, filename);
    if (toast) toast('Downloaded successfully', 'success');
  } catch (error) {
    console.error('Export failed:', error);
    if (toast) toast('Export failed — please try again', 'error');
  } finally {
    if (setLoading) setLoading(false);
  }
};
