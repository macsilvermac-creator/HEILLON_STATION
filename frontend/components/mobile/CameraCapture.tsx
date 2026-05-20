"use client";

import { useRef, useState } from "react";

import { postIngestFile } from "@/lib/api";

interface CameraCaptureProps {
  missionId?: string | null;
  onCaptured?: () => void;
}

export function CameraCapture({ missionId, onCaptured }: CameraCaptureProps) {
  const ref = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function onPick(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setBusy(true);
    setMsg(null);
    try {
      await postIngestFile(f, missionId ?? undefined);
      setMsg("Evidência ingerida com HDR ingestion.");
      onCaptured?.();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Erro ao ingerir.");
    } finally {
      setBusy(false);
      if (ref.current) ref.current.value = "";
    }
  }

  return (
    <div className="mt-8 space-y-3">
      <input
        ref={ref}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        id="camera-capture-hl"
        onChange={onPick}
      />
      <button
        type="button"
        disabled={busy}
        className="btn-glass w-full min-h-[52px]"
        onClick={() => ref.current?.click()}
      >
        {busy ? "A processar fotografia…" : "📷 Fotografar documento (ingestion)"}
      </button>
      {msg ? <p className="text-center text-xs text-white/50">{msg}</p> : null}
    </div>
  );
}
