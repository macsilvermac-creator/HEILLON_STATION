"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { fetchCurrentUser, logoutLegalOperator } from "@/lib/api";

export interface AuthUser {
  user_id: string;
  email: string;
  name: string;
  role: string;
  organization_id?: string;
  is_active?: boolean;
}

interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isReady: boolean;
  login: (user: AuthUser) => void;
  logout: () => Promise<void>;
  setUser: (user: AuthUser | null) => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

function parseStoredUser(raw: string | null): AuthUser | null {
  if (!raw) return null;
  try {
    const u = JSON.parse(raw) as Record<string, unknown>;
    if (typeof u.user_id !== "string" || typeof u.email !== "string") return null;
    return {
      user_id: u.user_id,
      email: u.email,
      name: typeof u.name === "string" ? u.name : "",
      role: typeof u.role === "string" ? u.role : "advogado",
      organization_id: typeof u.organization_id === "string" ? u.organization_id : undefined,
      is_active: typeof u.is_active === "boolean" ? u.is_active : true,
    };
  } catch {
    return null;
  }
}

function mapMePayload(raw: Record<string, unknown>): AuthUser {
  return {
    user_id: String(raw.user_id ?? ""),
    email: String(raw.email ?? ""),
    name: String(raw.name ?? ""),
    role: String(raw.role ?? "advogado"),
    organization_id: typeof raw.organization_id === "string" ? raw.organization_id : undefined,
    is_active: typeof raw.is_active === "boolean" ? raw.is_active : true,
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<AuthUser | null>(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    // Optimistic hydration from localStorage (non-sensitive user data only)
    const storedUser = parseStoredUser(localStorage.getItem("heillon_user"));
    if (storedUser) setUserState(storedUser);

    // Remove any legacy bearer token from localStorage
    localStorage.removeItem("heillon_bearer");

    let cancelled = false;
    (async () => {
      try {
        // Authoritative check via HttpOnly cookie — no bearer needed
        const raw = (await fetchCurrentUser()) as Record<string, unknown>;
        if (cancelled) return;
        const next = mapMePayload(raw);
        setUserState(next);
        localStorage.setItem("heillon_user", JSON.stringify(next));
      } catch {
        // Cookie expired or absent — clear cached user
        if (!cancelled) {
          setUserState(null);
          localStorage.removeItem("heillon_user");
        }
      } finally {
        if (!cancelled) setHydrated(true);
      }
    })();

    // Global session-expiry handler — fired by apiFetch on 401 responses
    const handleSessionExpired = () => {
      localStorage.removeItem("heillon_user");
      setUserState(null);
      // Redirect to login preserving original destination
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        const from = window.location.pathname + window.location.search;
        window.location.href = `/login?from=${encodeURIComponent(from)}&expired=1`;
      }
    };
    window.addEventListener("heillon:session-expired", handleSessionExpired);

    return () => {
      cancelled = true;
      window.removeEventListener("heillon:session-expired", handleSessionExpired);
    };
  }, []);

  const login = useCallback((newUser: AuthUser) => {
    localStorage.setItem("heillon_user", JSON.stringify(newUser));
    setUserState(newUser);
  }, []);

  const logout = useCallback(async () => {
    await logoutLegalOperator();
    localStorage.removeItem("heillon_user");
    setUserState(null);
  }, []);

  const setUser = useCallback((next: AuthUser | null) => {
    if (next) localStorage.setItem("heillon_user", JSON.stringify(next));
    else localStorage.removeItem("heillon_user");
    setUserState(next);
  }, []);

  const value = useMemo<AuthContextType>(
    () => ({
      user: hydrated ? user : null,
      isAuthenticated: hydrated && !!user,
      isReady: hydrated,
      login,
      logout,
      setUser,
    }),
    [hydrated, user, login, logout, setUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
