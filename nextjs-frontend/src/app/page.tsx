// src/app/page.tsx
//
// Public landing page (route: "/"). Lives OUTSIDE the (app)/ group so it
// renders without the sidebar/topbar — like a marketing page.
//
// Right now this is intentionally simple. Phase 12.8 (or beyond) will turn
// this into a real marketing landing with feature highlights, screenshots,
// pricing-style cards, etc. For now we just need a clean entry point with
// a button that takes the user into the actual app at /home.
//
// When auth lands in Step 13, this page will check the session server-side
// and redirect to /home if logged in, or render the marketing content if not.

import Image from "next/image";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function LandingPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-background text-foreground gap-8 p-8">
      <div className="flex flex-col items-center text-center space-y-5">
        <Image
          src="/mascot.png"
          alt="SAGE mascot"
          width={88}
          height={88}
          priority
          className="rounded-2xl size-[88px] object-contain"
        />
        <h1 className="text-5xl font-bold tracking-tight bg-gradient-to-r from-foreground via-violet-500 to-violet-400 bg-clip-text text-transparent">
          SAGE
        </h1>
        <p className="text-xl text-muted-foreground max-w-md">
          Student Academic Guidance Engine — your AI study assistant.
        </p>
        <p className="text-sm text-muted-foreground">
          Plan exams, get personalized advice, automate your campus life.
        </p>
      </div>

      <Button asChild size="lg" className="bg-violet-600 hover:bg-violet-500 text-white shadow-lg shadow-violet-900/30">
        <Link href="/home">
          Open SAGE
          <ArrowRight className="ml-1.5 size-4" />
        </Link>
      </Button>

      <p className="text-xs text-muted-foreground">
        Phase 12.3 — Dashboard in progress.
      </p>
    </main>
  );
}