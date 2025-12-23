/**
 * Hook return types
 */

import type { Message } from './common';

export interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  sessionId: string | null;
  sendMessage: (text: string) => Promise<void>;
  clearChat: () => void;
  toggleThinking: (messageId: string) => void;
  stopGeneration: () => void;
}
