"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { listMissions } from "@/lib/api";

interface MissionBrief {
  mission_id?: string;
  status?: string;
  description?: string;
  created_at?: string;
}

export default function MissionsListPage() {
  const [rows, setRows] = useState<MissionBrief[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const raw = (await listMissions(0, 80)) as MissionBrief[];
        if (!cancelled) {
          setRows(Array.isArray(raw) ? raw : []);
          setLoading(false);
        }
      } catch (e) {
        if (!cancelled) {
          setErr(e instanceof Error ? e.message : "Não foi possível carregar os casos.");
          setLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="mx-auto max-w-6xl px-6 py-16">
      <header className="mb-10">
        <p className="text-xs uppercase tracking-widest text-gold-400/80">Diário EASY</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Casos</h1>
        <p className="mt-2 max-w-2xl text-sm text-white/60">
          Lista de casos com auditoria de IA registrada. Clique em qualquer item para inspecionar a
          cadeia HDR completa, evidências e relatório forense.
        </p>
      </header>

      {err ? (
        <div
          role="alert"
          className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-5 py-4 text-sm text-rose-200"
        >
          {err}
        </div>
      ) : null}

      {loading && !err ? (
        <p className="text-sm text-white/45" aria-live="polite">
          Carregando casos…
        </p>
      ) : null}

      {!loading && rows.length === 0 && !err ? (
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] px-8 py-12 text-center">
          <p className="text-base text-white/70">Você ainda não tem casos auditados.</p>
          <p className="mt-2 text-sm text-white/40">
            Comece pela ingestão de evidências em <Link href="/ingestion" className="text-gold-300 underline">/ingestion</Link>.
          </p>
        </div>
      ) : null}

      <ul className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {rows.map((m) =>
          m.mission_id ? (
            <li key={m.mission_id}>
              <Link
                prefetch={false}
                href={`/missions/${m.mission_id}`}
                className="group block rounded-2xl border border-white/10 bg-white/[0.02] p-5 transition hover:border-gold-400/40 hover:bg-white/[0.04] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-400/60"
              >
                <p className="font-mono text-[11px] text-gold-200/90" aria-label={`Identificador do caso ${m.mission_id}`}>
                  {m.mission_id}
                </p>
                <p className="mt-3 line-clamp-3 text-sm text-white/70">
                  {m.description || "Sem descrição."}
                </p>
                <p className="mt-4 text-[11px] uppercase tracking-wider text-white/40">
                  {m.status || "—"}
                </p>
              </Link>
            </li>
          ) : null,
        )}
      </ul>
    </section>
  );
}
