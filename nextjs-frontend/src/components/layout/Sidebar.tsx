// src/components/layout/Sidebar.tsx
//
// The left navigation sidebar. Dark navy background, full-height, fixed width
// (280px on lg+). Layout from the user's mockup screenshot:
//
//   ┌─────────────────────────┐
//   │ [mascot] SAGE        << │   header
//   │ Student Academic ...    │
//   ├─────────────────────────┤
//   │ [+] New Chat            │   primary CTA
//   ├─────────────────────────┤
//   │ [icon] Home  (active)   │   nav items (8)
//   │ [icon] Chat             │
//   │ ...                     │
//   ├─────────────────────────┤
//   │ Recent Chats            │
//   │  - Data Structures Quiz │   scrollable list
//   │  - ...                  │
//   │  View all               │
//   ├─────────────────────────┤
//   │ [avatar] Abrar Fahim    │   user card
//   │          CS  ▾  [⚙]     │
//   └─────────────────────────┘
//
// Active route highlighting uses usePathname() — Next.js client hook —
// so the whole component is "use client". The TooltipProvider wrap
// happens in (app)/layout.tsx, not here.

"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronsLeft, Plus, Settings, ChevronDown } from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

import { NAV_ITEMS, MOCK_RECENT_CHATS } from "./nav-items";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-[280px] flex-col bg-[#0F0F1A] text-slate-200">
      {/* ─── Header: logo + collapse button ──────────────────────── */}
      <div className="flex items-start justify-between gap-2 p-5">
        <div className="flex items-center gap-2.5">
          <Image
            src="/mascot.png"
            alt="SAGE mascot"
            width={40}
            height={40}
            priority
            className="rounded-lg"
          />
          <div className="leading-tight">
            <div className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-violet-200 to-violet-400 bg-clip-text text-transparent">
              SAGE
            </div>
            <div className="text-[10px] text-slate-400 -mt-0.5">
              Student Academic Guidance Engine
            </div>
          </div>
        </div>
        <button
          type="button"
          aria-label="Collapse sidebar"
          className="text-slate-400 hover:text-slate-200 transition-colors mt-1"
        >
          <ChevronsLeft className="size-4" />
        </button>
      </div>

      {/* ─── New Chat CTA ────────────────────────────────────────── */}
      <div className="px-4 pb-4">
        <Button
          size="lg"
          className="w-full justify-start gap-2 bg-violet-600 hover:bg-violet-500 text-white shadow-lg shadow-violet-900/30"
        >
          <Plus className="size-4" />
          <span className="font-medium">New Chat</span>
        </Button>
      </div>

      {/* ─── Nav items ───────────────────────────────────────────── */}
      <nav className="px-3 space-y-0.5">
        {NAV_ITEMS.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);

          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                isActive
                  ? "bg-slate-800/80 text-white"
                  : "text-slate-300 hover:bg-slate-800/50 hover:text-white"
              )}
            >
              <Icon className="size-4 shrink-0" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <Separator className="my-4 bg-slate-800/60" />

      {/* ─── Recent Chats ────────────────────────────────────────── */}
      <div className="flex-1 min-h-0 px-3 flex flex-col">
        <div className="px-3 pb-2 text-xs font-medium uppercase tracking-wider text-slate-500">
          Recent Chats
        </div>

        <ScrollArea className="flex-1 -mx-3 px-3">
          <ul className="space-y-0.5">
            {MOCK_RECENT_CHATS.map((chat) => (
              <li key={chat.id}>
                <button
                  type="button"
                  className="w-full flex items-baseline justify-between gap-3 rounded-md px-3 py-2 text-sm text-slate-300 hover:bg-slate-800/40 hover:text-white text-left transition-colors"
                >
                  <span className="truncate">{chat.title}</span>
                  <span className="shrink-0 text-[10px] text-slate-500">
                    {chat.timestamp}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </ScrollArea>

        <Link
          href="/chat"
          className="mt-1 px-3 py-2 text-sm text-violet-400 hover:text-violet-300 transition-colors"
        >
          View all
        </Link>
      </div>

      {/* ─── User card ───────────────────────────────────────────── */}
      <div className="border-t border-slate-800/60 p-4">
        <div className="flex items-center gap-3">
          <Avatar className="size-9">
            <AvatarImage src="" alt="Abrar Fahim" />
            <AvatarFallback className="bg-violet-900 text-violet-100 text-xs">
              AF
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 leading-tight min-w-0">
            <div className="text-sm font-medium text-white truncate">
              Abrar Fahim
            </div>
            <div className="text-[11px] text-slate-400">Computer Science</div>
          </div>
          <button
            type="button"
            aria-label="Account menu"
            className="text-slate-400 hover:text-slate-200 transition-colors"
          >
            <ChevronDown className="size-4" />
          </button>
          <button
            type="button"
            aria-label="Settings"
            className="text-slate-400 hover:text-slate-200 transition-colors"
          >
            <Settings className="size-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}