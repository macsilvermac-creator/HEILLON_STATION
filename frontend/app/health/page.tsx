"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

interface HealthCheck {
  status: "ok" | "error" | "warning";
  message?: string;
  type?: string;
  tsa_url?: string;
  total_agents?: number;
}

interface HealthData {
  status: string;
  version: string;
  timestamp: string;
  checks: Record<string, HealthCheck>;
}

export default function HealthPage() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/v1/health/detailed", { credentials: "include" })
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(
            typeof body.detail === "string" ? body.detail : `HTTP ${res.status}`,
          );
        }
        return res.json() as Promise<HealthData>;
      })
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Falha ao carregar saúde do sistema.");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center pt-20">
        <div className="glass-card p-8">
          <div className="animate-pulse text-white/50">A carregar estado do sistema…</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-4xl px-4 pb-28 pt-28">
        <div className="glass-card border border-amber-500/30 p-8 text-amber-100">
          <h1 className="text-xl font-semibold">System Health</h1>
          <p className="mt-3 text-sm text-white/60">{error}</p>
          <p className="mt-2 text-xs text-white/40">Acesso reservado a administradores autenticados.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto min-h-screen max-w-4xl px-4 pb-28 pt-28">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-8"
      >
        <h1 className="mb-2 text-2xl font-bold text-white">System Health</h1>
        <p className="mb-6 text-white/50">Heillon Legal Platform v{health?.version}</p>

        <div
          className={`mb-8 rounded-xl p-4 ${
            health?.status === "ok"
              ? "border border-green-500/30 bg-green-500/10"
              : "border border-yellow-500/30 bg-yellow-500/10"
          }`}
        >
          <span className="text-lg font-semibold text-white">
            Status:{" "}
            {health?.status === "ok" ? "All Systems Operational" : "Degraded"}
          </span>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {health?.checks &&
            Object.entries(health.checks).map(([name, check]) => (
              <motion.div
                key={name}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="glass-card p-4"
              >
                <div className="mb-2 flex items-center justify-between">
                  <h3 className="font-medium capitalize text-white">{name}</h3>
                  <span
                    className={`rounded-full px-2 py-1 text-xs ${
                      check.status === "ok"
                        ? "bg-green-500/20 text-green-300"
                        : check.status === "warning"
                          ? "bg-yellow-500/20 text-yellow-300"
                          : "bg-red-500/20 text-red-300"
                    }`}
                  >
                    {check.status}
                  </span>
                </div>
                {check.type ? <p className="text-sm text-white/50">Type: {check.type}</p> : null}
                {check.total_agents !== undefined ? (
                  <p className="text-sm text-white/50">Agents: {check.total_agents}</p>
                ) : null}
                {check.tsa_url ? <p className="text-sm text-white/50">TSA: {check.tsa_url}</p> : null}
                {check.message ? <p className="mt-1 text-sm text-white/50">{check.message}</p> : null}
              </motion.div>
            ))}
        </div>

        <p className="mt-6 text-xs text-white/30">
          Last updated:{" "}
          {health?.timestamp
            ? new Date(health.timestamp).toLocaleString("pt-PT")
            : "N/A"}
        </p>
      </motion.div>
    </div>
  );
}
