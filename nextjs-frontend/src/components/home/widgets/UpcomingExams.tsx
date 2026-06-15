// src/components/home/widgets/UpcomingExams.tsx
//
// Right-column widget: vertical list of the next 3 exams with date,
// time, and days-remaining badge. Mock data for now — replaced in 12.7
// with real exam schedule from the Exam Prep MCP server.
//
// Each row: icon tile + (name + datetime) + days-remaining badge.
// The badge color shifts based on urgency:
//   <= 7 days → red
//   <= 14 days → orange
//   > 14 days → muted

import Link from "next/link";
import { CalendarDays, Database, Cpu, type LucideIcon } from "lucide-react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type Exam = {
  id: string;
  name: string;
  date: string;
  time: string;
  daysAway: number;
  icon: LucideIcon;
  iconBg: string;
  iconText: string;
};

const EXAMS: Exam[] = [
  {
    id: "ds",
    name: "Data Structures",
    date: "Jun 05, 2026",
    time: "10:00 AM",
    daysAway: 5,
    icon: CalendarDays,
    iconBg: "bg-violet-100 dark:bg-violet-950/40",
    iconText: "text-violet-600 dark:text-violet-400",
  },
  {
    id: "dbms",
    name: "Database Systems",
    date: "Jun 10, 2026",
    time: "2:00 PM",
    daysAway: 10,
    icon: Database,
    iconBg: "bg-teal-100 dark:bg-teal-950/40",
    iconText: "text-teal-600 dark:text-teal-400",
  },
  {
    id: "os",
    name: "Operating Systems",
    date: "Jun 15, 2026",
    time: "9:00 AM",
    daysAway: 15,
    icon: Cpu,
    iconBg: "bg-orange-100 dark:bg-orange-950/40",
    iconText: "text-orange-600 dark:text-orange-400",
  },
];

function urgencyClass(daysAway: number): string {
  if (daysAway <= 7) {
    return "bg-red-100 dark:bg-red-950/40 text-red-700 dark:text-red-400";
  }
  if (daysAway <= 14) {
    return "bg-orange-100 dark:bg-orange-950/40 text-orange-700 dark:text-orange-400";
  }
  return "bg-muted text-muted-foreground";
}

export function UpcomingExams() {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-sm">Upcoming Exams</h3>
        <Link
          href="/exam-prep"
          className="text-xs font-medium text-violet-600 dark:text-violet-400 hover:underline"
        >
          View all
        </Link>
      </div>

      <ul className="space-y-3">
        {EXAMS.map((e) => {
          const Icon = e.icon;
          return (
            <li key={e.id} className="flex items-center gap-3">
              <div
                className={`size-10 shrink-0 rounded-lg flex items-center justify-center ${e.iconBg} ${e.iconText}`}
              >
                <Icon className="size-4" />
              </div>
              <div className="flex-1 min-w-0 leading-tight">
                <div className="font-medium text-sm truncate">{e.name}</div>
                <div className="text-[11px] text-muted-foreground">
                  {e.date} · {e.time}
                </div>
              </div>
              <span
                className={cn(
                  "shrink-0 rounded-md px-2 py-1 text-[10px] font-semibold",
                  urgencyClass(e.daysAway)
                )}
              >
                {e.daysAway} Days
              </span>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}