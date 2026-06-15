// src/components/home/GreetingStrip.tsx
//
// The thin top strip on the dashboard. Greets the user by name with a
// time-of-day-aware message. Small mascot to the left.
//
// "use client" because we read the current hour for the greeting. Doing
// this on the server would either bake in the build time (wrong) or
// require pushing time logic into the layout (overkill). Client-side is
// fine — it's <10 lines of logic and runs once on mount.
//
// User name and program are hardcoded for now. In Step 13 (auth) we'll
// pull them from session.

"use client";

import Image from "next/image";
import { useMemo } from "react";

// User identity — replaced with session data in Step 13.
const USER = {
  firstName: "Abrar",
};

function getGreeting(hour: number): string {
  if (hour < 5) return "Still up";
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  if (hour < 22) return "Good evening";
  return "Burning the midnight oil";
}

export function GreetingStrip() {
  // useMemo to avoid recomputing on every render. The hour won't change
  // during a session; we read it once.
  const greeting = useMemo(() => getGreeting(new Date().getHours()), []);

  return (
    <div className="flex items-center gap-4 px-8 py-5">
      <Image
        src="/mascot.png"
        alt="SAGE"
        width={44}
        height={44}
        priority
        className="rounded-xl shrink-0 size-11 object-contain"
      />
      <div className="leading-tight">
        <div className="text-lg font-semibold">
          {greeting}, {USER.firstName} <span aria-hidden>👋</span>
        </div>
        <div className="text-sm text-muted-foreground">
          Ready to plan, learn, and achieve today?
        </div>
      </div>
    </div>
  );
}