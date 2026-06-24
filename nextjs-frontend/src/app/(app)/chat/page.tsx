// src/app/(app)/chat/page.tsx
//
// Phase 12.5b — Step 4 verification scaffold.
// Same behavior as Step 3, but uses the useChat() convenience hook
// instead of pulling slices directly from the Zustand store. Real chat
// UI lands in 12.5c-e.

"use client";

import { Button } from "@/components/ui/button";
import { useChat } from "@/hooks/use-chat";

export default function ChatPage() {
  const {
    conversations,
    currentConversation,
    messages,
    isStreaming,
    error,
    sendMessage,
    startNewConversation,
    clearError,
  } = useChat();

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Chat (debug scaffold)</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Phase 12.5b Step 4 — using useChat() hook. Real UI in 12.5c-e.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button onClick={() => startNewConversation()}>New conversation</Button>
        <Button
          onClick={() => sendMessage("Say hi in one short sentence.")}
          disabled={isStreaming}
        >
          {isStreaming ? "Streaming..." : "Send: Say hi"}
        </Button>
        <Button
          variant="secondary"
          onClick={() => sendMessage("What are my upcoming exams?")}
          disabled={isStreaming}
        >
          Send: What exams?
        </Button>
      </div>

      {error && (
        <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950/40 dark:text-red-400">
          <div className="flex items-start justify-between gap-3">
            <span><strong>Error:</strong> {error}</span>
            <button onClick={clearError} className="underline shrink-0">Dismiss</button>
          </div>
        </div>
      )}

      <div className="text-sm space-y-1">
        <div>
          <strong>Conversations:</strong> {conversations.length}
        </div>
        <div>
          <strong>Current:</strong>{" "}
          <code className="text-xs">
            {currentConversation?.title ?? "(none)"}
          </code>
        </div>
      </div>

      {currentConversation && (
        <div className="space-y-3 border-t pt-4">
          <div className="text-sm font-semibold">
            {currentConversation.title} · {messages.length} messages
          </div>
          {messages.map((m) => (
            <div
              key={m.id}
              className="rounded-md border border-border p-3 space-y-2"
            >
              <div className="flex items-center gap-2 text-xs">
                <span className="font-semibold uppercase">{m.role}</span>
                <span className="text-muted-foreground">{m.status}</span>
              </div>
              <div className="text-sm whitespace-pre-wrap">{m.content}</div>
              {m.tool_calls.length > 0 && (
                <ul className="space-y-1 text-xs font-mono">
                  {m.tool_calls.map((tc) => (
                    <li
                      key={tc.id}
                      className="rounded bg-muted/40 px-2 py-1 border border-border"
                    >
                      🔧 <span className="text-violet-600 dark:text-violet-400">{tc.name}</span>{" "}
                      <span className="text-muted-foreground">[{tc.status}]</span>
                      {" — "}
                      {JSON.stringify(tc.input)}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}