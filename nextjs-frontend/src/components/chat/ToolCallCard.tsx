"use client";

import { useState } from "react";
import { ChevronRight, Check, Loader2, AlertCircle } from "lucide-react";
import type { ToolCall } from "@/types/chat";

/**
 * ToolCallCard — one MCP tool invocation, shown inline in the assistant turn.
 *
 * This is the most important demo detail: it makes SAGE's agentic behavior
 * VISIBLE. Collapsed by default (just name + status), expandable to reveal
 * the input args. The status dot animates pending -> ok/error as the
 * tool_start/tool_end event pair arrives.
 *
 * Glass styling so it reads as a distinct "the agent did something" surface
 * floating within the assistant's prose.
 */
interface ToolCallCardProps {
  tool: ToolCall;
}

export function ToolCallCard({ tool }: ToolCallCardProps) {
  const [open, setOpen] = useState(false);

  const statusIcon = {
    pending: <Loader2 className="size-3.5 animate-spin text-violet-300" />,
    ok: <Check className="size-3.5 text-emerald-400" />,
    error: <AlertCircle className="size-3.5 text-red-400" />,
  }[tool.status];

  const statusLabel = {
    pending: "Running",
    ok: "Done",
    error: "Failed",
  }[tool.status];

  const hasInput = Object.keys(tool.input).length > 0;

  return (
    <div className="glass my-2 max-w-[85%] overflow-hidden rounded-xl text-xs">
      <button
        type="button"
        onClick={() => hasInput && setOpen((v) => !v)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left"
      >
        {hasInput ? (
          <ChevronRight
            className={`size-3.5 shrink-0 text-white/40 transition-transform ${
              open ? "rotate-90" : ""
            }`}
          />
        ) : (
          <span className="size-3.5 shrink-0" />
        )}
        <span className="font-mono text-white/80">{tool.name}</span>
        <span className="ml-auto flex items-center gap-1.5 text-white/50">
          {statusIcon}
          <span>{statusLabel}</span>
        </span>
      </button>

      {open && hasInput && (
        <div className="border-t border-white/10 px-3 py-2">
          <pre className="overflow-x-auto text-[0.7rem] leading-relaxed text-white/60">
            {JSON.stringify(tool.input, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
