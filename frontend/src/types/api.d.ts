/**
 * API request/response types
 */

import type { WorkflowStep } from './common';

export interface ChatRequest {
  message: string;
  session_id?: string | null;
}

export interface ChatResponse {
  response: string;
  session_id: string;
}

export interface HealthResponse {
  status: string;
  agent_initialized: boolean;
}

export interface ChatStreamEvent {
  type: 'session' | 'token' | 'tool' | 'workflow' | 'complete' | 'error';
  session_id?: string;
  content?: string;
  name?: string;
  message?: string;
  input?: unknown;
  response?: string;
  steps?: WorkflowStep[];
  workflow?: WorkflowStep[]; // Workflow can be included in complete event
}
