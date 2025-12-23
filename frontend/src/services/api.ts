import type { ChatRequest, ChatStreamEvent } from '../types';

const API_BASE = '/ai/api';

/**
 * Stream chat response from the API using Server-Sent Events.
 * Session ID is sent in request body and tracked from SSE events.
 */
export async function* streamChat(
  request: ChatRequest,
  signal?: AbortSignal
): AsyncGenerator<ChatStreamEvent, void, unknown> {
  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal,
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('Response body is not readable');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  // Helper to parse and yield SSE data line
  const processDataLine = function* (data: string): Generator<ChatStreamEvent> {
    if (!data || data === 'keep-alive') return;
    
    try {
      yield JSON.parse(data) as ChatStreamEvent;
    } catch {
      const preview = data.length > 100 ? `${data.substring(0, 100)}...` : data;
      console.warn('Failed to parse SSE event (skipping):', preview);
    }
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          yield* processDataLine(line.slice(6).trim());
        }
      }
    }
    
    // Process remaining buffer
    if (buffer.trim().startsWith('data: ')) {
      yield* processDataLine(buffer.trim().slice(6).trim());
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * Check API health status
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Fetch question suggestions for welcome screen
 */
export async function fetchSuggestions(): Promise<string[]> {
  try {
    const response = await fetch(`${API_BASE}/suggestions`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch suggestions:', error);
    return [];
  }
}

/**
 * Fetch welcome screen configuration
 */
export async function fetchWelcomeConfig(): Promise<{
  title: string;
  subtitle: string;
  suggestions: string[];
}> {
  try {
    const response = await fetch(`${API_BASE}/welcome`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch welcome config:', error);
    return {
      title: 'Welcome!',
      subtitle: 'Try questions like:',
      suggestions: [],
    };
  }
}
