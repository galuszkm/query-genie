import type { ReactElement } from 'react';
import { memo } from 'react';
import styles from './ChatMessage.module.css';

function TypingIndicatorComponent(): ReactElement {
  // ======================
  // STATE, HOOKS & REFS
  // ======================

  // ======================
  // MIDDLEWARES
  // ======================

  // ======================
  // RENDER FUNCTIONS
  // ======================
  return (
    <span className={styles.typingIndicator}>
      <span className={styles.dot}></span>
      <span className={styles.dot}></span>
      <span className={styles.dot}></span>
    </span>
  );
}

export const TypingIndicator = memo(TypingIndicatorComponent);
