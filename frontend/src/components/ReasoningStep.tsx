import type { ReactElement } from 'react';
import { memo } from 'react';
import type { ReasoningStepProps } from '../types';
import styles from './WorkflowDialog.module.css';

function ReasoningStepComponent({ content }: ReasoningStepProps): ReactElement {
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
    <div className={styles.reasoningStep}>
      <div className={styles.stepLabel}>💭 Reasoning</div>
      <div className={styles.reasoningText}>{content}</div>
    </div>
  );
}

export const ReasoningStep = memo(ReasoningStepComponent);
