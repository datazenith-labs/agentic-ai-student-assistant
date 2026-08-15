import { create } from "zustand";
import {
  AuthUser,
  clearAccessToken,
  fetchMe,
  getAccessToken,
  login,
  saveAccessToken,
  signup,
} from "@/lib/auth";

type AuthState = {
  user: AuthUser | null;
  token: string | null;
  initialized: boolean;
  initialize: () => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (name: string, email: string, password: string) => Promise<void>;
  signOut: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  initialized: false,
  initialize: async () => {
    const token = getAccessToken();
    if (!token) return set({ initialized: true });
    try {
      const user = await fetchMe(token);
      set({ user, token, initialized: true });
    } catch {
      clearAccessToken();
      set({ user: null, token: null, initialized: true });
    }
  },
  signIn: async (email, password) => {
    const result = await login(email, password);
    saveAccessToken(result.access_token);
    set({ token: result.access_token, user: result.user, initialized: true });
  },
  signUp: async (name, email, password) => {
    const result = await signup(name, email, password);
    saveAccessToken(result.access_token);
    set({ token: result.access_token, user: result.user, initialized: true });
  },
  signOut: () => {
    clearAccessToken();
    set({ user: null, token: null, initialized: true });
  },
}));
