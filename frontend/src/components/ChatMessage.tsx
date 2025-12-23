import { useState, memo, lazy, Suspense } from 'react';
import type { ReactElement } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import rehypeRaw from 'rehype-raw';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import type { ChatMessageProps } from '../types';
import { useTypewriter } from '../hooks';
import { TypingIndicator } from './TypingIndicator';
import styles from './ChatMessage.module.css';

// Lazy load heavy WorkflowDialog (contains PrimeReact Dialog + Accordion)
const WorkflowDialog = lazy(() =>
  import('./WorkflowDialog').then((m) => ({ default: m.WorkflowDialog }))
);

const ThinkingBox = lazy(() =>
  import('./ThinkingBox').then((m) => ({ default: m.ThinkingBox }))
);

function ChatMessageComponent({ message, onToggleThinking }: ChatMessageProps): ReactElement {
  // ======================
  // STATE, HOOKS & REFS
  // ======================
  const [showWorkflow, setShowWorkflow] = useState(false);
  const isUser = message.role === 'user';

  // Use typewriter effect for assistant messages when complete
  const isComplete = !message.isStreaming && !!message.content;
  const displayedContent = useTypewriter(message.content, isComplete, 5);

  const hasWorkflow = message.workflow && message.workflow.length > 0;
  const hasThinking = message.thinkingItems && message.thinkingItems.length > 0;

  // ======================
  // MIDDLEWARES
  // ======================
  const handleShowWorkflow = () => {
    setShowWorkflow(true);
  };

  const handleHideWorkflow = () => {
    setShowWorkflow(false);
  };

  // ======================
  // RENDER FUNCTIONS
  // ======================
  const renderUserMessage = (): ReactElement => (
    <div className={`${styles.message} ${styles.user}`}>
      <div className={`${styles.content} ${styles.userContent}`}>
        {message.content}
      </div>
    </div>
  );

  const renderThinkingBox = (): ReactElement | null =>
    hasThinking ? (
      <ThinkingBox
        thinkingItems={message.thinkingItems!}
        isStreaming={!!message.isStreaming}
        isExpanded={!!message.thinkingExpanded}
        onToggle={onToggleThinking}
      />
    ) : null;

  const renderMessageContent = (): ReactElement => {
    const contentClasses = `${styles.content} ${styles.assistantContent} ${
      message.isError ? styles.error : ''
    } ${!message.content && message.isStreaming && !hasThinking ? styles.loading : ''}`;

    return (
      <div className={contentClasses}>
        {displayedContent ? (
          <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkBreaks]}
            rehypePlugins={[rehypeRaw]}
            components={{
              code({ className, children, ...props }: any) {
                const match = /language-(\w+)/.exec(className || '');
                const inline = !props.node || props.node.position?.start.line === props.node.position?.end.line;
                return !inline && match ? (
                  <SyntaxHighlighter
                    language={match[1]}
                    PreTag="div"
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className={className} {...props}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {displayedContent}
          </ReactMarkdown>
        ) : message.isStreaming ? (
          <TypingIndicator />
        ) : (
          ''
        )}
      </div>
    );
  };

  const renderWorkflowButton = (): ReactElement | null =>
    hasWorkflow && !message.isStreaming ? (
      <div className={styles.workflowButtonContainer}>
        <button className={styles.workflowButton} onClick={handleShowWorkflow}>
          🔍 Review actions
        </button>
      </div>
    ) : null;

  const renderWorkflowDialog = (): ReactElement | null =>
    hasWorkflow && showWorkflow ? (
      <Suspense fallback={null}>
        <WorkflowDialog
          steps={message.workflow!}
          visible={showWorkflow}
          onHide={handleHideWorkflow}
        />
      </Suspense>
    ) : null;

  const renderAssistantMessage = (): ReactElement => (
    <div className={`${styles.message} ${styles.assistant}`}>
      <div className={styles.assistantContainer}>
        {renderThinkingBox()}
        {renderMessageContent()}
        {renderWorkflowButton()}
      </div>
      {renderWorkflowDialog()}
    </div>
  );

  if (isUser) {
    return renderUserMessage();
  }

  return renderAssistantMessage();
}

export const ChatMessage = memo(ChatMessageComponent);
