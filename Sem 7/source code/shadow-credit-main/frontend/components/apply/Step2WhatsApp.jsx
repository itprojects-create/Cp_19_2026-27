'use client';

import { useState, useRef, useCallback } from 'react';
import { FileText, X, Upload } from 'lucide-react';
import { uploadWithProgress, formatFileSize } from '@/lib/uploadWithProgress';
import styles from './Step2WhatsApp.module.css';

const ACCEPTED_TYPES = ['.txt', '.zip', 'text/plain', 'application/zip',
                        'application/x-zip-compressed'];

export default function Step2WhatsApp({ onNext, onBack, sessionData }) {
  const [file,        setFile]        = useState(null);
  const [dragActive,  setDragActive]  = useState(false);
  const [progress,    setProgress]    = useState(0);
  const [uploading,   setUploading]   = useState(false);
  const [uploaded,    setUploaded]    = useState(false);
  const [error,       setError]       = useState('');
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
    const dropped = e.dataTransfer.files[0];
    if (dropped) validateAndSetFile(dropped);
  }, []);

  function handleFileInput(e) {
    const selected = e.target.files[0];
    if (selected) validateAndSetFile(selected);
  }

  function validateAndSetFile(f) {
    const ext  = '.' + f.name.split('.').pop().toLowerCase();
    const valid = ACCEPTED_TYPES.some(
      (t) => t === ext || t === f.type
    );
    if (!valid) {
      setError('Only .txt or .zip files are accepted. Export without media from WhatsApp.');
      return;
    }
    if (f.size > 50 * 1024 * 1024) {
      setError('File is too large. Maximum size is 50MB.');
      return;
    }
    setError('');
    setFile(f);
    setUploaded(false);
    setProgress(0);
  }

  function removeFile() {
    setFile(null);
    setUploaded(false);
    setProgress(0);
    setError('');
    if (inputRef.current) inputRef.current.value = '';
  }

  async function handleContinue() {
    if (!file) { onNext({ whatsappUploaded: false }); return; }
    if (uploaded) { onNext({ whatsappUploaded: true }); return; }

    setUploading(true);
    setError('');

    try {
      await uploadWithProgress(
        sessionId,
        file,
        'WHATSAPP',
        setProgress
      );
      setUploaded(true);
      setTimeout(() => onNext({ whatsappUploaded: true }), 600);
    } catch (err) {
      setError(err.message);
      setUploading(false);
      setProgress(0);
    }
  }

  function handleSkip() {
    onNext({ whatsappUploaded: false });
  }

  return (
    <div className={styles.step}>

      <div className={styles.heading}>
        <h2 className={styles.title}>WhatsApp business chat</h2>
        <p className={styles.subtitle}>
          Your chat history shows how often customers pay you and how
          much. This is one of the strongest signals for your credit score.
        </p>
      </div>

      <div className={styles.howTo}>
        <span className={styles.howToLabel}>How to export your chat</span>
        <ol className={styles.howToList}>
          <li>Open WhatsApp and go to your main business chat</li>
          <li>Tap the three dots (⋮) → More → Export Chat</li>
          <li>Select <strong>Without Media</strong></li>
          <li>Save the file and upload it below</li>
        </ol>
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
          aria-label="Click or drag to upload WhatsApp export"
          onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
        >
          <Upload
            size={28}
            strokeWidth={1.5}
            className={styles.dropIcon}
          />
          <span className={styles.dropTitle}>
            Drop your chat export here
          </span>
          <span className={styles.dropSubtitle}>
            or tap to browse files
          </span>
          <span className={styles.dropAccepted}>
            Accepts .txt or .zip — max 50MB
          </span>
          <input
            ref={inputRef}
            type="file"
            accept=".txt,.zip"
            className={styles.hiddenInput}
            onChange={handleFileInput}
            tabIndex={-1}
          />
        </div>
      ) : (
        <div className={`${styles.fileCard} ${uploaded ? styles.fileCardSuccess : ''}`}>
          <div className={styles.fileCardLeft}>
            <div className={styles.fileIconWrap}>
              <FileText size={20} strokeWidth={1.5} />
            </div>
            <div className={styles.fileInfo}>
              <span className={styles.fileName}>{file.name}</span>
              <span className={styles.fileMeta}>
                {formatFileSize(file.size)}
                {uploaded && (
                  <span className={styles.uploadedBadge}>
                    ✓ Uploaded
                  </span>
                )}
              </span>
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
        {uploading && (
          <span
            className={styles.progressFill}
            style={{ width: `${progress}%` }}
          />
        )}
        <span className={styles.btnContent}>
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
              <span>Continue without uploading</span>
              <span className={styles.btnArrow}>→</span>
            </>
          )}
        </span>
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
