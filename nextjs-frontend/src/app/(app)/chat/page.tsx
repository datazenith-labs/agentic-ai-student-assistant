"use client";

import { useChat } from "@/hooks/use-chat";
import { MessageList } from "@/components/chat/MessageList";
import { ChatInput } from "@/components/chat/ChatInput";

/**
 * /chat — the main chat view. Replaces the 12.5b debug scaffold.
 *
 * Layout: a full-height column. MessageList fills the available space and
 * scrolls; ChatInput is docked at the bottom. Both sit over the aurora
 * background so the glass surfaces read as premium floating panels.
 *
 * When there are no messages yet, we show an empty state instead of an
 * empty scroll area (suggested prompts come in Step 5; for now a simple
 * centered welcome).
 */
export default function ChatPage() {
  const { messages, isStreaming, error, sendMessage, clearError } = useChat();

  const hasMessages = messages.length > 0;

  return (
    <div className="flex h-full flex-col">
      {/* Error banner */}
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

      {hasMessages ? (
        <MessageList messages={messages} />
      ) : (
        <div className="aurora-bg flex flex-1 flex-col items-center justify-center px-4 text-center">
          <h1 className="bg-gradient-to-r from-white to-violet-300 bg-clip-text text-3xl font-semibold text-transparent">
            How can I help you today?
          </h1>
          <p className="mt-2 text-sm text-white/50">
            Ask about your courses, exams, deadlines, or upload notes to study from.
          </p>
        </div>
      )}

      <ChatInput onSend={sendMessage} disabled={isStreaming} />
    </div>
  );
}
