import type { ReactElement } from 'react';
import { memo } from 'react';
import type { HeaderProps } from '../types';
import styles from './Header.module.css';

function HeaderComponent({ onClearChat, sessionId }: HeaderProps): ReactElement {
  // ======================
  // STATE, HOOKS & REFS
  // ======================

  // ======================
  // MIDDLEWARES
  // ======================
  const handleClearClick = () => {
    onClearChat();
  };

  const handleSessionDetailsClick = () => {
    if (!sessionId) return;
    const sessionUrl = `/ai/api/session/${sessionId}`;
    window.open(sessionUrl, '_blank');
  };

  // ======================
  // RENDER FUNCTIONS
  // ======================
  const renderTitle = (): ReactElement => (
    <>
      <h1 className={styles.title}>🤖 AI Agent Assistant</h1>
      <span className={styles.subtitle}>Powered by Strands Agents + PostgreSQL</span>
      <div className={styles.author}>Developed by<br/>
        <a 
          href="https://github.com/galuszkm" 
          target="_blank" 
          rel="noopener noreferrer" 
          style={{ color: '#ddeaf7ff', textDecoration: 'underline' }}>
          Michal Galuszka
        </a>
      </div>
    </>
  );

  const renderButtons = (): ReactElement => (
    <div className={styles.buttonGroup}>
      <button
        onClick={handleSessionDetailsClick}
        className={styles.sessionButton}
        title="View session details and metrics"
        disabled={!sessionId}
      >
        Session Details
      </button>
      <button
        onClick={handleClearClick}
        className={styles.clearButton}
        title="Start new conversation"
      >
        Clear Chat
      </button>
    </div>
  );

  return (
    <header className={styles.header}>
      {renderTitle()}
      {renderButtons()}
    </header>
  );
}

export const Header = memo(HeaderComponent);
