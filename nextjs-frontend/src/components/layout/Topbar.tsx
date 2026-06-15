// src/components/layout/Topbar.tsx
//
// Horizontal bar above the main content. Sits to the right of the sidebar.
// Layout from the mockup:
//
//   ┌──────────────────────────────────────────────────────┐
//   │ [search input        ]        [theme] [bell] [⌘K]    │
//   └──────────────────────────────────────────────────────┘
//
// Height: 60px (matches the sidebar header for clean alignment).
// Border-bottom only — no shadow — to feel flat and modern.
//
// Interactive bits are visual stubs for now:
//   - Search input: doesn't filter anything (wires up in 12.6 for upload/RAG)
//   - Theme toggle: visual only (real toggle in 12.9)
//   - Bell: notifications system isn't in scope yet
//   - ⌘K: command palette is a stretch goal
//
// Tooltips on the icon buttons. TooltipProvider lives in (app)/layout.tsx.

"use client";

import { Bell, Command, Search, Sun } from "lucide-react";

import { Input } from "@/components/ui/input";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function Topbar() {
  return (
    <header className="h-[60px] shrink-0 border-b border-border bg-background flex items-center justify-between gap-4 px-6">
      {/* ─── Search ──────────────────────────────────────────────── */}
      <div className="flex-1 max-w-md relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
        <Input
          type="search"
          placeholder="Search chats, documents, tasks..."
          aria-label="Search"
          className="pl-9 bg-muted/40 border-transparent focus-visible:bg-background focus-visible:border-border"
        />
      </div>

      {/* ─── Right-side actions ──────────────────────────────────── */}
      <div className="flex items-center gap-1">
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              aria-label="Toggle theme"
              className="size-9 inline-flex items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            >
              <Sun className="size-4" />
            </button>
          </TooltipTrigger>
          <TooltipContent>Toggle theme</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              aria-label="Notifications"
              className="size-9 inline-flex items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground transition-colors relative"
            >
              <Bell className="size-4" />
              {/* Unread dot — visual stub */}
              <span className="absolute top-2 right-2 size-1.5 rounded-full bg-violet-500" />
            </button>
          </TooltipTrigger>
          <TooltipContent>Notifications</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              aria-label="Command palette"
              className="ml-1 h-9 px-2.5 inline-flex items-center gap-1.5 rounded-md border border-border text-xs text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            >
              <Command className="size-3.5" />
              <span className="font-mono">K</span>
            </button>
          </TooltipTrigger>
          <TooltipContent>Command palette (coming soon)</TooltipContent>
        </Tooltip>
      </div>
    </header>
  );
}