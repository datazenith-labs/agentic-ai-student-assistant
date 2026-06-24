"use client";

import { useRef, useState, type KeyboardEvent } from "react";
import { ArrowUp } from "lucide-react";

/**
 * ChatInput — the persistent message composer docked at the bottom of the
 * chat view.
 *
 * Behavior:
 *   - Multi-line textarea that auto-grows up to a max height.
 *   - Enter sends; Shift+Enter inserts a newline.
 *   - Disabled while a stream is in flight (prevents overlapping sends).
 *   - Glass-strong dock so it reads as a premium floating surface over
 *     the aurora background.
 *
 * Purely presentational: it calls `onSend(text)` and clears itself. The
 * parent owns what "send" actually does (store wiring).
 */
interface ChatInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = "Message SAGE…",
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const submit = () => {
    const text = value.trim();
    if (!text || disabled) return;
    onSend(text);
    setValue("");
    // Reset height after clearing.
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  // Auto-grow the textarea as the user types, capped at ~200px.
  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  };

  return (
    <div className="aurora-bg px-4 pb-6 pt-2">
      <div className="glass-strong mx-auto flex max-w-3xl items-end gap-2 rounded-2xl px-3 py-2.5">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={placeholder}
          rows={1}
          disabled={disabled}
          className="max-h-[200px] flex-1 resize-none bg-transparent py-1.5 text-sm text-white/95 placeholder:text-white/40 focus:outline-none disabled:opacity-50"
        />
        <button
          type="button"
          onClick={submit}
          disabled={disabled || !value.trim()}
          className="flex size-8 shrink-0 items-center justify-center rounded-full bg-violet-500 text-white transition hover:bg-violet-400 disabled:cursor-not-allowed disabled:opacity-40"
          aria-label="Send message"
        >
          <ArrowUp className="size-4" />
        </button>
      </div>
    </div>
  );
}
