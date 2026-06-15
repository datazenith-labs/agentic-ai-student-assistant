// src/app/(app)/layout.tsx
//
// Shared shell for every logged-in page (every route under (app)).
// Composes Sidebar + Topbar around a scrollable content area.
//
// Structure:
//   <TooltipProvider>                — required by Topbar's tooltips
//     <div flex h-screen>            — full viewport, side-by-side
//       <Sidebar />                  — fixed 280px, scrolls internally
//       <div flex-1 flex-col>        — right pane: column
//         <Topbar />                 — 60px, sticky-feeling
//         <main flex-1 overflow>     — only this scrolls
//           {children}
//         </main>
//       </div>
//     </div>
//   </TooltipProvider>
//
// TooltipProvider is mounted ONCE here, not in individual components,
// so all tooltips share one portal/state.

import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { TooltipProvider } from "@/components/ui/tooltip";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <TooltipProvider delayDuration={200}>
      <div className="flex h-screen w-full overflow-hidden bg-background">
        <Sidebar />

        <div className="flex flex-1 flex-col overflow-hidden">
          <Topbar />
          <main className="flex-1 overflow-y-auto">{children}</main>
        </div>
      </div>
    </TooltipProvider>
  );
}