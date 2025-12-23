import type { ReactElement } from 'react';
import { memo, useState } from 'react';
import styles from './ToolBadge.module.css';

interface ToolBadgeProps {
  toolName: string;
  toolMessage: string;
  toolInput?: unknown;
}

function ToolBadgeComponent({
  toolName,
  toolMessage,
  toolInput,
}: ToolBadgeProps): ReactElement {
  const [isExpanded, setIsExpanded] = useState(false);

  const hasInput = 
    !!toolInput && 
    !(typeof toolInput === 'object' && Object.keys(toolInput as object).length === 0);

  const renderJsonInput = (): ReactElement | null => {
    if (!hasInput || !isExpanded) return null;

    try {
      // Parse input if it's a string, otherwise use as-is
      const inputData = typeof toolInput === 'string' ? JSON.parse(toolInput) : toolInput;
      
      // If it's a simple value, just display it
      if (typeof inputData !== 'object' || inputData === null) {
        return (
          <div className={styles.toolInputContent}>
            <div className={styles.toolInputValue}>{String(inputData)}</div>
          </div>
        );
      }

      // Render object as key-value pairs
      return (
        <div className={styles.toolInputContent}>
          {Object.entries(inputData).map(([key, value]) => (
            <div key={key} className={styles.toolInputRow}>
              <span className={styles.toolInputKey}>{key}:</span>
              <span className={styles.toolInputValue}>
                {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
              </span>
            </div>
          ))}
        </div>
      );
    } catch (error) {
      // If JSON parsing fails, display as string
      return (
        <div className={styles.toolInputContent}>
          <div className={styles.toolInputValue}>{String(toolInput)}</div>
        </div>
      );
    }
  };

  const handleToggle = (): void => {
    if (hasInput) {
      setIsExpanded(!isExpanded);
    }
  };

  return (
    <div className={styles.toolBadgeContainer}>
      <button
        className={`${styles.thinkingToolBadge} ${hasInput ? styles.clickable : ''} ${isExpanded ? styles.expanded : ''}`}
        onClick={handleToggle}
        type="button"
        disabled={!hasInput}
      >
        {hasInput && (
          <span className={styles.toolToggleIcon}>
            {isExpanded ? '▼' : '▶'}
          </span>
        )}
        <span>{toolMessage || `🔧 ${toolName}`}</span>
      </button>
      {hasInput && renderJsonInput()}
    </div>
  );
}

export const ToolBadge = memo(ToolBadgeComponent);
