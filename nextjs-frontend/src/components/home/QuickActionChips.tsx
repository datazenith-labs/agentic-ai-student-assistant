// src/components/home/QuickActionChips.tsx
//
// Horizontal row of suggested starter actions below the hero. Each chip is
// a card with: icon | bold verb / lighter subject. Clicking will eventually
// prefill the chat input (Phase 12.5). For now: console.log + visual feedback.
//
// Why client component: chips need onClick handlers. Tiny ones for now.
//
// Layout: horizontal flex with gap, no wrap, overflow-x-auto on small screens
// (matches the mockup which shows an arrow indicating horizontal scroll).
// On wide screens all 4 fit. The arrow indicator on the right edge is a
// scroll affordance — visual only, doesn't scroll programmatically.

"use client";

import { BookOpen, ClipboardList, CalendarDays, FileText, ChevronRight, type LucideIcon } from "lucide-react";

import { Card } from "@/components/ui/card";

type QuickAction = {
  id: string;
  verb: string;       // e.g. "Explain"
  subject: string;    // e.g. "Data Structures"
  icon: LucideIcon;
  // Future: prefill text for the chat input.
  prompt: string;
};

const QUICK_ACTIONS: QuickAction[] = [
  {
    id: "explain",
    verb: "Explain",
    subject: "Data Structures",
    icon: BookOpen,
    prompt: "Explain Data Structures with simple examples.",
  },
  {
    id: "quiz",
    verb: "Generate",
    subject: "Quiz on OOP",
    icon: ClipboardList,
    prompt: "Generate a quiz on Object-Oriented Programming.",
  },
  {
    id: "plan",
    verb: "Plan",
    subject: "My Revision",
    icon: CalendarDays,
    prompt: "Help me plan a revision schedule for my upcoming exams.",
  },
  {
    id: "summarize",
    verb: "Summarize",
    subject: "This PDF",
    icon: FileText,
    prompt: "Summarize the PDF I just uploaded.",
  },
];

export function QuickActionChips() {
  const handleClick = (action: QuickAction) => {
    // TODO (Phase 12.5): wire to chat input — prefill the textarea, focus it.
    console.log("[QuickAction]", action.id, action.prompt);
  };

  return (
    <div className="relative">
      <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1 scrollbar-hide">
        {QUICK_ACTIONS.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.id}
              type="button"
              onClick={() => handleClick(action)}
              className="shrink-0 group"
            >
              <Card className="w-[180px] p-4 hover:border-violet-300 dark:hover:border-violet-700 hover:shadow-md transition-all cursor-pointer">
                <div className="flex flex-col gap-2 items-start">
                  <div className="size-8 rounded-lg bg-violet-100 dark:bg-violet-950/50 flex items-center justify-center text-violet-600 dark:text-violet-400 group-hover:bg-violet-200 dark:group-hover:bg-violet-900/60 transition-colors">
                    <Icon className="size-4" />
                  </div>
                  <div className="text-left leading-tight">
                    <div className="font-semibold text-sm">{action.verb}</div>
                    <div className="text-xs text-muted-foreground">
                      {action.subject}
                    </div>
                  </div>
                </div>
              </Card>
            </button>
          );
        })}
      </div>

      {/* Scroll affordance — visual hint only, like the mockup */}
      <div
        aria-hidden
        className="absolute right-0 top-1/2 -translate-y-1/2 size-9 rounded-full bg-background border border-border shadow-sm flex items-center justify-center text-muted-foreground pointer-events-none"
      >
        <ChevronRight className="size-4" />
      </div>
    </div>
  );
}