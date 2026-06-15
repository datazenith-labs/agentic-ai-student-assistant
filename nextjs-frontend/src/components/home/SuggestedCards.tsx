// src/components/home/SuggestedCards.tsx
//
// 4-card grid of suggested actions below the chat input. Unlike the quick
// chips above (which prefill the chat), these route to dedicated tool pages
// — Revise Weak Topics, Mock Exam, Study Roadmap, Flashcards.
//
// Each card has its own accent color for the icon tile. Hardcoded inline —
// they're brand-style accents, not theme tokens, so they shouldn't shift
// in dark mode. The card body and text stay theme-aware.
//
// Routes are best-guesses for now; they'll wire to real pages in 12.7.
// Until then, clicking a card just navigates to a placeholder route that
// already exists in the (app) group.

"use client";

import Link from "next/link";
import {
  ArrowRight,
  ClipboardCheck,
  CalendarRange,
  BookMarked,
  Layers,
  type LucideIcon,
} from "lucide-react";

import { Card } from "@/components/ui/card";

type Suggestion = {
  id: string;
  title: string;
  description: string;
  href: string;
  icon: LucideIcon;
  // Tailwind utility classes for the icon tile (bg + text color).
  // Hardcoded brand accents, not theme tokens.
  iconBg: string;
  iconText: string;
};

const SUGGESTIONS: Suggestion[] = [
  {
    id: "revise",
    title: "Revise Weak Topics",
    description: "Focus on your weak areas",
    href: "/learning",
    icon: ClipboardCheck,
    iconBg: "bg-violet-100 dark:bg-violet-950/40",
    iconText: "text-violet-600 dark:text-violet-400",
  },
  {
    id: "mock-exam",
    title: "Mock Exam",
    description: "Take a full-length test",
    href: "/exam-prep",
    icon: CalendarRange,
    iconBg: "bg-teal-100 dark:bg-teal-950/40",
    iconText: "text-teal-600 dark:text-teal-400",
  },
  {
    id: "roadmap",
    title: "Study Roadmap",
    description: "Get a personalized plan",
    href: "/learning",
    icon: BookMarked,
    iconBg: "bg-orange-100 dark:bg-orange-950/40",
    iconText: "text-orange-600 dark:text-orange-400",
  },
  {
    id: "flashcards",
    title: "Flashcards",
    description: "Smart flashcards from notes",
    href: "/learning",
    icon: Layers,
    iconBg: "bg-blue-100 dark:bg-blue-950/40",
    iconText: "text-blue-600 dark:text-blue-400",
  },
];

export function SuggestedCards() {
  return (
    <section>
      <h2 className="text-sm font-semibold mb-3">Suggested for you</h2>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {SUGGESTIONS.map((s) => {
          const Icon = s.icon;
          return (
            <Link key={s.id} href={s.href} className="group block">
              <Card className="p-4 h-full hover:border-violet-300 dark:hover:border-violet-700 hover:shadow-md transition-all">
                <div className="flex flex-col gap-3">
                  <div
                    className={`size-10 rounded-lg flex items-center justify-center ${s.iconBg} ${s.iconText}`}
                  >
                    <Icon className="size-5" />
                  </div>

                  <div className="leading-tight">
                    <div className="font-semibold text-sm">{s.title}</div>
                    <div className="text-xs text-muted-foreground mt-0.5">
                      {s.description}
                    </div>
                  </div>

                  <div className="text-xs font-medium text-violet-600 dark:text-violet-400 flex items-center gap-1 mt-1 group-hover:gap-1.5 transition-all">
                    Start Now
                    <ArrowRight className="size-3" />
                  </div>
                </div>
              </Card>
            </Link>
          );
        })}
      </div>
    </section>
  );
}