import type { ReactElement } from 'react';
import { useCallback, useEffect, useState, memo } from 'react';
import type { WelcomeScreenProps } from '../types';
import { fetchWelcomeConfig } from '../services/api';
import styles from './WelcomeScreen.module.css';

function WelcomeScreenComponent({ onSuggestionClick }: WelcomeScreenProps): ReactElement {
  // ======================
  // STATE, HOOKS & REFS
  // ======================
  const [title, setTitle] = useState<string>('Welcome!');
  const [subtitle, setSubtitle] = useState<string>('Try questions like:');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadWelcomeConfig() {
      setIsLoading(true);
      const config = await fetchWelcomeConfig();
      setTitle(config.title);
      setSubtitle(config.subtitle);
      setSuggestions(config.suggestions);
      setIsLoading(false);
    }
    loadWelcomeConfig();
  }, []);

  // ======================
  // MIDDLEWARES
  // ======================
  const handleSuggestionClick = useCallback(
    (suggestion: string) => () => {
      onSuggestionClick(suggestion);
    },
    [onSuggestionClick]
  );

  // ======================
  // RENDER FUNCTIONS
  // ======================
  const renderSuggestionItem = (suggestion: string): ReactElement => (
    <li
      key={suggestion}
      className={styles.suggestion}
      onClick={handleSuggestionClick(suggestion)}
    >
      &quot;{suggestion}&quot;
    </li>
  );

  const renderSuggestionsList = (): ReactElement => {
    if (isLoading) {
      return <p className={styles.loading}>Loading suggestions...</p>;
    }
    
    if (suggestions.length === 0) {
      return <p className={styles.empty}>No suggestions available</p>;
    }
    
    return (
      <ul className={styles.suggestions}>
        {suggestions.map(renderSuggestionItem)}
      </ul>
    );
  };

  return (
    <div className={styles.welcome}>
      <h2 className={styles.title}>{title}</h2>
      <p className={styles.subtitle}>{subtitle}</p>
      {renderSuggestionsList()}
    </div>
  );
}

export const WelcomeScreen = memo(WelcomeScreenComponent);
