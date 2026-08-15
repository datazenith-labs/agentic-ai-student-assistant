// src/types/chat.ts
//
// TypeScript types for the SAGE chat API.
//
// Mirrors the Pydantic models in backend/schemas/chat.py. When the Python
// schemas change, update this file too. They're not auto-generated (yet) —
// we deliberately skipped openapi-typescript codegen in Phase 12.1 because
// the surface area is small enough to hand-maintain.
//
// All SSE event types share a `type` discriminator. Use it to narrow:
//
//   if (event.type === "token") {
//     // event.text is now typed
//   }

// ---------------------------------------------------------------------
// Request (matches Pydantic's ChatRequest)
// ---------------------------------------------------------------------

export type ChatRequest = {
  session_id: string;
  message: string;
  // Optional ChromaDB collection name for RAG. Null/undefined → no RAG
  // routing; Claude is told no documents are loaded.
  collection_name?: string | null;
};

// ---------------------------------------------------------------------
// SSE events (match Pydantic's *Event classes)
// ---------------------------------------------------------------------

// One incremental chunk of Claude's text. Many per turn.
export type TokenEvent = {
  type: "token";
  text: string;
};

// Claude is about to call an MCP tool. The `id` matches the corresponding
// tool_end event so the UI can pair start+end into a single tool card.
export type ToolStartEvent = {
  type: "tool_start";
  id: string;        // Anthropic tool_use_id
  name: string;      // e.g. "list_upcoming_deadlines"
  input: Record<string, unknown>;
};

// The MCP tool returned. Claude resumes streaming after this.
export type ToolEndEvent = {
  type: "tool_end";
  id: string;        // Matches the prior tool_start.id
  status: "ok" | "error";
};

// Final event of a successful stream. Exactly one per turn.
export type DoneEvent = {
  type: "done";
  iterations: number;
  tools_used: string[];
};

// Final event of a failed stream. Exactly one per turn (instead of done).
export type ErrorEvent = {
  type: "error";
  message: string;
};

// Discriminated union of every possible event from /chat/stream.
// Use in switch statements and let TypeScript narrow:
//
//   switch (event.type) {
//     case "token":      handleToken(event.text); break;
//     case "tool_start": showToolCard(event); break;
//     case "tool_end":   updateToolCard(event); break;
//     case "done":       finishStream(event); break;
//     case "error":      showError(event.message); break;
//   }
export type ChatStreamEvent =
  | TokenEvent
  | ToolStartEvent
  | ToolEndEvent
  | DoneEvent
  | ErrorEvent;

// ---------------------------------------------------------------------
// UI-facing types (NOT part of the wire format)
// ---------------------------------------------------------------------
//
// These describe how the frontend stores conversation state. They're
// shaped for rendering, not for serialization.

// One tool call that Claude made during a turn. The UI renders these
// as collapsible cards inline with the assistant message.
export type ToolCall = {
  id: string;
  name: string;
  input: Record<string, unknown>;
  // `null` while pending (between tool_start and tool_end).
  status: "pending" | "ok" | "error";
};

// One message in a conversation. Either from the user or from SAGE.
export type Message = {
  // Stable client-side ID for keying in React. Backend has its own ID
  // which we may also store later, but for now this is local-only.
  id: string;
  role: "user" | "assistant";
  // Plain text content. For assistant messages this grows as tokens arrive.
  content: string;
  // Tool calls Claude made while producing this assistant message.
  // Empty for user messages and for assistant messages that didn't use tools.
  tool_calls: ToolCall[];
  // ISO timestamp for ordering and display.
  created_at: string;
  // Streaming state. Only meaningful for assistant messages.
  // - "streaming": tokens still arriving
  // - "done": stream finished normally
  // - "error": stream failed
  status: "streaming" | "done" | "error";
};

// A conversation thread. Maps to the backend's Session/Message tables,
// though we don't load all messages on initial render — see use-chat.ts.
export type Conversation = {
  id: string;          // session_id
  title: string;       // First user message, truncated. Editable later.
  created_at: string;
  // We may or may not have the messages loaded for a given conversation;
  // null means "not loaded yet". Empty array means "loaded, no messages".
  messages: Message[] | null;
};
