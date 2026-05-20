"use client";

import { motion, type PanInfo } from "framer-motion";
import { useState } from "react";

interface SwipeApprovalProps {
  onApprove: () => Promise<void>;
  onReject: () => Promise<void>;
}

export function SwipeApproval({ onApprove, onReject }: SwipeApprovalProps) {
  const [busy, setBusy] = useState(false);

  async function finalize(offsetX: number) {
    setBusy(true);
    try {
      navigator.vibrate?.(18);
      if (offsetX > 140) await onApprove();
      else if (offsetX < -140) await onReject();
    } finally {
      setBusy(false);
    }
  }

  function handleDragEnd(_e: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) {
    if (Math.abs(info.offset.x) > 140) {
      void finalize(info.offset.x);
    }
  }

  return (
    <div className="relative mx-auto mt-10 w-full max-w-md pb-36">
      <motion.div
        drag="x"
        dragElastic={0.55}
        dragConstraints={{ left: 0, right: 0 }}
        onDragEnd={handleDragEnd}
        style={{ touchAction: "none" }}
        className={`glass-elite cursor-grab rounded-[2rem] px-8 py-16 text-center active:cursor-grabbing ${busy ? "opacity-65" : ""}`}
      >
        <p className="text-sm uppercase tracking-[0.3em] text-white/35">Gestos rápidos</p>
        <p className="mt-8 text-xl font-semibold text-white">
          Direita · <span className="text-emerald-300">aprovar</span>
        </p>
        <p className="mt-3 text-lg text-white/60">
          Esquerda · <span className="text-rose-300">rejeitar</span>
        </p>
        <p className="mt-12 text-[11px] text-white/30">Reposicione lentamente até ver o resultado — ou use os botões.</p>
      </motion.div>

      <div className="mt-8 grid grid-cols-2 gap-3">
        <button
          type="button"
          disabled={busy}
          className="min-h-[48px] rounded-2xl border border-rose-500/35 bg-rose-500/10 py-4 text-xs font-semibold text-rose-200"
          onClick={() => finalize(-240)}
        >
          Rejeitar
        </button>
        <button
          type="button"
          disabled={busy}
          className="min-h-[48px] rounded-2xl border border-emerald-500/40 bg-emerald-500/15 py-4 text-xs font-semibold text-emerald-100"
          onClick={() => finalize(240)}
        >
          Aprovar
        </button>
      </div>
    </div>
  );
}
