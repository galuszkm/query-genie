/**
 * Common shared types across the application
 */

export interface ThinkingItem {
  type: 'text' | 'tool';
  content: string;
  toolName?: string;
  toolMessage?: string;
  toolInput?: unknown;
}

export interface WorkflowStep {
  step: number;
  type: 'reasoning' | 'tool';
  content?: string;
  name?: string;
  message?: string;
  input?: unknown;
  output?: unknown;
  status?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  thinkingItems?: ThinkingItem[];
  thinkingExpanded?: boolean;
  workflow?: WorkflowStep[];
  isStreaming?: boolean;
  isError?: boolean;
}
