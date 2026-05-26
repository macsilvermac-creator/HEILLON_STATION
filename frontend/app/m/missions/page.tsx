"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listMissions } from "@/lib/api";

interface Brief {
  mission_id?: string;
  status?: string;
  description?: string;
}

export default function MobileMissionsListPage() {
  const [rows, setRows] = useState<Brief[]>([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    let c = false;
    (async () => {
      try {
        const raw = (await listMissions(0, 40)) as Brief[];
        if (!c) setRows(Array.isArray(raw) ? raw : []);
      } catch (e) {
        if (!c) setErr(e instanceof Error ? e.message : "Sem acesso ao diário EASY.");
      }
    })();
    return () => {
      c = true;
    };
  }, []);

  return (
    <div className="px-5">
      <h1 className="text-lg font-semibold text-white">Casos</h1>
      <p className="mt-1 text-xs text-white/45">Toca para ver a cadeia de auditoria de IA do caso.</p>
      {err ? <p className="mt-4 text-xs text-rose-300">{err}</p> : null}
      <ul className="mt-8 space-y-2 pb-36">
        {rows.map((m) =>
          m.mission_id ? (
            <li key={m.mission_id}>
              <Link prefetch={false} href={`/m/missions/${m.mission_id}`} className="glass-elite block rounded-2xl px-5 py-4">
                <p className="font-mono text-[11px] text-gold-200/95">{m.mission_id}</p>
                <p className="mt-3 line-clamp-2 text-xs text-white/50">{m.description}</p>
                <p className="mt-2 text-[11px] uppercase tracking-wider text-white/35">{m.status}</p>
              </Link>
            </li>
          ) : null,
        )}
      </ul>
    </div>
  );
}
