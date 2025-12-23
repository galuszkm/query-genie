/**
 * Session management helpers
 */

const SESSION_STORAGE_KEY = 'chat_session_id';

/**
 * Get or create a unique session ID for this browser tab
 */
export function getSessionId(): string {
  let sessionId = sessionStorage.getItem(SESSION_STORAGE_KEY);
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  }
  return sessionId;
}

/**
 * Store session ID in session storage
 */
export function setSessionId(sessionId: string): void {
  sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
}

/**
 * Generate a new session ID and store it
 */
export function createNewSessionId(): string {
  const newSessionId = crypto.randomUUID();
  sessionStorage.setItem(SESSION_STORAGE_KEY, newSessionId);
  return newSessionId;
}

/**
 * Clear all session data from session storage
 */
export function clearSessionStorage(): void {
  sessionStorage.removeItem(SESSION_STORAGE_KEY);
}
