"use client";

import { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownProps {
  content: string;
}

/**
 * Memoized markdown renderer for assistant messages.
 *
 * Memoization is critical: during streaming the parent re-renders on every
 * token, but react-markdown re-parses the entire string on each render. Without
 * memo, a long assistant message re-parses hundreds of times mid-stream and
 * janks the UI. memo() short-circuits re-render unless `content` actually
 * changed, so we only re-parse when new text has genuinely arrived.
 *
 * Styling note: we lean on Tailwind's prose utilities applied by the PARENT
 * (AssistantBubble in Step 2), so this component stays purely structural.
 */
function MarkdownComponent({ content }: MarkdownProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        a: ({ ...props }) => (
          <a
            {...props}
            target="_blank"
            rel="noopener noreferrer"
            className="text-violet-400 underline underline-offset-2 hover:text-violet-300"
          />
        ),
        code: ({ className, children, ...props }) => {
          const isBlock = className?.includes("language-");
          if (isBlock) {
            return (
              <code
                className={`${className ?? ""} block overflow-x-auto rounded-lg bg-black/40 p-3 text-sm`}
                {...props}
              >
                {children}
              </code>
            );
          }
          return (
            <code
              className="rounded bg-white/10 px-1.5 py-0.5 text-[0.85em]"
              {...props}
            >
              {children}
            </code>
          );
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

export const Markdown = memo(
  MarkdownComponent,
  (prev, next) => prev.content === next.content,
);
