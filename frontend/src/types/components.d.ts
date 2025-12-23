/**
 * Component prop types
 */

import type { Message, WorkflowStep, ThinkingItem } from './common';

// ======================
// ChatInput
// ======================

export interface ChatInputProps {
  onSend: (message: string) => void;
  onStop: () => void;
  isLoading: boolean;
}

// ======================
// ChatMessage
// ======================

export interface ChatMessageProps {
  message: Message;
  onToggleThinking?: () => void;
}

// ======================
// Header
// ======================

export interface HeaderProps {
  onClearChat: () => void;
  sessionId: string | null;
}

// ======================
// WelcomeScreen
// ======================

export interface WelcomeScreenProps {
  onSuggestionClick: (text: string) => void;
}

// ======================
// WorkflowDialog
// ======================

export interface WorkflowDialogProps {
  steps: WorkflowStep[];
  visible: boolean;
  onHide: () => void;
}

// ======================
// ThinkingBox
// ======================

export interface ThinkingBoxProps {
  thinkingItems: ThinkingItem[];
  isStreaming: boolean;
  isExpanded: boolean;
  onToggle?: () => void;
}

// ======================
// ToolStep
// ======================

export interface ToolStepProps {
  step: WorkflowStep;
  index: number;
  isExpanded: boolean;
  onToggle: (index: number, isOpen: boolean) => void;
}

// ======================
// ReasoningStep
// ======================

export interface ReasoningStepProps {
  content?: string;
}
