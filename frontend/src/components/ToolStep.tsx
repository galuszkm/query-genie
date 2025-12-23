import type { ReactElement } from 'react';
import { memo, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Accordion, AccordionTab } from 'primereact/accordion';
import type { ToolStepProps } from '../types';
import { formatInput, formatOutput } from '../helpers';
import styles from './WorkflowDialog.module.css';

function ToolStepComponent({
  step,
  index,
  isExpanded,
  onToggle,
}: ToolStepProps): ReactElement {
  // ======================
  // STATE, HOOKS & REFS
  // ======================

  // ======================
  // MIDDLEWARES
  // ======================
  const handleTabChange = useCallback(
    (e: { index: number | number[] | null | undefined }) => {
      onToggle(index, e.index === 0);
    },
    [index, onToggle]
  );

  // ======================
  // RENDER FUNCTIONS
  // ======================
  const renderToolHeader = (): ReactElement => (
    <div className={styles.toolHeader}>
      <span className={styles.toolIcon}>🔧</span>
      <span className={styles.toolName}>{step.name}</span>
      <span
        className={`${styles.toolStatus} ${
          step.status === 'success' ? styles.success : styles.error
        }`}
      >
        {step.status === 'success' ? '✓' : '✗'}
      </span>
    </div>
  );

  const renderInputSection = (): ReactElement => (
    <div className={styles.toolSection}>
      <div className={styles.sectionTitle}>Input</div>
      <div className={styles.sectionContent}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {formatInput(step.input)}
        </ReactMarkdown>
      </div>
    </div>
  );

  const renderOutputSection = (): ReactElement => (
    <div className={styles.toolSection}>
      <div className={styles.sectionTitle}>Output</div>
      <div className={styles.sectionContent}>
        <pre className={styles.outputPre}>{formatOutput(step.output)}</pre>
      </div>
    </div>
  );

  return (
    <div className={styles.toolStep}>
      <Accordion
        activeIndex={isExpanded ? 0 : null}
        onTabChange={handleTabChange}
      >
        <AccordionTab header={renderToolHeader()}>
          <div className={styles.toolDetails}>
            {renderInputSection()}
            {renderOutputSection()}
          </div>
        </AccordionTab>
      </Accordion>
    </div>
  );
}

export const ToolStep = memo(ToolStepComponent);
