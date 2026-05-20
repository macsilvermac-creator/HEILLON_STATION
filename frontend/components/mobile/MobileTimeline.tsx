"use client";

import { motion } from "framer-motion";
import { useState } from "react";

interface MobileTimelineProps {
  hdrIds: string[];
  chainValid?: boolean | null;
}

export function MobileTimeline({ hdrIds, chainValid }: MobileTimelineProps) {
  const [open, setOpen] = useState<number | null>(null);

  if (!hdrIds.length) {
    return <p className="text-xs text-white/45">Sem HDRs associados nesta vista.</p>;
  }

  return (
    <div className="relative">
      <div className="mb-6 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-xs text-white/60">
        Cadeia pública:&nbsp;
        <span className={`font-semibold ${chainValid ? "text-emerald-400" : "text-amber-200"}`}>
          {chainValid === null || chainValid === undefined ? "—" : chainValid ? "válida" : "precisa revisão"}
        </span>
      </div>

      <div className="absolute bottom-10 left-[11px] top-14 w-[2px] bg-gradient-to-b from-gold-500/85 via-white/25 to-transparent" />

      <div className="space-y-5">
        {hdrIds.map((id, idx) => {
          const expanded = open === idx;
          return (
            <motion.div
              key={`${id}-${idx}`}
              layout
              className="relative pl-11"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="absolute left-[6px] top-4 h-[10px] w-[10px] rounded-full border-2 border-gold-400 bg-deep-space-900" />
              <button
                type="button"
                onClick={() => setOpen(expanded ? null : idx)}
                className="glass-elite block w-full rounded-xl px-4 py-3 text-left md:min-h-[48px]"
              >
                <p className="text-[11px] uppercase tracking-wider text-gold-400/90">HDR #{idx + 1}</p>
                <p className="mt-2 font-mono text-[10px] leading-relaxed text-white/70">{id}</p>
              </button>
              {expanded ? (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  className="mt-3 overflow-hidden rounded-lg border border-white/10 bg-white/[0.02] px-3 py-2 text-[11px] text-white/55"
                >
                  Use “Verificar” para validar hashes e marca temporal Trusted TSA.
                </motion.div>
              ) : null}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
