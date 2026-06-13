import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-background text-foreground gap-8 p-8">
      <div className="text-center space-y-4">
        <h1 className="text-5xl font-bold tracking-tight">
          🎓 SAGE
        </h1>
        <p className="text-xl text-muted-foreground max-w-md">
          Student Academic Guidance Engine — your AI study assistant
        </p>
        <p className="text-sm text-muted-foreground">
          Next.js + TypeScript + Tailwind + shadcn/ui
        </p>
      </div>

      <div className="flex gap-3">
        <Button>Primary Action</Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="outline">Outline</Button>
        <Button variant="ghost">Ghost</Button>
      </div>

      <p className="text-xs text-muted-foreground">
        Phase 12.1 — Foundation complete. Violet theme active.
      </p>
    </main>
  );
}