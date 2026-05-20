"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import {
  fetchChainVerification,
  fetchHdrVerification,
} from "@/lib/api";

/** Public verification UX surface (RFC 3161 + digests without login). */

export function VerificationChecker() {
  const searchParams = useSearchParams();
  const [mode, setMode] = useState<"hdr" | "chain">("hdr");
  const [target, setTarget] = useState("");
  const [result, setResult] = useState<string>("");

  useEffect(() => {
    const hinted = searchParams.get("hdr") || searchParams.get("id") || "";
    const normalized = hinted.trim();
    if (normalized) {
      setMode("hdr");
      setTarget(normalized);
    }
  }, [searchParams]);

  const descriptor = useMemo(
    () => (mode === "hdr" ? "hash SHA-256 de 64 hex" : "identificador de missão"),
    [mode],
  );

  const handleVerify = async () => {
    if (!target.trim()) {
      setResult("Precisa de um identificador válido.");
      return;
    }
    try {
      const payload =
        mode === "hdr"
          ? await fetchHdrVerification(target.trim())
          : await fetchChainVerification(target.trim());

      setResult(JSON.stringify(payload, null, 2));
    } catch (error) {
      setResult(error instanceof Error ? error.message : "Erro de rede/API.");
    }
  };

  return (
    <div className="space-y-6 rounded-xl border border-neutral-800 bg-neutral-900/70 p-4">
      <div className="flex gap-6 text-xs">
        <label className="flex gap-2">
          <input type="radio" checked={mode === "hdr"} onChange={() => setMode("hdr")} /> HDR único
        </label>
        <label className="flex gap-2">
          <input type="radio" checked={mode === "chain"} onChange={() => setMode("chain")} />
          Missão inteira
        </label>
      </div>

      <label className="block space-y-2 text-sm">
        <span>Identificador ({descriptor})</span>
        <input
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          className="w-full rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 font-mono text-xs outline-none ring-blue-600/70 focus-visible:ring-2"
          placeholder={mode === "hdr" ? "64 hex lowercase" : "mission_xxx"}
        />
      </label>

      <button
        type="button"
        onClick={handleVerify}
        className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-amber-400"
      >
        Validar custódia
      </button>

      {result ? (
        <pre className="max-h-[520px] overflow-auto rounded-lg border border-neutral-800 bg-neutral-950 p-4 text-[11px] text-neutral-200">
          {result}
        </pre>
      ) : null}
    </div>
  );
}
