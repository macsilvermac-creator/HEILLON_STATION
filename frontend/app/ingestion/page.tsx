"use client";

import { EvidenceUploader } from "@/components/EvidenceUploader";

export default function IngestionPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-9 pb-32 pt-36">
      <div>
        <h1 className="text-gradient text-3xl font-semibold tracking-tight">Ingresso de evidências</h1>
        <p className="mt-2 max-w-2xl text-sm text-white/60">
          Envio inicial gera HDR de ingestão assinando SHA-256 do ficheiro e carimbo de tempo de confiança.
        </p>
      </div>
      <EvidenceUploader />
    </div>
  );
}
