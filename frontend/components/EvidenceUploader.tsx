"use client";

import { useState } from "react";

import { postIngestFile } from "@/lib/api";

export function EvidenceUploader() {
  const [missionId, setMissionId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>("");

  const handleUpload = async () => {
    if (!file) {
      setStatus("Selecione um ficheiro.");
      return;
    }
    try {
      setStatus("A enviar…");
      const payload = await postIngestFile(file, missionId || undefined);
      setStatus(JSON.stringify(payload, null, 2));
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Erro desconhecido.");
    }
  };

  return (
    <div className="space-y-4 rounded-xl border border-neutral-800 bg-neutral-900/70 p-4">
      <div className="grid gap-3 md:grid-cols-2">
        <label className="space-y-1 text-sm">
          <span>Mission ID (opcional)</span>
          <input
            value={missionId}
            onChange={(e) => setMissionId(e.target.value)}
            className="w-full rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm outline-none ring-blue-600/70 focus-visible:ring-2"
            placeholder="mission_demo_01"
          />
        </label>
        <label className="space-y-1 text-sm">
          <span>Ficheiro</span>
          <input
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="block w-full text-xs text-neutral-400 file:rounded-md file:border-0 file:bg-blue-700 file:px-3 file:py-2 file:text-xs file:text-white"
          />
        </label>
      </div>

      <button
        type="button"
        onClick={handleUpload}
        className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500"
      >
        Emitir HDR de ingestão
      </button>

      {status ? <p className="text-xs text-neutral-400">{status}</p> : null}
    </div>
  );
}
