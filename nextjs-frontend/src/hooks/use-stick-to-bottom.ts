"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * useStickToBottom — smart auto-scroll for a streaming chat list.
 *
 * The classic chat-UI bug is "always scroll to bottom", which fights a user
 * who scrolls up mid-stream to re-read. This hook instead:
 *
 *   - Auto-scrolls to bottom ONLY when the user is already near the bottom
 *     (within `threshold` px). If they've scrolled up, it leaves them alone.
 *   - Exposes `showJumpButton` so the UI can offer a "jump to latest" pill
 *     when the user has scrolled away while content is still arriving.
 *   - Exposes `scrollToBottom()` for the pill's onClick.
 *
 * Usage:
 *   const { scrollRef, bottomRef, showJumpButton, scrollToBottom } =
 *     useStickToBottom([messages]);
 *   <div ref={scrollRef}>...messages...<div ref={bottomRef} /></div>
 *
 * Pass the deps that change as content streams (e.g. the messages array, or
 * a string of all content) so the effect re-runs on each token.
 */
export function useStickToBottom(deps: unknown[], threshold = 100) {
  // The scrollable container.
  const scrollRef = useRef<HTMLDivElement>(null);
  // A zero-height sentinel at the very bottom of the list.
  const bottomRef = useRef<HTMLDivElement>(null);
  // Whether the user is currently near the bottom. Drives auto-scroll.
  const [isNearBottom, setIsNearBottom] = useState(true);

  // Measure distance from bottom on every scroll.
  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
    setIsNearBottom(distance <= threshold);
  }, [threshold]);

  // Imperative scroll to bottom (used by the pill and by auto-scroll).
  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    bottomRef.current?.scrollIntoView({ behavior });
  }, []);

  // On new content: if the user is near the bottom, follow it. If they've
  // scrolled away, do nothing (the pill will appear instead).
  useEffect(() => {
    if (isNearBottom) {
      scrollToBottom("smooth");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  // Show the jump pill only when the user has scrolled away from the bottom.
  const showJumpButton = !isNearBottom;

  return {
    scrollRef,
    bottomRef,
    showJumpButton,
    scrollToBottom,
    handleScroll,
  };
}
