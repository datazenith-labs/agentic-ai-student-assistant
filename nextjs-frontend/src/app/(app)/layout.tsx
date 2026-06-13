// (app)/layout.tsx — shared layout for all logged-in pages.
// Phase 12.2.3: passthrough only — the real sidebar/topbar shell
// is wired in Phase 12.2.4. For now, just renders children full-bleed.

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}