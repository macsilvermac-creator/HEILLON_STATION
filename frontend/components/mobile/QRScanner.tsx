"use client";

import { Html5Qrcode } from "html5-qrcode";
import { useEffect, useId, useRef, useState } from "react";

interface QRScannerProps {
  onDecoded: (hdrId: string) => void;
  onClose?: () => void;
}

export function normalizeHdrCandidate(raw: string): string | null {
  const t = raw.trim();
  const m = t.match(/[0-9a-f]{64}/i);
  if (m) return m[0].toLowerCase();
  try {
    const u = new URL(t, typeof window !== "undefined" ? window.location.origin : "https://heillon.local");
    const parts = u.pathname.split("/").filter(Boolean);
    const idx = parts.findIndex((p) => p.toLowerCase() === "verify");
    if (idx >= 0 && parts[idx + 1] && /^[0-9a-f]{64}$/i.test(parts[idx + 1])) return parts[idx + 1].toLowerCase();
  } catch {
    /* noop */
  }
  return null;
}

export function QRScannerOverlay({ onDecoded, onClose }: QRScannerProps) {
  const uid = useId().replace(/:/g, "");
  const regionEl = `mobile-qr-${uid}`;
  const [msg, setMsg] = useState("A iniciar câmara…");
  const camRef = useRef<Html5Qrcode | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function boot() {
      try {
        const mod = await import("html5-qrcode");
        if (cancelled) return;

        const cam = new mod.Html5Qrcode(regionEl, false);
        camRef.current = cam;

        await cam.start(
          { facingMode: "environment" },
          {
            fps: 10,
            qrbox: () => ({
              width: Math.min(Math.floor(window.innerWidth * 0.84), 300),
              height: Math.min(Math.floor(window.innerWidth * 0.84), 300),
            }),
          },
          (decoded) => {
            const hdr = normalizeHdrCandidate(decoded);
            if (hdr && camRef.current) {
              camRef.current
                .stop()
                .then(() => {
                  onDecoded(hdr);
                  onClose?.();
                })
                .catch(() => {
                  /* ignore duplicate stop */
                });
            }
          },
          undefined,
        );
        setMsg("Aponte para o código QR ou URL HDR.");
      } catch (err) {
        setMsg(err instanceof Error ? err.message : "Erro ao abrir câmara.");
      }
    }

    boot();
    return () => {
      cancelled = true;
      if (camRef.current) {
        camRef.current
          .stop()
          .catch(() => {
            /* already stopped */
          })
          .finally(() => {
            camRef.current = null;
          });
      }
    };
  }, [onDecoded, onClose, regionEl]);

  return (
    <div className="fixed inset-0 z-[200] bg-black/88 backdrop-blur-md">
      <div className="flex h-full flex-col pt-safe-mobile">
        <div className="flex items-center justify-between px-6 py-5">
          <p className="text-sm font-medium text-white/80">Digitalizar HDR</p>
          <button
            type="button"
            className="min-h-[48px] min-w-[48px] rounded-full border border-white/20 px-5 text-xs text-white/75"
            onClick={async () => {
              await camRef.current?.stop?.().catch(() => undefined);
              onClose?.();
            }}
          >
            Fechar
          </button>
        </div>
        <div className="flex flex-1 flex-col items-center px-5">
          <div id={regionEl} className="w-full max-w-md overflow-hidden rounded-2xl border border-gold-500/35" />
          <p className="mt-6 max-w-xs text-center text-[11px] text-white/50">{msg}</p>
        </div>
      </div>
    </div>
  );
}
