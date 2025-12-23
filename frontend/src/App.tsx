import type { ReactElement } from 'react';
import { useRef, useEffect, useCallback } from 'react';
import { Header, WelcomeScreen, ChatMessage, ChatInput } from './components';
import { useChat } from './hooks';
import styles from './App.module.css';

export function App(): ReactElement {
  // ======================
  // STATE, HOOKS & REFS
  // ======================
  const { messages, isLoading, sessionId, sendMessage, clearChat, toggleThinking, stopGeneration } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const prevMessageCountRef = useRef(0);

  useEffect(() => {
    // Only auto-scroll when a new message is added or when streaming
    const hasNewMessage = messages.length > prevMessageCountRef.current;
    const lastMessage = messages[messages.length - 1];
    const isStreaming = lastMessage?.isStreaming;

    if (hasNewMessage || isStreaming) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }

    prevMessageCountRef.current = messages.length;
  }, [messages]);

  // ======================
  // MIDDLEWARES
  // ======================
  const handleSuggestionClick = useCallback(
    (text: string): void => {
      sendMessage(text);
    },
    [sendMessage]
  );

  // ======================
  // RENDER FUNCTIONS
  // ======================
  const renderMessages = (): ReactElement => (
    <div className={styles.messages}>
      {messages.map((message) => (
        <ChatMessage
          key={message.id}
          message={message}
          onToggleThinking={() => toggleThinking(message.id)}
        />
      ))}
      <div ref={messagesEndRef} />
    </div>
  );

  const renderMainContent = (): ReactElement =>
    messages.length === 0 ? (
      <WelcomeScreen onSuggestionClick={handleSuggestionClick} />
    ) : (
      renderMessages()
    );

  return (
    <div className={styles.app}>
      <Header onClearChat={clearChat} sessionId={sessionId} />
      <main className={styles.chatContainer}>{renderMainContent()}</main>
      <ChatInput onSend={sendMessage} onStop={stopGeneration} isLoading={isLoading} />
    </div>
  );
}

export default App;
