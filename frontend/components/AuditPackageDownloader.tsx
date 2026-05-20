"use client";

import { useState } from "react";

import { getBackendPublicUrl, generateForensicPackage, toAbsoluteHref } from "@/lib/api";

interface AuditDownloaderProps {
  missionId: string;
}

export function AuditPackageDownloader({ missionId }: AuditDownloaderProps) {
  const [packageId, setPackageId] = useState<string | null>(null);
  const [error, setError] = useState<string>("");

  const handleGenerate = async () => {
    setError("");
    try {
      const payload = await generateForensicPackage(missionId, "portal_cli");
      if (typeof payload === "object" && payload !== null && "package_id" in payload) {
        setPackageId(String((payload as { package_id?: string }).package_id));
      } else {
        setError("Resposta sem package_id.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falhou geração do pacote.");
    }
  };

  const pdfHref = packageId ? toAbsoluteHref(`/api/v1/forensic/package/${packageId}/download/pdf`) : null;
  const jsonHref = packageId ? toAbsoluteHref(`/api/v1/forensic/package/${packageId}/download/json`) : null;
  const manifestHref = packageId ? toAbsoluteHref(`/api/v1/forensic/package/${packageId}/download/manifest`) : null;

  return (
    <div className="rounded-xl border border-neutral-700 bg-neutral-900/70 p-4 text-sm">
      <h3 className="font-semibold text-neutral-100">Pacote forense</h3>
      <p className="mt-2 text-xs text-neutral-400">
        Gera resumo textual (stub PDF/A), manifesto JSON e cadeia de HDRs usando o novo domínio forense. Backend
        base:{" "}
        <span className="font-mono text-neutral-300" suppressHydrationWarning>
          {typeof window !== "undefined" ? getBackendPublicUrl() : "…"}
        </span>
      </p>
      <button
        type="button"
        className="mt-4 rounded-lg bg-indigo-500 px-3 py-2 text-xs font-semibold text-neutral-950 hover:bg-indigo-400"
        onClick={() => void handleGenerate()}
      >
        Gerar pacote para esta missão
      </button>
      {error ? <p className="mt-2 text-xs text-rose-400">{error}</p> : null}
      {packageId ? (
        <div className="mt-4 space-y-2 text-xs text-neutral-300">
          <p className="font-mono">{packageId}</p>
          <div className="flex flex-wrap gap-2">
            <a href={pdfHref ?? "#"} className="rounded border border-neutral-700 px-2 py-1 hover:bg-neutral-800">
              Stub executivo (.txt)
            </a>
            <a href={jsonHref ?? "#"} className="rounded border border-neutral-700 px-2 py-1 hover:bg-neutral-800">
              Chain JSON
            </a>
            <a href={manifestHref ?? "#"} className="rounded border border-neutral-700 px-2 py-1 hover:bg-neutral-800">
              Manifesto
            </a>
          </div>
        </div>
      ) : null}
    </div>
  );
}
