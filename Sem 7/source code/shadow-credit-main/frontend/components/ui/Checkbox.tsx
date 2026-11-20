import React from 'react';
import styles from './Checkbox.module.css';

interface CheckboxProps {
  label: string | React.ReactNode;
  checked: boolean;
  onChange: (checked: boolean) => void;
  id?: string;
}

export const Checkbox: React.FC<CheckboxProps> = ({ label, checked, onChange, id }) => {
  return (
    <label className={styles.container} htmlFor={id}>
      <input
        type="checkbox"
        id={id}
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className={styles.hiddenInput}
      />
      <div className={`${styles.checkbox} ${checked ? styles.checked : ''}`}>
        {checked && (
          <svg width="14" height="11" viewBox="0 0 14 11" fill="none">
            <path
              d="M1 5.5L5 9.5L13 1.5"
              stroke="white"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}
      </div>
      <span className={styles.label}>{label}</span>
    </label>
  );
};
