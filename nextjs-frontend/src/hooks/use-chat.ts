// src/hooks/use-chat.ts
//
// Convenience hook around the chat Zustand store. Gives components a clean
// view of the data they care about without each component having to write
// half a dozen `useChatStore(s => ...)` selector calls.
//
// Usage in a component:
//
//   const {
//     conversations,
//     currentConversation,
//     messages,
//     isStreaming,
//     error,
//     sendMessage,
//     startNewConversation,
//     setCurrentConversation,
//     clearError,
//   } = useChat();
//
// Why a separate hook layer instead of consuming the store directly?
//   - Components don't need to know they're touching Zustand. If we ever
//     swap Zustand for Redux/Context/whatever, only this file changes.
//   - Derived state (currentConversation, messages) gets computed in one
//     place rather than re-derived in every component.
//   - Easier to test components: mock useChat() instead of stubbing the store.

"use client";

import { useChatStore } from "@/stores/chat-store";
import type { Conversation, Message } from "@/types/chat";

export type UseChatReturn = {
  // ── Read state ──────────────────────────────────────────
  /** All conversations, newest-first. */
  conversations: Conversation[];
  /** The currently active conversation, or null if none. */
  currentConversation: Conversation | null;
  /** Messages in the current conversation, or [] if none. */
  messages: Message[];
  /** True if a stream is in flight. UI should disable input during this. */
  isStreaming: boolean;
  /** Last error from the stream layer, or null. */
  error: string | null;

  // ── Actions ─────────────────────────────────────────────
  /** Send a message in the current conversation. Auto-creates one if none active. */
  sendMessage: (text: string) => Promise<void>;
  /** Create a fresh empty conversation, set it as current. Returns its id. */
  startNewConversation: () => string;
  /** Switch the active conversation. */
  setCurrentConversation: (id: string) => void;
  /** Dismiss the current error banner. */
  clearError: () => void;
};

export function useChat(): UseChatReturn {
  // Subscribe to each slice individually so unrelated re-renders don't fire.
  // Zustand will only re-run this hook when one of these specific values
  // changes, so the per-selector subscription pattern is the right one.
  const conversations = useChatStore((s) => s.conversations);
  const currentId = useChatStore((s) => s.currentConversationId);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const error = useChatStore((s) => s.error);

  const sendMessage = useChatStore((s) => s.sendMessage);
  const startNewConversation = useChatStore((s) => s.startNewConversation);
  const setCurrentConversation = useChatStore((s) => s.setCurrentConversation);
  const clearError = useChatStore((s) => s.clearError);

  // Derived: find the active conversation in the list.
  const currentConversation =
    conversations.find((c) => c.id === currentId) ?? null;

  // Derived: messages of the active conversation. Defaults to [] so
  // components can always `.map()` without null-checks.
  const messages = currentConversation?.messages ?? [];

  return {
    conversations,
    currentConversation,
    messages,
    isStreaming,
    error,

    sendMessage,
    startNewConversation,
    setCurrentConversation,
    clearError,
  };
}