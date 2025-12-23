import { useState } from 'react';
import type { ReactElement } from 'react';
import { Dialog } from 'primereact/dialog';
import type { WorkflowDialogProps, WorkflowStep } from '../types';
import { ReasoningStep } from './ReasoningStep';
import { ToolStep } from './ToolStep';
import styles from './WorkflowDialog.module.css';

export function WorkflowDialog({
  steps,
  visible,
  onHide,
}: WorkflowDialogProps): ReactElement {
  // ======================
  // STATE, HOOKS & REFS
  // ======================
  const [expandedTabs, setExpandedTabs] = useState<number[]>([]);

  // ======================
  // MIDDLEWARES
  // ======================
  const handleTabToggle = (index: number, isOpen: boolean) => {
    setExpandedTabs((prev) =>
      isOpen ? [...prev, index] : prev.filter((i) => i !== index)
    );
  };

  // ======================
  // RENDER FUNCTIONS
  // ======================
  const renderDialogHeader = (): ReactElement => (
    <div className={styles.dialogHeader}>
      <span className={styles.dialogTitle}>🔍 Agent Workflow</span>
      <span className={styles.stepCount}>{steps.length} steps</span>
    </div>
  );

  const renderStepContent = (step: WorkflowStep, index: number): ReactElement =>
    step.type === 'reasoning' ? (
      <ReasoningStep content={step.content} />
    ) : (
      <ToolStep
        step={step}
        index={index}
        isExpanded={expandedTabs.includes(index)}
        onToggle={handleTabToggle}
      />
    );

  const renderStep = (step: WorkflowStep, index: number): ReactElement => (
    <div key={index} className={styles.stepWrapper}>
      <div className={styles.stepNumber}>{step.step}</div>
      <div className={styles.stepContent}>{renderStepContent(step, index)}</div>
    </div>
  );

  const renderSteps = (): ReactElement => (
    <div className={styles.stepsContainer}>{steps.map(renderStep)}</div>
  );

  return (
    <Dialog
      header={renderDialogHeader()}
      visible={visible}
      onHide={onHide}
      className={styles.workflowDialog}
      style={{ width: '70vw', height: '80vh' }}
      modal
      maximizable
      draggable
      resizable
    >
      {renderSteps()}
    </Dialog>
  );
}
