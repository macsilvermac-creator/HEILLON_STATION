"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

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
  token: string | null;
  isAuthenticated: boolean;
  isReady: boolean;
  login: (token: string, user: AuthUser) => void;
  logout: () => void;
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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const storedToken = localStorage.getItem("heillon_bearer");
    const storedUser = parseStoredUser(localStorage.getItem("heillon_user"));
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUserState(storedUser);
    }
    setHydrated(true);
  }, []);

  const login = useCallback((newToken: string, newUser: AuthUser) => {
    localStorage.setItem("heillon_bearer", newToken);
    localStorage.setItem("heillon_user", JSON.stringify(newUser));
    setToken(newToken);
    setUserState(newUser);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("heillon_bearer");
    localStorage.removeItem("heillon_user");
    setToken(null);
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
      token: hydrated ? token : null,
      isAuthenticated: hydrated && !!token,
      isReady: hydrated,
      login,
      logout,
      setUser,
    }),
    [hydrated, user, token, login, logout, setUser],
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
