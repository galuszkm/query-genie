import type { ReactElement } from 'react';
import { memo } from 'react';
import type { ThinkingItem, ThinkingBoxProps } from '../types';
import { ToolBadge } from './ToolBadge';
import styles from './ChatMessage.module.css';

function ThinkingBoxComponent({
  thinkingItems,
  isStreaming,
  isExpanded,
  onToggle,
}: ThinkingBoxProps): ReactElement {
  // ======================
  // STATE, HOOKS & REFS
  // ======================

  // ======================
  // MIDDLEWARES
  // ======================

  // ======================
  // RENDER FUNCTIONS
  // ======================
  const renderThinkingItem = (item: ThinkingItem, index: number): ReactElement =>
    item.type === 'text' ? (
      <span key={index} className={styles.thinkingText}>
        {item.content}
      </span>
    ) : (
      <ToolBadge
        key={index}
        toolName={item.toolName || 'Unknown Tool'}
        toolMessage={item.toolMessage || `🔧 ${item.toolName}`}
        toolInput={item.toolInput}
      />
    );

  const renderHeader = (): ReactElement => (
    <button
      className={styles.thinkingHeader}
      onClick={onToggle}
      type="button"
    >
      <span className={styles.thinkingIcon}>
        {isStreaming ? '🧠' : '💭'}
      </span>
      <span className={styles.thinkingTitle}>
        {isStreaming ? 'Thinking...' : 'Reasoning'}
      </span>
      <span className={styles.thinkingToggle}>
        {isExpanded ? '▼' : '▶'}
      </span>
    </button>
  );

  const renderContent = (): ReactElement | null =>
    isExpanded ? (
      <div className={styles.thinkingContent}>
        {thinkingItems.map(renderThinkingItem)}
      </div>
    ) : null;

  return (
    <div
      className={`${styles.thinkingBox} ${isExpanded ? styles.expanded : styles.collapsed}`}
    >
      {renderHeader()}
      {renderContent()}
    </div>
  );
}

export const ThinkingBox = memo(ThinkingBoxComponent);
