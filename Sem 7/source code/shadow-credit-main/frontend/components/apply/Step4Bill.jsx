'use client';

import { useState, useRef, useCallback } from 'react';
import { Receipt, X, Upload, FileText } from 'lucide-react';
import { uploadWithProgress, formatFileSize } from '@/lib/uploadWithProgress';
import styles from './Step4Bill.module.css';

const ACCEPTED_TYPES = [
  'image/jpeg', 'image/png', 'image/webp', 'image/heic',
  'application/pdf',
];
const ACCEPTED_EXT   = ['.jpg', '.jpeg', '.png', '.webp', '.heic', '.pdf'];
const MAX_SIZE_BYTES = 10 * 1024 * 1024;

export default function Step4Bill({ onNext, onBack, sessionData }) {
  const [file,       setFile]       = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [progress,   setProgress]   = useState(0);
  const [uploading,  setUploading]  = useState(false);
  const [uploaded,   setUploaded]   = useState(false);
  const [error,      setError]      = useState('');
  const inputRef = useRef(null);

  const sessionId = sessionData?.sessionId
    || (typeof window !== 'undefined' && localStorage.getItem('sc_session_id'));

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const f = e.dataTransfer.files[0];
    if (f) validateAndSet(f);
  }, []);

  function validateAndSet(f) {
    const ext   = '.' + f.name.split('.').pop().toLowerCase();
    const valid = ACCEPTED_TYPES.includes(f.type) || ACCEPTED_EXT.includes(ext);
    if (!valid) {
      setError('Only JPG, PNG, or PDF files accepted.');
      return;
    }
    if (f.size > MAX_SIZE_BYTES) {
      setError('File too large. Maximum size is 10MB.');
      return;
    }
    setError('');
    setFile(f);
    setUploaded(false);
    setProgress(0);
  }

  function handleFileInput(e) {
    const f = e.target.files[0];
    if (f) validateAndSet(f);
    e.target.value = '';
  }

  function removeFile() {
    setFile(null);
    setUploaded(false);
    setProgress(0);
    setError('');
    if (inputRef.current) inputRef.current.value = '';
  }

  async function handleContinue() {
    if (!file || uploaded) { onNext({}); return; }

    setUploading(true);
    setError('');

    try {
      await uploadWithProgress(
        sessionId,
        file,
        'BILL',
        setProgress
      );
      setUploaded(true);
      setTimeout(() => onNext({ billUploaded: true }), 600);
    } catch (err) {
      setError(err.message);
      setUploading(false);
      setProgress(0);
    }
  }

  function handleSkip() {
    onNext({});
  }

  const isPDF = file?.type === 'application/pdf'
    || file?.name?.toLowerCase().endsWith('.pdf');

  return (
    <div className={styles.step}>

      <div className={styles.heading}>
        <div className={styles.titleRow}>
          <h2 className={styles.title}>Utility bill or address proof</h2>
          <span className={styles.optionalBadge}>Optional</span>
        </div>
        <p className={styles.subtitle}>
          An electricity bill, rent receipt, or shop license confirms
          your business address and strengthens your application
          significantly. You can skip this if you don't have it ready.
        </p>
      </div>

      <div className={styles.strengthBlock}>
        <div className={styles.strengthRow}>
          <span className={styles.strengthLabel}>
            Application strength without this
          </span>
          <span className={styles.strengthValue}>Good</span>
        </div>
        <div className={styles.strengthBar}>
          <div className={styles.strengthFillGood} />
        </div>
        <div className={styles.strengthRow}>
          <span className={styles.strengthLabel}>
            Application strength with this
          </span>
          <span className={styles.strengthValueBetter}>Excellent</span>
        </div>
        <div className={styles.strengthBar}>
          <div className={styles.strengthFillExcellent} />
        </div>
      </div>

      {!file ? (
        <div
          className={`${styles.dropZone} ${dragActive ? styles.dropZoneActive : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          aria-label="Click or drag to upload bill"
          onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
        >
          <Receipt size={28} strokeWidth={1.5} className={styles.dropIcon} />
          <span className={styles.dropTitle}>
            Upload electricity bill or address proof
          </span>
          <span className={styles.dropSubtitle}>or tap to browse files</span>
          <span className={styles.dropAccepted}>
            JPG, PNG or PDF — max 10MB
          </span>
          <input
            ref={inputRef}
            type="file"
            accept="image/*,.pdf"
            className={styles.hiddenInput}
            onChange={handleFileInput}
            tabIndex={-1}
          />
        </div>
      ) : (
        <div className={`${styles.fileCard} ${uploaded ? styles.fileCardSuccess : ''}`}>
          <div className={styles.fileCardLeft}>
            <div className={styles.fileIconWrap}>
              {isPDF
                ? <Receipt size={20} strokeWidth={1.5} />
                : <Upload size={20} strokeWidth={1.5} />
              }
            </div>
            <div className={styles.fileInfo}>
              <span className={styles.fileName}>{file.name}</span>
              <span className={styles.fileMeta}>
                {formatFileSize(file.size)}
                {' · '}
                {isPDF ? 'PDF Document' : 'Image'}
                {uploaded && (
                  <span className={styles.uploadedBadge}>✓ Uploaded</span>
                )}
              </span>
              {uploading && !uploaded && (
                <div className={styles.fileProgress}>
                  <div
                    className={styles.fileProgressFill}
                    style={{ width: `${progress}%` }}
                  />
                </div>
              )}
            </div>
          </div>
          {!uploading && (
            <button
              className={styles.removeBtn}
              onClick={removeFile}
              aria-label="Remove file"
              type="button"
            >
              <X size={14} strokeWidth={2} />
            </button>
          )}
        </div>
      )}

      {error && (
        <div className={styles.errorMsg}>
          <span className={styles.errorDot} />
          {error}
        </div>
      )}

      <button
        className={styles.continueBtn}
        onClick={handleContinue}
        disabled={uploading}
        type="button"
      >
        {uploading ? (
          <>
            <span className={styles.spinner} aria-hidden="true" />
            <span>Uploading... {progress}%</span>
          </>
        ) : uploaded ? (
          <>
            <span>Uploaded ✓  Continue</span>
            <span className={styles.btnArrow}>→</span>
          </>
        ) : file ? (
          <>
            <span>Upload &amp; Continue</span>
            <span className={styles.btnArrow}>→</span>
          </>
        ) : (
          <>
            <span>Continue without bill</span>
            <span className={styles.btnArrow}>→</span>
          </>
        )}
      </button>

      <button
        className={styles.skipBtn}
        onClick={handleSkip}
        type="button"
      >
        Skip for now →
      </button>

    </div>
  );
}
