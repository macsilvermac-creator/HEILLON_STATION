"use client";

import { useEffect, useMemo, useState } from "react";

import { GlassTimeline } from "@/components/GlassTimeline";
import { getDiary, getDiaryStats, getNormativeRules } from "@/lib/api";
import { buildTimelineEntries } from "@/lib/diary-mapper";

export default function DiaryPage() {
  const [snapshot, setSnapshot] = useState<unknown>(null);
  const [stats, setStats] = useState<unknown>(null);
  const [rulesPreview, setRulesPreview] = useState<unknown>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const [diaryResp, diaryStatsResp, corpus] = await Promise.all([
          getDiary({ limit: "20" }),
          getDiaryStats(),
          getNormativeRules(),
        ]);
        if (!ignore) {
          setSnapshot(diaryResp);
          setStats(diaryStatsResp);
          setRulesPreview(Array.isArray(corpus) ? corpus.slice(0, 5) : corpus);
        }
      } catch (err) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Diário indisponível.");
        }
      }
    })();
    return () => {
      ignore = true;
    };
  }, []);

  const missions =
    snapshot && typeof snapshot === "object" && snapshot !== null && "missions" in snapshot
      ? ((snapshot as { missions?: Record<string, unknown>[] }).missions ?? [])
      : [];

  const timeline = useMemo(() => buildTimelineEntries(missions), [missions]);

  return (
    <div className="mx-auto max-w-5xl space-y-10 px-4 pb-28 pt-36 sm:px-6">
      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-gold-500/85">Custódia operacional</p>
        <h1 className="text-4xl font-semibold tracking-tight text-white">Diário visual de missões</h1>
        <p className="max-w-2xl text-sm text-white/60">
          Dados vindos de <span className="font-mono text-[11px] text-white">GET /mission/diary</span> com filtros opcionais
          aplicados lado servidor.
        </p>
      </div>

      {error ? (
        <p className="text-sm text-rose-400">{error}</p>
      ) : (
        <div className="grid gap-5 lg:grid-cols-[1.05fr_minmax(0,0.82fr)]">
          <GlassTimeline events={timeline} />

          <div className="space-y-4">
            <div className="glass-card glass-card-hover p-5">
              <h2 className="text-sm font-semibold text-white/90">Métricas agregadas</h2>
              <pre className="mt-3 max-h-[220px] overflow-auto text-[11px] leading-relaxed text-white/60">
                {JSON.stringify(stats ?? {}, null, 2)}
              </pre>
            </div>
            <div className="glass-card glass-card-hover p-5">
              <h2 className="text-sm font-semibold text-white/90">Amostra do Corpus Normativo</h2>
              <pre className="mt-3 max-h-[220px] overflow-auto text-[11px] leading-relaxed text-white/60">
                {JSON.stringify(rulesPreview ?? {}, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
