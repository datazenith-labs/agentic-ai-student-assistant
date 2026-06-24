"use client";

import { ArrowDown } from "lucide-react";
import type { Message } from "@/types/chat";
import { UserBubble } from "./UserBubble";
import { AssistantBubble } from "./AssistantBubble";
import { useStickToBottom } from "@/hooks/use-stick-to-bottom";

/**
 * MessageList — the scrolling conversation view.
 *
 * Responsibilities:
 *   - Render the aurora-glow background (the colorful field the glass blurs).
 *   - Map messages to UserBubble / AssistantBubble.
 *   - Smart auto-scroll via useStickToBottom.
 *   - Floating "jump to latest" pill when the user has scrolled away.
 *
 * Purely presentational: it receives `messages` and renders them. Store
 * wiring (sendMessage, etc.) happens in the page that mounts this (Step 4).
 */
interface MessageListProps {
  messages: Message[];
}

export function MessageList({ messages }: MessageListProps) {
  // Re-run auto-scroll whenever message count OR the last message's content
  // length changes (i.e. on every streamed token).
  const lastContentLen = messages[messages.length - 1]?.content.length ?? 0;
  const { scrollRef, bottomRef, showJumpButton, scrollToBottom, handleScroll } =
    useStickToBottom([messages.length, lastContentLen]);

  return (
    <div className="relative flex-1 overflow-hidden">
      {/* Scrollable region with the aurora glow behind everything */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="aurora-bg h-full overflow-y-auto"
      >
        <div className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-8">
          {messages.map((message) =>
            message.role === "user" ? (
              <UserBubble key={message.id} content={message.content} />
            ) : (
              <AssistantBubble key={message.id} message={message} />
            ),
          )}
          {/* Bottom sentinel for scrollIntoView */}
          <div ref={bottomRef} className="h-px" />
        </div>
      </div>

      {/* Floating jump-to-latest pill */}
      {showJumpButton && (
        <button
          type="button"
          onClick={() => scrollToBottom("smooth")}
          className="glass-strong absolute bottom-4 left-1/2 flex -translate-x-1/2 items-center gap-1.5 rounded-full px-4 py-2 text-xs font-medium text-white/90 transition hover:text-white"
        >
          <ArrowDown className="size-3.5" />
          Jump to latest
        </button>
      )}
    </div>
  );
}
