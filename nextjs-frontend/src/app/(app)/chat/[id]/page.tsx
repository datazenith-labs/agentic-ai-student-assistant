"use client";

import { use, useEffect } from "react";
import { useChat } from "@/hooks/use-chat";
import { MessageList } from "@/components/chat/MessageList";
import { ChatInput } from "@/components/chat/ChatInput";

/**
 * /chat/[id] — a specific conversation, addressable by URL.
 *
 * Reads the conversation id from the route params and tells the store to
 * make it active. The store is the source of truth; this page is just a
 * thin URL-to-store binding plus the same MessageList + ChatInput as /chat.
 *
 * Note: in Next 15+, params is a Promise and must be unwrapped with use().
 */
interface ChatIdPageProps {
  params: Promise<{ id: string }>;
}

export default function ChatIdPage({ params }: ChatIdPageProps) {
  const { id } = use(params);
  const {
    messages,
    isStreaming,
    error,
    sendMessage,
    clearError,
    setCurrentConversation,
    currentConversation,
  } = useChat();

  // Bind the URL's conversation id into the store as the active conversation.
  // Runs whenever the id in the URL changes (e.g. clicking a different chat).
  useEffect(() => {
    setCurrentConversation(id);
  }, [id, setCurrentConversation]);

  // If the id in the URL doesn't match any known conversation (e.g. a stale
  // bookmark, or a hard refresh that wiped the in-memory store), show a
  // gentle empty state rather than a blank screen. Real hydration from the
  // backend lands in a later phase.
  const notFound = currentConversation === null;

  return (
    <div className="flex h-full flex-col">
      {error && (
        <div className="aurora-bg px-4 pt-3">
          <div className="mx-auto flex max-w-3xl items-center justify-between gap-3 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-200">
            <span>{error}</span>
            <button
              type="button"
              onClick={clearError}
              className="text-red-300/70 hover:text-red-200"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {notFound ? (
        <div className="aurora-bg flex flex-1 flex-col items-center justify-center px-4 text-center">
          <p className="text-sm text-white/50">
            This conversation isn&apos;t loaded. Start a new chat or pick one
            from the sidebar.
          </p>
        </div>
      ) : (
        <MessageList messages={messages} />
      )}

      <ChatInput onSend={sendMessage} disabled={isStreaming} />
    </div>
  );
}
