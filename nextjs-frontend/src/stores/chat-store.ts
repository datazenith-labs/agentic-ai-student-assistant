// src/stores/chat-store.ts
//
// Zustand store for chat state. Single source of truth for the UI.
//
// Architecture:
//   - One ChatStore instance lives for the lifetime of the app.
//   - Components subscribe to slices via the useChat() hook (next step).
//   - The store owns ALL conversation state — message list, streaming
//     status, current session, errors.
//   - When sendMessage() is called, it adds the user message optimistically,
//     creates an in-progress assistant message, then consumes chatStream()
//     and updates the assistant message's content as tokens arrive.
//
// Persistence:
//   - The store is NOT persisted to localStorage (decision A in 12.5b plan).
//   - Backend SQLite is the source of truth; we'd hydrate conversations
//     from a /api/conversations endpoint in 12.5c.
//
// Optimistic rendering:
//   - User messages appear immediately, BEFORE the backend acknowledges.
//   - If the stream errors, the assistant message gets status="error" but
//     the user message stays in place.

import { create } from "zustand";

import { chatStream } from "@/lib/chat-stream";
import type {
  ChatStreamEvent,
  Conversation,
  Message,
  ToolCall,
} from "@/types/chat";

// ---------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------

// User ID is hardcoded until auth lands in Step 13. Matches the seeded
// test user in the backend DB.
const TEST_USER_ID = "1670551a-ecef-449c-a63c-cce402570981";

// Simple browser-native ID generator. Good enough for client-side keying;
// the backend assigns canonical IDs for any persisted record.
function clientId(): string {
  return crypto.randomUUID();
}

function nowIso(): string {
  return new Date().toISOString();
}

// Derive a conversation title from the first user message. Truncated to
// keep the sidebar readable. The user can edit it later (Phase 12.7+).
function titleFromMessage(text: string): string {
  const trimmed = text.trim().replace(/\s+/g, " ");
  return trimmed.length > 40 ? `${trimmed.slice(0, 40)}…` : trimmed;
}

// ---------------------------------------------------------------------
// Store shape
// ---------------------------------------------------------------------

type ChatState = {
  // ── State ───────────────────────────────────────────────
  conversations: Conversation[];
  currentConversationId: string | null;
  isStreaming: boolean;
  // Last stream-level error. UI shows a dismissable banner.
  error: string | null;

  // ── Actions ─────────────────────────────────────────────
  startNewConversation: () => string;        // returns the new id
  setCurrentConversation: (id: string) => void;
  sendMessage: (text: string) => Promise<void>;
  clearError: () => void;
};

// ---------------------------------------------------------------------
// Store implementation
// ---------------------------------------------------------------------

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentConversationId: null,
  isStreaming: false,
  error: null,

  startNewConversation: () => {
    const id = clientId();
    const newConv: Conversation = {
      id,
      title: "New chat",
      created_at: nowIso(),
      messages: [],
    };

    set((state) => ({
      conversations: [newConv, ...state.conversations],
      currentConversationId: id,
      error: null,
    }));

    return id;
  },

  setCurrentConversation: (id) => {
    set({ currentConversationId: id, error: null });
  },

  sendMessage: async (text) => {
    if (!text.trim()) return;

    let conversationId = get().currentConversationId;

    // Lazy-init: if there's no current conversation, create one. This lets
    // the home page's chat input "just work" — user types, hits enter,
    // a conversation pops into existence.
    if (!conversationId) {
      conversationId = get().startNewConversation();
    }

    // Optimistic user message + an empty in-progress assistant message.
    // We'll patch the assistant message's content as tokens arrive.
    const userMsg: Message = {
      id: clientId(),
      role: "user",
      content: text,
      tool_calls: [],
      created_at: nowIso(),
      status: "done",
    };

    const assistantMsg: Message = {
      id: clientId(),
      role: "assistant",
      content: "",
      tool_calls: [],
      created_at: nowIso(),
      status: "streaming",
    };

    appendMessages(set, conversationId, [userMsg, assistantMsg]);
    set({ isStreaming: true, error: null });

    // Also update the conversation title if this is the first message.
    set((state) => ({
      conversations: state.conversations.map((c) =>
        c.id === conversationId && c.messages?.length === 2
          ? { ...c, title: titleFromMessage(text) }
          : c,
      ),
    }));

    try {
      for await (const event of chatStream({
        user_id: TEST_USER_ID,
        session_id: conversationId,
        message: text,
      })) {
        applyEvent(set, conversationId, assistantMsg.id, event);
      }
    } catch (err) {
      // Network / non-2xx / abort. Mark the assistant message as errored
      // and surface a top-level error banner.
      const message =
        err instanceof Error ? err.message : "Unknown stream error";

      set({ error: message });
      patchMessage(set, conversationId, assistantMsg.id, {
        status: "error",
      });
    } finally {
      set({ isStreaming: false });
    }
  },

  clearError: () => set({ error: null }),
}));

// ---------------------------------------------------------------------
// State-mutation helpers (kept outside the store factory for readability)
// ---------------------------------------------------------------------

type SetFn = (
  partial:
    | ChatState
    | Partial<ChatState>
    | ((state: ChatState) => ChatState | Partial<ChatState>),
) => void;

/** Append one or more messages to a conversation's messages array. */
function appendMessages(
  set: SetFn,
  conversationId: string,
  msgs: Message[],
): void {
  set((state) => ({
    conversations: state.conversations.map((c) =>
      c.id === conversationId
        ? { ...c, messages: [...(c.messages ?? []), ...msgs] }
        : c,
    ),
  }));
}

/** Patch a single message by id within a conversation. */
function patchMessage(
  set: SetFn,
  conversationId: string,
  messageId: string,
  patch: Partial<Message>,
): void {
  set((state) => ({
    conversations: state.conversations.map((c) =>
      c.id !== conversationId || c.messages === null
        ? c
        : {
            ...c,
            messages: c.messages.map((m) =>
              m.id === messageId ? { ...m, ...patch } : m,
            ),
          },
    ),
  }));
}

/** Append a tool call to a message (used on tool_start). */
function pushToolCall(
  set: SetFn,
  conversationId: string,
  messageId: string,
  call: ToolCall,
): void {
  set((state) => ({
    conversations: state.conversations.map((c) =>
      c.id !== conversationId || c.messages === null
        ? c
        : {
            ...c,
            messages: c.messages.map((m) =>
              m.id === messageId
                ? { ...m, tool_calls: [...m.tool_calls, call] }
                : m,
            ),
          },
    ),
  }));
}

/** Update an existing tool call's status (used on tool_end). */
function patchToolCall(
  set: SetFn,
  conversationId: string,
  messageId: string,
  toolCallId: string,
  patch: Partial<ToolCall>,
): void {
  set((state) => ({
    conversations: state.conversations.map((c) =>
      c.id !== conversationId || c.messages === null
        ? c
        : {
            ...c,
            messages: c.messages.map((m) =>
              m.id !== messageId
                ? m
                : {
                    ...m,
                    tool_calls: m.tool_calls.map((tc) =>
                      tc.id === toolCallId ? { ...tc, ...patch } : tc,
                    ),
                  },
            ),
          },
    ),
  }));
}

/**
 * Apply a single ChatStreamEvent to the assistant message in flight.
 * This is the meat of the streaming logic: every event from the backend
 * maps to a precise state mutation.
 */
function applyEvent(
  set: SetFn,
  conversationId: string,
  assistantMessageId: string,
  event: ChatStreamEvent,
): void {
  switch (event.type) {
    case "token":
      set((state) => ({
        conversations: state.conversations.map((c) =>
          c.id !== conversationId || c.messages === null
            ? c
            : {
                ...c,
                messages: c.messages.map((m) =>
                  m.id === assistantMessageId
                    ? { ...m, content: m.content + event.text }
                    : m,
                ),
              },
        ),
      }));
      break;

    case "tool_start":
      pushToolCall(set, conversationId, assistantMessageId, {
        id: event.id,
        name: event.name,
        input: event.input,
        status: "pending",
      });
      break;

    case "tool_end":
      patchToolCall(set, conversationId, assistantMessageId, event.id, {
        status: event.status,
      });
      break;

    case "done":
      patchMessage(set, conversationId, assistantMessageId, {
        status: "done",
      });
      break;

    case "error":
      set({ error: event.message });
      patchMessage(set, conversationId, assistantMessageId, {
        status: "error",
      });
      break;
  }
}