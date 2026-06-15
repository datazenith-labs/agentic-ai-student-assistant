// src/app/(app)/home/page.tsx
//
// Dashboard home — main landing experience inside the SAGE shell.
//
// Composition only. Real UI lives in src/components/home/*.
//
// Build progress (Phase 12.3 — Dashboard):
//   Part 2: GreetingStrip + CenterHero               ✓
//   Part 3: + QuickActionChips + ChatInputBox        ✓
//   Part 4: + SuggestedCards + disclaimer footer     ✓
//   Part 5a: two-col grid + TodaysOverview            ✓
//            + UpcomingExams (right column)
//   Part 5b: + StudyStreak + QuickUpload (right col) ← current — COMPLETE
//
// Layout:
//   ┌─[main scroll]──────────────────────────────────────┐
//   │  GreetingStrip (full width)                        │
//   │  ┌─[center col flex-1]─┐ ┌─[right col 340px]─────┐ │
//   │  │  CenterHero          │ │  TodaysOverview       │ │
//   │  │  QuickActionChips    │ │  UpcomingExams        │ │
//   │  │  ChatInputBox        │ │  StudyStreak          │ │
//   │  │  SuggestedCards      │ │  QuickUpload          │ │
//   │  │  Disclaimer          │ │                       │ │
//   │  └──────────────────────┘ └───────────────────────┘ │
//   └────────────────────────────────────────────────────┘

import { CenterHero } from "@/components/home/CenterHero";
import { ChatInputBox } from "@/components/home/ChatInputBox";
import { GreetingStrip } from "@/components/home/GreetingStrip";
import { QuickActionChips } from "@/components/home/QuickActionChips";
import { SuggestedCards } from "@/components/home/SuggestedCards";
import { QuickUpload } from "@/components/home/widgets/QuickUpload";
import { StudyStreak } from "@/components/home/widgets/StudyStreak";
import { TodaysOverview } from "@/components/home/widgets/TodaysOverview";
import { UpcomingExams } from "@/components/home/widgets/UpcomingExams";

export default function HomePage() {
  return (
    <div className="min-h-full">
      <GreetingStrip />

      <div className="px-8 pb-12">
        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          {/* Center column */}
          <div className="space-y-6 min-w-0">
            <CenterHero />
            <QuickActionChips />
            <ChatInputBox />
            <SuggestedCards />

            <div className="rounded-lg bg-muted/40 border border-border px-4 py-2.5 text-center">
              <p className="text-xs text-muted-foreground">
                SAGE can make mistakes. Please verify important information.
              </p>
            </div>
          </div>

          {/* Right column */}
          <aside className="space-y-4">
            <TodaysOverview />
            <UpcomingExams />
            <StudyStreak />
            <QuickUpload />
          </aside>
        </div>
      </div>
    </div>
  );
}