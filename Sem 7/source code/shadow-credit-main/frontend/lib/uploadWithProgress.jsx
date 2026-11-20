/**
 * Upload a single file with real progress tracking via XHR.
 * fetch() does not support upload progress — XHR is required.
 *
 * @param {string}   sessionId    - sc_session_id from localStorage
 * @param {File}     file         - the File object to upload
 * @param {string}   artifactType - WHATSAPP_EXPORT | UPI_SCREENSHOT etc.
 * @param {Function} onProgress   - called with 0-100 integer
 * @returns {Promise<object>}     - resolves with response data object
 */
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export function uploadWithProgress(sessionId, file, artifactType, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr  = new XMLHttpRequest();
    const form = new FormData();
    form.append('files', file);
    form.append('artifact_types', artifactType);

    xhr.open('POST', `${API_BASE}/ingest/${sessionId}`);

    // Track upload progress
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        const pct = Math.round((e.loaded / e.total) * 100);
        onProgress(pct);
      }
    });

    xhr.addEventListener('load', () => {
      try {
        const body = JSON.parse(xhr.responseText);
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(body.data);
        } else {
          reject(new Error(
            body?.detail?.error || body?.error || `Upload failed (${xhr.status})`
          ));
        }
      } catch {
        reject(new Error('Invalid response from server.'));
      }
    });

    xhr.addEventListener('error', () => {
      reject(new Error('Network error. Check your connection and try again.'));
    });

    xhr.addEventListener('abort', () => {
      reject(new Error('Upload was cancelled.'));
    });

    xhr.send(form);
  });
}

/**
 * Format bytes to human readable string.
 * @param {number} bytes
 * @returns {string}
 */
export function formatFileSize(bytes) {
  if (bytes < 1024)        return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
