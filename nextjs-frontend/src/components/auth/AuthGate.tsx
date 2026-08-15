"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, initialized, initialize } = useAuthStore();

  useEffect(() => { void initialize(); }, [initialize]);
  useEffect(() => {
    if (initialized && !user) router.replace(`/login?next=${encodeURIComponent(pathname)}`);
  }, [initialized, user, router, pathname]);

  if (!initialized || !user) {
    return <div className="grid min-h-screen place-items-center text-sm text-muted-foreground">Loading SAGE…</div>;
  }
  return children;
}
