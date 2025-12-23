import type { ReactElement, FormEvent, ChangeEvent } from 'react';
import { useState, useRef, useEffect, useCallback } from 'react';
import { Button } from 'primereact/button';
import type { ChatInputProps } from '../types';
import styles from './ChatInput.module.css';

export function ChatInput({ onSend, onStop, isLoading }: ChatInputProps): ReactElement {
  // ======================
  // STATE, HOOKS & REFS
  // ======================
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, [isLoading]);

  // ======================
  // MIDDLEWARES
  // ======================
  const handleSubmit = useCallback(
    (e: FormEvent): void => {
      e.preventDefault();
      const text = input.trim();
      if (text && !isLoading) {
        onSend(text);
        setInput('');
      }
    },
    [input, isLoading, onSend]
  );

  const handleStop = useCallback(
    (e: FormEvent): void => {
      e.preventDefault();
      onStop();
    },
    [onStop]
  );

  const handleChange = (e: ChangeEvent<HTMLInputElement>): void => {
    setInput(e.target.value);
  };

  // ======================
  // RENDER FUNCTIONS
  // ======================
  const renderInput = (): ReactElement => (
    <input
      ref={inputRef}
      type="text"
      value={input}
      onChange={handleChange}
      placeholder="Ask some question..."
      disabled={isLoading}
      className={styles.input}
    />
  );

  const renderButton = (): ReactElement => {
    if (isLoading) {
      return (
        <Button
          type="button"
          onClick={handleStop}
          className={styles.stopButton}
          icon="pi pi-stop-circle margin-right-2"
          label="Stop"
          severity="danger"
        />
      );
    }
    return (
      <Button
        type="submit"
        disabled={!input.trim()}
        className={styles.sendButton}
        icon="pi pi-send margin-right-2"
        label="Send"
      />
    );
  };

  return (
    <footer className={styles.inputArea}>
      <form onSubmit={handleSubmit} className={styles.form}>
        {renderInput()}
        {renderButton()}
      </form>
    </footer>
  );
}
