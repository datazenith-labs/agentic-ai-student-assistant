// src/components/home/CenterHero.tsx
//
// The visual centerpiece of the dashboard. Big mascot in a soft glow ring,
// "How can I help you today?" headline with a gradient on the verb phrase,
// and a one-line subtitle.
//
// The mascot has a subtle violet "halo" ring effect — pure CSS, no animation.
// In Phase 12.8 polish we may add a soft floating animation here.
//
// Layout-wise this component centers itself horizontally and has comfortable
// vertical padding. The actual page composition handles where it sits.

import Image from "next/image";

export function CenterHero() {
  return (
    <div className="flex flex-col items-center text-center py-8 px-4">
      {/* Mascot in a soft violet halo */}
      <div className="relative mb-6">
        {/* Outer glow ring — pure CSS, no images */}
        <div
          aria-hidden
          className="absolute inset-0 -m-4 rounded-full bg-violet-500/10 blur-2xl"
        />
        <div
          aria-hidden
          className="absolute inset-0 -m-2 rounded-full bg-gradient-to-br from-violet-200 via-violet-100 to-transparent dark:from-violet-900/40 dark:via-violet-950/30"
        />

        {/* Mascot on top */}
        <div className="relative rounded-full bg-background p-2 shadow-xl shadow-violet-200/30 dark:shadow-violet-900/30 ring-1 ring-violet-200/50 dark:ring-violet-800/30">
          <Image
            src="/mascot.png"
            alt="SAGE mascot"
            width={140}
            height={140}
            priority
            className="rounded-full size-[140px] object-contain"
          />
        </div>
      </div>

      {/* Headline */}
      <h1 className="text-4xl font-bold tracking-tight">
        How can{" "}
        <span className="bg-gradient-to-r from-blue-500 via-violet-500 to-violet-400 bg-clip-text text-transparent">
          I help you
        </span>{" "}
        today?
      </h1>

      {/* Subtitle */}
      <p className="mt-3 text-muted-foreground max-w-lg">
        Ask me anything about your studies, exams, courses, or campus life.
      </p>
    </div>
  );
}