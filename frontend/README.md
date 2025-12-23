# Frontend Dashboard

## Overview

The Frontend Dashboard is a modern React application that provides an interactive interface for QueryGenie's AI agent. Built with React 19 and TypeScript, it delivers real-time visualization of agent reasoning through Server-Sent Events (SSE), displaying streaming responses, tool executions, and complete workflow timelines.

## Key Features

- **Real-time SSE Streaming** — Live updates as the agent thinks, executes tools, and generates responses
- **Reasoning Visualization** — Expandable thinking boxes show agent's step-by-step reasoning process
- **Tool Execution Tracking** — Visual indicators for database queries, schema exploration, and other tool usage
- **Complete Workflow Timeline** — Detailed view of all reasoning steps and tool calls via dialog
- **Session Persistence** — Secure httpOnly cookie-based sessions prevent XSS attacks
- **Responsive Design** — Clean, modern UI with smooth animations and typewriter effects
- **Markdown Rendering** — Full GFM support with syntax highlighting for code blocks

## Architecture

```
            ┌─────────────────────────────────────────────────────────────────┐
            │                        FRONTEND APPLICATION                     │
            │                                                                 │
            │  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐   │
            │  │     App      │─────>│   useChat    │─────>│  API Client  │   │
            │  │  (Main UI)   │      │    (Hook)    │      │  (SSE Stream)│   │
            │  └──────────────┘      └──────────────┘      └──────────────┘   │
            │         │                      │                      │         │
            │         ▼                      ▼                      ▼         │
            │  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐   │
            │  │  Components  │      │    State     │      │   Helpers    │   │
            │  │              │      │  Management  │      │  (Session)   │   │
            │  └──────────────┘      └──────────────┘      └──────────────┘   │
            │         │                                                       │
            │         ▼                                                       │
            │  ┌────────────────┐                                             │
            │  │ ChatMessage    │                                             │
            │  │ ThinkingBox    │                                             │
            │  │ ToolBadge      │                                             │
            │  │ WorkflowDialog │                                             │
            │  └────────────────┘                                             │
            └─────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼ HTTP + SSE (Port 8080)
            ┌─────────────────────────────────────────────────────────────────┐
            │                         BACKEND API                             │
            │              POST /ai/api/chat/stream (SSE Response)            │
            └─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
frontend/
├── src/
│   ├── App.tsx                    # Main application component
│   ├── App.module.css            # Application-level styles
│   ├── main.tsx                  # Application entry point
│   ├── index.css                 # Global styles and CSS variables
│   │
│   ├── components/               # React components
│   │   ├── Header.tsx            # Application header with actions
│   │   ├── ChatMessage.tsx       # Individual message display
│   │   ├── ChatInput.tsx         # Message input with send button
│   │   ├── ThinkingBox.tsx       # Agent reasoning visualization
│   │   ├── ToolBadge.tsx         # Tool execution indicator
│   │   ├── ToolStep.tsx          # Individual tool step display
│   │   ├── ReasoningStep.tsx     # Reasoning text display
│   │   ├── TypingIndicator.tsx   # Loading animation
│   │   ├── WelcomeScreen.tsx     # Initial landing screen
│   │   ├── WorkflowDialog.tsx    # Complete workflow timeline
│   │   └── *.module.css          # Component-scoped styles
│   │
│   ├── hooks/                    # Custom React hooks
│   │   ├── useChat.ts            # Main chat logic and SSE handling
│   │   └── useTypewriter.ts      # Typewriter animation effect
│   │
│   ├── services/                 # API communication
│   │   └── api.ts                # SSE streaming client
│   │
│   ├── helpers/                  # Utility functions
│   │   ├── sessionHelpers.ts     # Session ID management
│   │   └── workflowFormatters.ts # Workflow data transformation
│   │
│   └── types/                    # TypeScript definitions
│       ├── api.d.ts              # API request/response types
│       ├── components.d.ts       # Component prop types
│       ├── hooks.d.ts            # Hook return types
│       └── common.d.ts           # Shared type definitions
│
├── public/                       # Static assets
├── vite.config.ts               # Vite configuration
├── tsconfig.json                # TypeScript configuration
├── package.json                 # Dependencies and scripts
└── README.md                    # This file
```

## Core Components

### App.tsx

Main application component that orchestrates the UI:
- Manages message list rendering
- Handles auto-scrolling behavior
- Routes between welcome screen and chat interface
- Integrates all child components

### useChat Hook

Central state management for chat functionality:
- **SSE Event Handling**: Processes streaming events (`token`, `tool`, `workflow`, `complete`, `error`)
- **Message Management**: Creates, updates, and tracks messages with unique IDs
- **Thinking Items**: Accumulates text buffers and tool events into structured thinking items
- **Abort Control**: Allows stopping in-progress generations

**Event Flow**:
```
SSE Event → useChat Handler → State Update → Component Re-render
```

### ChatMessage Component

Displays individual messages with:
- User/assistant role indicators
- Expandable thinking box showing reasoning process
- Tool execution badges with visual feedback
- Markdown rendering with GFM support and syntax highlighting
- Workflow dialog button for detailed timeline

### ThinkingBox Component

Expandable visualization of agent reasoning:
- Text content with typewriter effect
- Tool execution steps with name, input, and output
- Collapse/expand functionality
- Visual hierarchy with indentation

### WorkflowDialog Component

Modal dialog displaying complete workflow:
- Chronological list of all reasoning steps
- Tool executions with full input/output
- Formatted JSON display
- Copy-to-clipboard functionality

## API Integration

### SSE Event Types

The frontend handles the following Server-Sent Event types from the backend:

```typescript
// Session initialization
{ type: "session", session_id: "uuid" }

// Streaming text tokens
{ type: "token", content: "Hello" }

// Tool execution start
{ type: "tool", name: "query_database", message: "🔎 Querying...", input: {...} }

// Workflow updates (periodic)
{ type: "workflow", steps: [{type: "reasoning", content: "..."}, ...] }

// Completion with full response
{ type: "complete", response: "...", workflow: [...], session_id: "uuid" }

// Error handling
{ type: "error", message: "...", session_id: "uuid" }
```

### API Client

The `streamChat` function uses async generators for efficient SSE streaming:

```typescript
for await (const event of streamChat(request, signal)) {
  // Process event types
  switch (event.type) {
    case 'session': handleSession(event); break;
    case 'token': handleToken(event); break;
    case 'tool': handleTool(event); break;
    // ...
  }
}
```

Supports abort signals for cancellation and handles reconnection logic.

## Development

### Prerequisites

- **Node.js 22+** — JavaScript runtime ([Install Node](https://nodejs.org/))
- **npm** — Package manager (included with Node.js)

### Local Development

```bash
# Install dependencies
npm install

# Start dev server (http://localhost:5173)
npm run dev

# Type checking
npm run build

# Lint code
npm run lint

# Preview production build
npm run preview
```

### Environment Variables

The frontend uses Vite's environment variable system:

```env
# Base URL for API requests (default: /ai/api)
VITE_API_BASE=/ai/api
```

For production, the frontend is typically built and served by the backend:

```bash
# Build for backend static serving
npm run build:backend
```

This outputs to `../backend/src/static` where the FastAPI server serves it.

---

## Building for Production

### Standard Build

```bash
npm run build
```

Output: `dist/` directory with optimized assets:
- **JavaScript**: Minified and code-split
- **CSS**: Extracted and minified
- **Assets**: Organized by type (fonts, images)
- **Vendor Chunks**: React libraries separated for caching

### Backend Integration Build

```bash
npm run build:backend
```

Builds directly into backend's static directory for single-server deployment.


## Technology Stack

| Category | Technologies |
|----------|-------------|
| **Framework** | React 19.2 |
| **Language** | TypeScript 5.9+ |
| **Build Tool** | Vite 7 |
| **UI Library** | PrimeReact 10.9 (icons only) |
| **Markdown** | react-markdown, remark-gfm, rehype-raw |
| **Syntax Highlighting** | react-syntax-highlighter |
| **State Management** | React hooks (useState, useCallback, useRef) |
| **HTTP Client** | Native Fetch API with SSE |
| **Code Quality** | ESLint, TypeScript Compiler |


## Styling Architecture

### CSS Modules

Component-scoped styles prevent naming conflicts:

```typescript
import styles from './ChatMessage.module.css';
<div className={styles.message}>...</div>
```

### CSS Variables

Global design tokens in `index.css`:

```css
:root {
  --primary-color: #646cff;
  --background: #1a1a1a;
  --surface: #242424;
  --text-primary: rgba(255, 255, 255, 0.87);
  --border-radius: 8px;
  /* ... */
}
```

### Responsive Design

Mobile-first approach with breakpoints:
- **Mobile**: Base styles
- **Tablet**: `@media (min-width: 768px)`
- **Desktop**: `@media (min-width: 1024px)`


## Performance Optimizations

### Code Splitting

- **Vendor Chunks**: React, Markdown, and UI libraries separated
- **Dynamic Imports**: Large components lazy-loaded when needed
- **Asset Optimization**: Images and fonts cached separately

### React Optimizations

- **useCallback**: Memoize event handlers to prevent re-renders
- **useRef**: Store mutable values without triggering re-renders
- **Virtual Scrolling**: Auto-scroll only when new messages arrive

### SSE Streaming

- **Incremental Rendering**: UI updates as tokens arrive, no waiting for complete response
- **Buffer Management**: Efficient text accumulation without memory leaks
- **Abort Control**: Cancel in-progress requests to prevent resource waste


## Extending the Frontend

### Adding New Components

```typescript
// src/components/NewComponent.tsx
import type { ReactElement } from 'react';
import styles from './NewComponent.module.css';

interface NewComponentProps {
  data: string;
}

export function NewComponent({ data }: NewComponentProps): ReactElement {
  return <div className={styles.container}>{data}</div>;
}

// Export in src/components/index.ts
export { NewComponent } from './NewComponent';
```

### Adding Custom Hooks

```typescript
// src/hooks/useCustomHook.ts
import { useState, useEffect } from 'react';

export function useCustomHook(dependency: string) {
  const [value, setValue] = useState<string>('');

  useEffect(() => {
    // Custom logic
  }, [dependency]);

  return { value };
}

// Export in src/hooks/index.ts
export { useCustomHook } from './useCustomHook';
```

### Adding New SSE Event Types

1. **Update types** in `src/types/api.d.ts`:
```typescript
export interface ChatStreamEvent {
  type: 'session' | 'token' | 'tool' | 'workflow' | 'complete' | 'error' | 'new_event';
  // Add new fields
  new_field?: string;
}
```

2. **Handle in useChat** hook:
```typescript
const handleNewEvent = useCallback((event: ChatStreamEvent, messageId: string) => {
  // Process new event type
}, []);
```

3. **Update component** to display new data.
