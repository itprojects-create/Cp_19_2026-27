import React from 'react';
import styles from './BottomCTA.module.css';

interface BottomCTAProps {
  children: React.ReactNode;
  caption?: string;
}

export const BottomCTA: React.FC<BottomCTAProps> = ({ children, caption }) => {
  return (
    <div className={styles.container}>
      {children}
      {caption && <div className={styles.caption}>{caption}</div>}
    </div>
  );
};
