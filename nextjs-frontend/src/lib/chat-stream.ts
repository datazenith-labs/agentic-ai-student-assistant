// src/lib/chat-stream.ts
//
// SSE consumer for the SAGE backend's POST /api/v1/chat/stream endpoint.
//
// Returns an async generator that yields one ChatStreamEvent per parsed
// SSE message. Caller drives consumption with `for await`:
//
//   for await (const event of chatStream(req)) {
//     // event is typed: token | tool_start | tool_end | done | error
//   }
//
// Why an async generator and not EventSource?
//   - EventSource only supports GET requests. We need POST (with a JSON body).
//   - EventSource handles parsing, but we want control over errors and the
//     ability to abort cleanly.
//   - fetch() + ReadableStream gives us everything we need without a library.
//
// Wire format: see the backend's _format_sse() helper. Each event is:
//
//     data: {"type": "token", "text": "..."}\n\n
//
// Two newlines separate events. We split on that.

import type { ChatRequest, ChatStreamEvent } from "@/types/chat";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

/**
 * Stream a chat reply from SAGE. Yields events as they arrive.
 *
 * Throws on:
 *  - Network failure (fetch rejects)
 *  - Non-2xx response (we don't bother to read the body; just throw)
 *  - Malformed SSE wire format (shouldn't happen with our backend)
 *
 * Does NOT throw on `error` events emitted by the backend — those are
 * yielded normally so the UI can handle them as part of the stream.
 *
 * @param req       ChatRequest body
 * @param signal    Optional AbortSignal for cancellation (e.g. user navigates away)
 */
export async function* chatStream(
  req: ChatRequest,
  signal?: AbortSignal,
): AsyncGenerator<ChatStreamEvent, void, unknown> {
  const url = `${API_BASE}/api/v1/chat/stream`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(req),
    signal,
  });

  if (!response.ok) {
    throw new Error(
      `Chat stream failed: ${response.status} ${response.statusText}`,
    );
  }
  if (!response.body) {
    throw new Error("Chat stream response has no body");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");

  // Buffer holds bytes we've decoded but haven't yet split into full events.
  // Events arrive as `data: {...}\n\n` so we split on the blank line.
  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();

      if (done) {
        // Stream closed by server. Any trailing buffer that doesn't end in
        // a blank line is incomplete and ignored — should not happen given
        // our backend's format, but defensive code is cheap.
        break;
      }

      buffer += decoder.decode(value, { stream: true });

      // SSE events are terminated by a blank line (`\n\n`). Split on that,
      // process all complete events, leave the partial tail for next iter.
      let separatorIndex: number;
      while ((separatorIndex = buffer.indexOf("\n\n")) !== -1) {
        const rawEvent = buffer.slice(0, separatorIndex);
        buffer = buffer.slice(separatorIndex + 2);

        const event = parseSseEvent(rawEvent);
        if (event) {
          yield event;
        }
      }
    }
  } finally {
    // Always release the lock so the connection can be reused/GC'd.
    // Even if the caller stops iterating early (return/throw), this runs.
    reader.releaseLock();
  }
}

/**
 * Parse one SSE event block into a typed ChatStreamEvent.
 *
 * An event block looks like:
 *     data: {"type":"token","text":"Hi"}
 *
 * (Multiple `data:` lines are technically valid per the SSE spec — they'd
 * concatenate with newlines — but our backend always sends one per event.
 * We support the simple case only.)
 *
 * Returns null for empty/unparseable blocks rather than throwing, so a single
 * bad event doesn't kill the whole stream.
 */
function parseSseEvent(raw: string): ChatStreamEvent | null {
  const trimmed = raw.trim();
  if (!trimmed) return null;

  // Strip the "data: " prefix. We tolerate either "data:" or "data: " (one space).
  const match = trimmed.match(/^data:\s?(.*)$/);
  if (!match) {
    console.warn("[chatStream] Ignoring non-data SSE line:", trimmed);
    return null;
  }

  const json = match[1];
  try {
    return JSON.parse(json) as ChatStreamEvent;
  } catch (err) {
    console.warn("[chatStream] Failed to parse SSE event JSON:", json, err);
    return null;
  }
}