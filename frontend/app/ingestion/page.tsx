"use client";

import { EvidenceUploader } from "@/components/EvidenceUploader";

export default function IngestionPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-9 pb-32 pt-36">
      <div>
        <h1 className="text-gradient text-3xl font-semibold tracking-tight">Enviar documentos</h1>
        <p className="mt-2 max-w-2xl text-sm text-white/60">
          Cada documento enviado recebe um registo de custódia imutável com hash SHA-256 e carimbo temporal RFC 3161.
        </p>
      </div>
      <EvidenceUploader />
    </div>
  );
}
