'use client';

import { useState, useRef, useCallback } from 'react';
import { ImagePlus, X, Upload } from 'lucide-react';
import { uploadWithProgress, formatFileSize } from '@/lib/uploadWithProgress';
import styles from './Step3UPI.module.css';

const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp',
                               'image/heic', 'image/heif'];
const MAX_FILES = 10;
const MAX_FILE_SIZE = 20 * 1024 * 1024;

export default function Step3UPI({ onNext, onBack, sessionData }) {
  const [files,       setFiles]       = useState([]);
  const [dragActive,  setDragActive]  = useState(false);
  const [uploading,   setUploading]   = useState(false);
  const [uploadState, setUploadState] = useState({});
  const [globalError, setGlobalError] = useState('');
  const inputRef  = useRef(null);
  const addRef    = useRef(null);

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
    const dropped = Array.from(e.dataTransfer.files);
    addFiles(dropped);
  }, [files]);

  function addFiles(incoming) {
    setGlobalError('');
    const valid = [];
    const errors = [];

    for (const f of incoming) {
      if (!ACCEPTED_IMAGE_TYPES.includes(f.type)) {
        errors.push(`${f.name}: not a valid image type.`);
        continue;
      }
      if (f.size > MAX_FILE_SIZE) {
        errors.push(`${f.name}: exceeds 20MB limit.`);
        continue;
      }
      const duplicate = files.some((ex) => ex.name === f.name && ex.size === f.size);
      if (duplicate) continue;
      valid.push(f);
    }

    if (errors.length > 0) {
      setGlobalError(errors[0]);
    }

    setFiles((prev) => {
      const combined = [...prev, ...valid];
      return combined.slice(0, MAX_FILES);
    });
  }

  function handleFileInput(e) {
    const selected = Array.from(e.target.files);
    addFiles(selected);
    e.target.value = '';
  }

  function removeFile(index) {
    setFiles((prev) => prev.filter((_, i) => i !== index));
    setGlobalError('');
  }

  async function handleContinue() {
    if (files.length === 0) {
      onNext({});
      return;
    }

    setUploading(true);
    setGlobalError('');

    const initialState = {};
    files.forEach((f) => {
      initialState[f.name] = { progress: 0, done: false, error: '' };
    });
    setUploadState(initialState);

    let allSucceeded = true;

    for (const file of files) {
      try {
        await uploadWithProgress(
          sessionId,
          file,
          'UPI',
          (pct) => {
            setUploadState((prev) => ({
              ...prev,
              [file.name]: { ...prev[file.name], progress: pct },
            }));
          }
        );
        setUploadState((prev) => ({
          ...prev,
          [file.name]: { progress: 100, done: true, error: '' },
        }));
      } catch (err) {
        setUploadState((prev) => ({
          ...prev,
          [file.name]: { ...prev[file.name], error: err.message },
        }));
        allSucceeded = false;
      }
    }

    setUploading(false);

    if (allSucceeded) {
      setTimeout(() => onNext({ upiCount: files.length }), 700);
    } else {
      setGlobalError('Some files failed to upload. Remove them and try again.');
    }
  }

  function handleSkip() {
    onNext({});
  }

  const allDone = files.length > 0
    && files.every((f) => uploadState[f.name]?.done);

  return (
    <div className={styles.step}>

      <div className={styles.heading}>
        <h2 className={styles.title}>UPI payment screenshots</h2>
        <p className={styles.subtitle}>
          Screenshot your UPI app showing recent transactions.
          PhonePe, Google Pay, Paytm, or any UPI app works.
          More screenshots = stronger credit signal.
        </p>
      </div>

      <div className={styles.hint}>
        <span className={styles.hintLabel}>Tip</span>
        <span className={styles.hintText}>
          Include at least 3 months of transaction history if possible.
          Payments received from customers matter most.
        </span>
      </div>

      {files.length === 0 ? (
        <div
          className={`${styles.dropZone} ${dragActive ? styles.dropZoneActive : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          aria-label="Click or drag to upload UPI screenshots"
          onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
        >
          <ImagePlus
            size={28}
            strokeWidth={1.5}
            className={styles.dropIcon}
          />
          <span className={styles.dropTitle}>
            Drop UPI screenshots here
          </span>
          <span className={styles.dropSubtitle}>
            or tap to browse your gallery
          </span>
          <span className={styles.dropAccepted}>
            JPG, PNG, HEIC — up to {MAX_FILES} files — max 20MB each
          </span>
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            multiple
            className={styles.hiddenInput}
            onChange={handleFileInput}
            tabIndex={-1}
          />
        </div>
      ) : (
        <div className={styles.previewSection}>
          <div className={styles.previewGrid}>
            {files.map((file, index) => {
              const state = uploadState[file.name];
              const url   = URL.createObjectURL(file);
              return (
                <div key={`${file.name}-${index}`} className={styles.thumb}>
                  <img
                    src={url}
                    alt={file.name}
                    className={styles.thumbImg}
                  />

                  {state && !state.done && !state.error && (
                    <div className={styles.thumbOverlay}>
                      <span className={styles.thumbProgress}>
                        {state.progress}%
                      </span>
                      <div className={styles.thumbBar}>
                        <div
                          className={styles.thumbBarFill}
                          style={{ width: `${state.progress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {state?.done && (
                    <div className={styles.thumbDone}>✓</div>
                  )}

                  {state?.error && (
                    <div className={styles.thumbError}>!</div>
                  )}

                  {!uploading && (
                    <button
                      className={styles.thumbRemove}
                      onClick={() => removeFile(index)}
                      aria-label={`Remove ${file.name}`}
                      type="button"
                    >
                      <X size={10} strokeWidth={3} />
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          <div className={styles.fileCount}>
            {files.length} screenshot{files.length !== 1 ? 's' : ''} selected
            {files.length < MAX_FILES && (
              <span className={styles.maxNote}>
                {' '}(max {MAX_FILES})
              </span>
            )}
          </div>

          {files.length < MAX_FILES && !uploading && (
            <div
              className={styles.addMore}
              onClick={() => addRef.current?.click()}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && addRef.current?.click()}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <Upload size={14} strokeWidth={1.5} />
              <span>Add more screenshots +</span>
              <input
                ref={addRef}
                type="file"
                accept="image/*"
                multiple
                className={styles.hiddenInput}
                onChange={handleFileInput}
                tabIndex={-1}
              />
            </div>
          )}
        </div>
      )}

      {globalError && (
        <div className={styles.errorMsg}>
          <span className={styles.errorDot} />
          {globalError}
        </div>
      )}

      <button
        className={styles.continueBtn}
        onClick={handleContinue}
        disabled={uploading}
        type="button"
      >
        <span className={styles.btnContent}>
          {uploading ? (
            <>
              <span className={styles.spinner} aria-hidden="true" />
              <span>
                Uploading {files.filter((f) => uploadState[f.name]?.done).length}
                /{files.length}...
              </span>
            </>
          ) : allDone ? (
            <>
              <span>All uploaded ✓  Continue</span>
              <span className={styles.btnArrow}>→</span>
            </>
          ) : files.length > 0 ? (
            <>
              <span>Upload {files.length} screenshot{files.length !== 1 ? 's' : ''}</span>
              <span className={styles.btnArrow}>→</span>
            </>
          ) : (
            <>
              <span>Continue without screenshots</span>
              <span className={styles.btnArrow}>→</span>
            </>
          )}
        </span>
      </button>

      <button className={styles.skipBtn} onClick={handleSkip} type="button">
        Skip for now →
      </button>

    </div>
  );
}
