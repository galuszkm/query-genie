import { useState, useCallback, useRef } from 'react';
import type { Message, ChatStreamEvent, ThinkingItem, UseChatReturn } from '../types';
import { streamChat } from '../services';

/**
 * Custom hook for managing chat state and streaming.
 * Session management is handled automatically via secure httpOnly cookies.
 */
export function useChat(): UseChatReturn {
  // ======================
  // STATE, HOOKS & REFS
  // ======================
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionIdState] = useState<string | null>(null);
  const messageIdRef = useRef(0);
  // Track current text buffer for thinking items
  const textBufferRef = useRef<string>('');
  // Track thinking items array
  const thinkingItemsRef = useRef<ThinkingItem[]>([]);
  // Track abort controller for stopping streams
  const abortControllerRef = useRef<AbortController | null>(null);

  // ======================
  // MIDDLEWARES
  // ======================
  const updateMessage = useCallback(
    (messageId: string, updates: Partial<Message>) => {
      setMessages((prev) =>
        prev.map((msg) => (msg.id === messageId ? { ...msg, ...updates } : msg))
      );
    },
    []
  );

  const handleStreamEvent = useCallback(
    (event: ChatStreamEvent, messageId: string) => {
      if (event.type === 'session') {
        if (event.session_id) {
          setSessionIdState(event.session_id);
        }
        return;
      }

      switch (event.type) {
        case 'token':
          textBufferRef.current += event.content ?? '';
          const lastTextItem =
            thinkingItemsRef.current[thinkingItemsRef.current.length - 1];

          if (lastTextItem && lastTextItem.type === 'text') {
            lastTextItem.content = textBufferRef.current;
          } else {
            thinkingItemsRef.current.push({
              type: 'text',
              content: textBufferRef.current,
            });
          }

          updateMessage(messageId, {
            thinkingItems: [...thinkingItemsRef.current],
            thinkingExpanded: true,
          });
          break;

        case 'tool':
          thinkingItemsRef.current.push({
            type: 'tool',
            content: '',
            toolName: event.name ?? '',
            toolMessage: event.message ?? '',
            toolInput: event.input ?? undefined,
          });
          textBufferRef.current = '';

          updateMessage(messageId, {
            thinkingItems: [...thinkingItemsRef.current],
            thinkingExpanded: true,
          });
          break;

        case 'workflow':
          updateMessage(messageId, { workflow: event.steps ?? [] });
          break;

        case 'complete':
          updateMessage(messageId, {
            content: event.response ?? '',
            workflow: event.workflow ?? undefined,
            thinkingExpanded: false,
            isStreaming: false,
          });
          break;

        case 'error':
          updateMessage(messageId, {
            content: `Error: ${event.message ?? event.content ?? 'Unknown error'}`,
            isStreaming: false,
            isError: true,
          });
          break;
      }
    },
    [updateMessage]
  );

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isLoading) return;

      // Create new abort controller for this request
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      // Reset buffers for new message
      textBufferRef.current = '';
      thinkingItemsRef.current = [];

      // Add user message
      const userMessageId = `user-${++messageIdRef.current}`;
      const userMessage: Message = {
        id: userMessageId,
        role: 'user',
        content: text,
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      // Create assistant message placeholder
      const assistantMessageId = `assistant-${++messageIdRef.current}`;
      const assistantMessage: Message = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        thinkingItems: [],
        thinkingExpanded: true,
        isStreaming: true,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      try {
        for await (const event of streamChat({
          message: text,
          session_id: sessionId,
        }, abortController.signal)) {
          handleStreamEvent(event, assistantMessageId);
        }
      } catch (error) {
        // Don't show error if it was an abort
        if (error instanceof Error && error.name === 'AbortError') {
          updateMessage(assistantMessageId, {
            content: 'Generation stopped by user.',
            isStreaming: false,
          });
        } else {
          const errorMessage =
            error instanceof Error ? error.message : 'Unknown error';
          updateMessage(assistantMessageId, {
            content: `Error: ${errorMessage}`,
            isStreaming: false,
            isError: true,
          });
        }
      } finally {
        setIsLoading(false);
        abortControllerRef.current = null;
      }
    },
    [isLoading, sessionId, handleStreamEvent, updateMessage]
  );

  const clearChat = useCallback(() => {
    // Abort any ongoing stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setMessages([]);
    setIsLoading(false);
    // Reset session for new conversation
    setSessionIdState(null);
  }, []);

  const toggleThinking = useCallback((messageId: string) => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId
          ? { ...msg, thinkingExpanded: !msg.thinkingExpanded }
          : msg
      )
    );
  }, []);

  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
    }
  }, []);

  // ======================
  // RENDER FUNCTIONS
  // ======================

  return {
    messages,
    isLoading,
    sessionId,
    sendMessage,
    clearChat,
    toggleThinking,
    stopGeneration,
  };
}

