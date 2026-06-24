"use client";

import Image from "next/image";
import type { Message } from "@/types/chat";
import { Markdown } from "./Markdown";
import { ToolCallCard } from "./ToolCallCard";

/**
 * AssistantBubble — SAGE's reply.
 *
 * Left-aligned, mascot avatar, WIDE reading column with minimal chrome
 * (no heavy card around the text — assistant prose is the content you
 * actually read, so it gets width and breathing room, not containment).
 *
 * Renders, in order:
 *   1. The markdown text (memoized — see Markdown.tsx).
 *   2. Any tool-call cards Claude made during this turn.
 *
 * The prose-invert wrapper lives HERE (not in Markdown.tsx) so typography
 * is owned in one place and Markdown stays reusable.
 */
interface AssistantBubbleProps {
  message: Message;
}

export function AssistantBubble({ message }: AssistantBubbleProps) {
  const isStreaming = message.status === "streaming";

  return (
    <div className="flex w-full gap-3">
      {/* Mascot avatar */}
      <div className="glass-strong mt-0.5 flex size-8 shrink-0 items-center justify-center overflow-hidden rounded-full">
        <Image
          src="/mascot.png"
          alt="SAGE"
          width={28}
          height={28}
          className="size-7 object-contain"
        />
      </div>

      {/* Content column */}
      <div className="min-w-0 flex-1">
        <div className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-transparent prose-pre:p-0">
          <Markdown content={message.content} />
          {isStreaming && (
            <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse rounded-sm bg-violet-400 align-middle" />
          )}
        </div>

        {/* Tool-call cards, if any */}
        {message.tool_calls.length > 0 && (
          <div className="mt-1">
            {message.tool_calls.map((tool) => (
              <ToolCallCard key={tool.id} tool={tool} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
