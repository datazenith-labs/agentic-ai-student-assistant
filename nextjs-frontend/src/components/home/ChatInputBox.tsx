// src/components/home/ChatInputBox.tsx
//
// The hero chat input on the dashboard. Larger than a normal input — it's
// the focal call-to-action below the headline. Layout from the mockup:
//
//   ┌──────────────────────────────────────────────────────┐
//   │ Ask SAGE anything...                                  │  <- textarea
//   │                                                       │
//   │  [📎 Attach] [🌐 Web Search] [🗂 Use RAG]      [➤]    │  <- toolbar
//   └──────────────────────────────────────────────────────┘
//
// The toggles (Attach / Web Search / Use RAG) are stateful — they change
// how the message will be processed when sent. Tracked here in local state;
// in 12.5 we'll lift this into a chat store (Zustand).
//
// Send button: violet, prominent. Disabled when the textarea is empty.
//
// On enter, message logs to console for now. Real send in 12.5.

"use client";

import { useState } from "react";
import {
  Paperclip,
  Globe,
  Database,
  Send,
  type LucideIcon,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type ToggleKey = "attach" | "search" | "rag";

type ToolToggle = {
  key: ToggleKey;
  label: string;
  icon: LucideIcon;
};

const TOOL_TOGGLES: ToolToggle[] = [
  { key: "attach", label: "Attach File", icon: Paperclip },
  { key: "search", label: "Web Search", icon: Globe },
  { key: "rag",    label: "Use RAG",    icon: Database },
];

export function ChatInputBox() {
  const [message, setMessage] = useState("");
  const [toggles, setToggles] = useState<Record<ToggleKey, boolean>>({
    attach: false,
    search: false,
    rag: false,
  });

  const toggle = (key: ToggleKey) =>
    setToggles((prev) => ({ ...prev, [key]: !prev[key] }));

  const handleSend = () => {
    if (!message.trim()) return;
    // TODO (Phase 12.5): send to backend, navigate to /chat with conversation id.
    console.log("[Chat send]", { message, toggles });
    setMessage("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter sends, Shift+Enter inserts newline (standard chat UX).
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="rounded-2xl border border-border bg-background shadow-sm hover:shadow-md transition-shadow">
      {/* Textarea row */}
      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask SAGE anything..."
        aria-label="Ask SAGE anything"
        rows={2}
        className="w-full resize-none bg-transparent px-5 pt-4 pb-2 text-sm focus:outline-none placeholder:text-muted-foreground"
      />

      {/* Toolbar row */}
      <div className="flex items-center justify-between gap-2 px-3 pb-3">
        <div className="flex items-center gap-1.5 flex-wrap">
          {TOOL_TOGGLES.map((t) => {
            const Icon = t.icon;
            const active = toggles[t.key];
            return (
              <button
                key={t.key}
                type="button"
                onClick={() => toggle(t.key)}
                aria-pressed={active}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors border",
                  active
                    ? "bg-violet-100 dark:bg-violet-950/40 text-violet-700 dark:text-violet-300 border-violet-300 dark:border-violet-800"
                    : "bg-transparent text-muted-foreground border-border hover:bg-muted hover:text-foreground"
                )}
              >
                <Icon className="size-3.5" />
                {t.label}
              </button>
            );
          })}
        </div>

        <Button
          type="button"
          onClick={handleSend}
          disabled={!message.trim()}
          size="icon"
          className="size-9 bg-violet-600 hover:bg-violet-500 text-white disabled:bg-muted disabled:text-muted-foreground"
          aria-label="Send message"
        >
          <Send className="size-4" />
        </Button>
      </div>
    </div>
  );
}