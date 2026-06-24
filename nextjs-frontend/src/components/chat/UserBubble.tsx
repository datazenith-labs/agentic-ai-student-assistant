"use client";

/**
 * UserBubble — the student's own message.
 *
 * Right-aligned, violet-tinted glass, capped at ~75% width so long
 * messages stay contained and visually "owned" by the user. No avatar
 * (asymmetric on purpose: assistant gets the mascot, user does not).
 * Plain text only — users don't write markdown, and rendering it would
 * be a minor injection surface for no benefit.
 */
interface UserBubbleProps {
  content: string;
}

export function UserBubble({ content }: UserBubbleProps) {
  return (
    <div className="flex w-full justify-end">
      <div className="glass-violet max-w-[75%] rounded-2xl rounded-br-md px-4 py-2.5 text-sm leading-relaxed text-white/95 whitespace-pre-wrap">
        {content}
      </div>
    </div>
  );
}
