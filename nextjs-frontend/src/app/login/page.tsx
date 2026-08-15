"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";

export default function LoginPage() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const initialize = useAuthStore((state) => state.initialize);
  const signIn = useAuthStore((state) => state.signIn);
  const signUp = useAuthStore((state) => state.signUp);
  const [signupMode, setSignupMode] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { void initialize(); }, [initialize]);
  useEffect(() => {
    if (user) {
      const next = new URLSearchParams(window.location.search).get("next");
      router.replace(next?.startsWith("/") ? next : "/home");
    }
  }, [user, router]);

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(""); setBusy(true);
    try {
      if (signupMode) await signUp(name, email, password);
      else await signIn(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed.");
    } finally { setBusy(false); }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-[#0f0f1a] px-4">
      <form onSubmit={submit} className="w-full max-w-sm space-y-5 rounded-2xl border border-white/10 bg-white/5 p-8 text-white shadow-2xl">
        <div><h1 className="text-3xl font-bold">SAGE</h1><p className="mt-1 text-sm text-slate-400">{signupMode ? "Create your student account" : "Welcome back"}</p></div>
        {signupMode && <input required value={name} onChange={(e) => setName(e.target.value)} placeholder="Full name" className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 outline-none focus:border-violet-500" />}
        <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 outline-none focus:border-violet-500" />
        <input required minLength={signupMode ? 8 : 1} type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 outline-none focus:border-violet-500" />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button disabled={busy} className="w-full rounded-lg bg-violet-600 py-2.5 font-medium hover:bg-violet-500 disabled:opacity-60">{busy ? "Please wait…" : signupMode ? "Create account" : "Sign in"}</button>
        <button type="button" onClick={() => { setSignupMode(!signupMode); setError(""); }} className="w-full text-sm text-violet-300 hover:text-violet-200">{signupMode ? "Already registered? Sign in" : "New to SAGE? Create an account"}</button>
      </form>
    </main>
  );
}
