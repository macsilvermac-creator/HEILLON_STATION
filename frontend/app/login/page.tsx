"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth, type AuthUser } from "@/lib/auth-context";
import { loginLegalOperator } from "@/lib/api";

function toAuthUser(raw: Record<string, unknown>): AuthUser {
  return {
    user_id: String(raw.user_id ?? ""),
    email: String(raw.email ?? ""),
    name: String(raw.name ?? ""),
    role: String(raw.role ?? "advogado"),
    organization_id: typeof raw.organization_id === "string" ? raw.organization_id : undefined,
    is_active: typeof raw.is_active === "boolean" ? raw.is_active : true,
  };
}

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = (await loginLegalOperator(email, password)) as Record<string, unknown>;
      const access = typeof data.access_token === "string" ? data.access_token : null;
      const userRaw = data.user;
      if (!access || !userRaw || typeof userRaw !== "object") {
        throw new Error("Resposta de sessão inválida.");
      }
      login(access, toAuthUser(userRaw as Record<string, unknown>));
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Credenciais inválidas.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center px-4 pt-24">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(212,175,55,0.08),transparent_55%)]" />
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55 }}
        className="glass-elite relative w-full max-w-md p-8 md:p-10"
      >
        <h1 className="mb-2 text-2xl font-bold text-white">Bem-vindo</h1>
        <p className="mb-8 text-sm text-white/50">Entre na sua conta Heillon Legal</p>

        {error ? (
          <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200">{error}</div>
        ) : null}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="mb-2 block text-sm text-white/60">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder-white/30 transition-colors focus:border-gold-500/60 focus:outline-none focus:ring-1 focus:ring-gold-500/40"
              placeholder="perito@exemplo.com"
            />
          </div>
          <div>
            <label className="mb-2 block text-sm text-white/60">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder-white/30 transition-colors focus:border-gold-500/60 focus:outline-none focus:ring-1 focus:ring-gold-500/40"
              placeholder="••••••••"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="btn-gold relative w-full overflow-hidden py-3 text-center disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? (
              <span className="inline-flex items-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-deep-space-900 border-t-transparent" />
                A iniciar sessão…
              </span>
            ) : (
              "Entrar"
            )}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-white/40">
          Sem conta?{" "}
          <Link href="/register" className="text-gold-400 transition-colors hover:text-gold-300">
            Criar conta
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
