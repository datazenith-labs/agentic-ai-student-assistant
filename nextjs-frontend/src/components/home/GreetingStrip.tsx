"use client";

import Image from "next/image";
import { useMemo } from "react";

import { useAuthStore } from "@/stores/auth-store";

function getGreeting(hour: number): string {
  if (hour < 5) return "Still up";
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  if (hour < 22) return "Good evening";
  return "Burning the midnight oil";
}

export function GreetingStrip() {
  const name = useAuthStore((state) => state.user?.name);
  const firstName = name?.trim().split(/\s+/)[0] || "Student";
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
          {greeting}, {firstName} <span aria-hidden>👋</span>
        </div>
        <div className="text-sm text-muted-foreground">
          Ready to plan, learn, and achieve today?
        </div>
      </div>
    </div>
  );
}
