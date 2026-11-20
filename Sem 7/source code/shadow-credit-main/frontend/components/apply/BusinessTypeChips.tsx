import React from 'react';
import styles from './BusinessTypeChips.module.css';

const businessTypes = [
  { id: 'kirana', icon: '🛒', label: 'Kirana / General Store' },
  { id: 'tailor', icon: '✂️', label: 'Tailor / Clothing' },
  { id: 'food', icon: '🍱', label: 'Food / Restaurant' },
  { id: 'other', icon: '🔧', label: 'Other Business' },
];

interface BusinessTypeChipsProps {
  selected: string | null;
  onSelect: (id: string) => void;
}

export const BusinessTypeChips: React.FC<BusinessTypeChipsProps> = ({ selected, onSelect }) => {
  return (
    <div className={styles.grid}>
      {businessTypes.map((type) => (
        <button
          key={type.id}
          className={`${styles.chip} ${selected === type.id ? styles.selected : ''}`}
          onClick={() => onSelect(type.id)}
          type="button"
        >
          <span className={styles.icon}>{type.icon}</span>
          <span className={styles.label}>{type.label}</span>
        </button>
      ))}
    </div>
  );
};
