// src/components/home/widgets/TodaysOverview.tsx
//
// Right-column widget: 4 stat tiles in a 2x2 grid summarizing today's
// academic load. Hardcoded data for now — Phase 12.7 wires real numbers
// from /api/dashboard/overview.
//
// Each stat has: small icon tile, big number, small label. Icons use
// the same colored-tile pattern as SuggestedCards (brand accents, not
// theme tokens).
//
// "View all" link in the header — placeholder route /tasks for now.

import Link from "next/link";
import {
  CalendarDays,
  GraduationCap,
  Clock,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";

import { Card } from "@/components/ui/card";

type Stat = {
  id: string;
  value: string;
  label: string;
  icon: LucideIcon;
  iconBg: string;
  iconText: string;
};

const STATS: Stat[] = [
  {
    id: "tasks",
    value: "2",
    label: "Tasks Due",
    icon: CalendarDays,
    iconBg: "bg-violet-100 dark:bg-violet-950/40",
    iconText: "text-violet-600 dark:text-violet-400",
  },
  {
    id: "exams",
    value: "3",
    label: "Exams",
    icon: GraduationCap,
    iconBg: "bg-teal-100 dark:bg-teal-950/40",
    iconText: "text-teal-600 dark:text-teal-400",
  },
  {
    id: "study-time",
    value: "4.5 hrs",
    label: "Study Time",
    icon: Clock,
    iconBg: "bg-orange-100 dark:bg-orange-950/40",
    iconText: "text-orange-600 dark:text-orange-400",
  },
  {
    id: "progress",
    value: "78%",
    label: "Progress",
    icon: TrendingUp,
    iconBg: "bg-blue-100 dark:bg-blue-950/40",
    iconText: "text-blue-600 dark:text-blue-400",
  },
];

export function TodaysOverview() {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-sm">Today's Overview</h3>
        <Link
          href="/tasks"
          className="text-xs font-medium text-violet-600 dark:text-violet-400 hover:underline"
        >
          View all
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {STATS.map((s) => {
          const Icon = s.icon;
          return (
            <div
              key={s.id}
              className="rounded-lg border border-border p-3 bg-muted/20"
            >
              <div
                className={`size-8 rounded-md flex items-center justify-center mb-2 ${s.iconBg} ${s.iconText}`}
              >
                <Icon className="size-4" />
              </div>
              <div className="text-lg font-bold leading-tight">{s.value}</div>
              <div className="text-[11px] text-muted-foreground">{s.label}</div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}