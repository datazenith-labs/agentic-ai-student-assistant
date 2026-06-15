// src/components/home/widgets/StudyStreak.tsx
//
// Right-column widget: shows current streak (X days) and a week-strip of
// 7 day-dots — checkmark for completed, day number for today, dim for not yet.
//
// Mock data for now. Phase 12.7 wires real progress from the backend's
// confidence_logs (Step 9 tools).
//
// Why this matters in product: study streaks drive engagement. Duolingo,
// Khan Academy, etc. all use them. Visual progress > textual progress.

import { Check, Flame } from "lucide-react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

// Mock: current streak is 12 days. Today is day 8 of the current week
// (showing through the week-strip — most days completed, today in progress,
// future days dim). All replaced with real data in 12.7.
const STREAK_DAYS = 12;
const WEEK = [
  { id: 0, label: "Mon", status: "done" },
  { id: 1, label: "Tue", status: "done" },
  { id: 2, label: "Wed", status: "done" },
  { id: 3, label: "Thu", status: "done" },
  { id: 4, label: "Fri", status: "done" },
  { id: 5, label: "Sat", status: "done" },
  { id: 6, label: "Sun", status: "today", dayNumber: 8 },
] as const;

export function StudyStreak() {
  return (
    <Card className="p-5">
      <h3 className="font-semibold text-sm mb-4">Study Streak</h3>

      {/* Streak number row */}
      <div className="flex items-center gap-3 mb-4">
        <div className="size-12 rounded-full bg-orange-100 dark:bg-orange-950/40 flex items-center justify-center text-orange-500 dark:text-orange-400">
          <Flame className="size-6" fill="currentColor" />
        </div>
        <div className="leading-tight">
          <div className="text-xl font-bold">{STREAK_DAYS} days</div>
          <div className="text-xs text-muted-foreground">
            Keep it up! You're doing great.
          </div>
        </div>
      </div>

      {/* Week-strip: 7 dots, one per weekday */}
      <div className="flex items-center justify-between gap-1">
        {WEEK.map((d) => {
          const isToday = d.status === "today";
          return (
            <div
              key={d.id}
              aria-label={`${d.label}: ${d.status}`}
              className={cn(
                "size-8 rounded-full flex items-center justify-center text-xs font-semibold transition-colors",
                isToday
                  ? "bg-gradient-to-br from-violet-500 to-violet-600 text-white ring-2 ring-violet-300 dark:ring-violet-800"
                  : "bg-violet-600 text-white"
              )}
            >
              {isToday ? (d as { dayNumber: number }).dayNumber : (
                <Check className="size-4" />
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}