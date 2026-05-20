"use client";

import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";

export interface TimelineEvent {
  id: string;
  title: string;
  description: string;
  timestamp: string;
  status: "completed" | "failed" | "blocked" | "pending";
  agent: string;
  hdrId: string;
}

const statusTone: Record<TimelineEvent["status"], string> = {
  completed: "border-gold-500 bg-gold-500",
  failed: "border-rose-500 bg-rose-500",
  blocked: "border-amber-500 bg-amber-500",
  pending: "border-white/35 bg-transparent",
};

export function GlassTimeline({ events }: { events: TimelineEvent[] }) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <div className="relative">
      <div className="absolute bottom-4 left-[18px] top-4 w-px bg-gradient-to-b from-gold-400/85 via-white/15 to-transparent" />

      <div className="space-y-7">
        {events.map((event, index) => (
          <motion.div
            key={event.id}
            initial={{ opacity: 0, x: -18 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: "-30px" }}
            transition={{ delay: index * 0.06, duration: 0.5 }}
            className="relative pl-14"
          >
            <div
              className={`absolute left-3 top-[14px] h-5 w-5 -translate-x-1/2 rounded-full border-[3px] ${statusTone[event.status]}`}
            />

            <motion.div
              layout
              layoutId={`card-${event.id}`}
              role="button"
              tabIndex={0}
              onClick={() => setExpandedId(expandedId === event.id ? null : event.id)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") setExpandedId(expandedId === event.id ? null : event.id);
              }}
              className="glass-card glass-card-hover cursor-pointer border-white/15 p-5"
              data-cursor-hover
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="text-lg font-semibold text-white">{event.title}</h3>
                  <p className="mt-1 text-xs uppercase tracking-[0.15em] text-white/55">
                    {event.agent}
                    <span className="text-white/30"> • </span>
                    {(() => {
                      try {
                        return new Date(event.timestamp).toLocaleString("pt-PT");
                      } catch {
                        return event.timestamp;
                      }
                    })()}
                  </p>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-[11px] font-semibold ${
                    event.status === "completed"
                      ? "bg-gold-500/15 text-gold-300"
                      : event.status === "failed"
                        ? "bg-rose-500/15 text-rose-300"
                        : event.status === "blocked"
                          ? "bg-amber-500/15 text-amber-300"
                          : "bg-white/10 text-white/70"
                  }`}
                >
                  {event.status === "completed"
                    ? "Concluído"
                    : event.status === "failed"
                      ? "Falhou"
                      : event.status === "blocked"
                        ? "Bloqueado"
                        : "Pendente"}
                </span>
              </div>

              <AnimatePresence initial={false}>
                {expandedId === event.id && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.35 }}
                    className="overflow-hidden border-t border-white/10 pt-5"
                  >
                    <p className="mb-6 text-sm text-white/70">{event.description}</p>
                    {event.hdrId ? (
                      <>
                        <div className="flex flex-wrap items-center gap-2 text-xs">
                          <span className="text-white/45">HDR</span>
                          <code className="rounded-md bg-deep-space-800/95 px-2 py-1 font-mono text-gold-300">{event.hdrId}</code>
                          <button
                            type="button"
                            data-cursor-hover
                            className="text-white/55 transition hover:text-gold-400"
                            onClick={(e) => {
                              e.stopPropagation();
                              void navigator.clipboard?.writeText(event.hdrId).catch(() => {});
                            }}
                          >
                            copiar
                          </button>
                        </div>

                        <Link
                          href={`/verification?hdr=${encodeURIComponent(event.hdrId)}`}
                          data-cursor-hover
                          className="mt-4 inline-flex text-sm font-semibold text-gold-400 transition hover:text-gold-300"
                          onClick={(e) => e.stopPropagation()}
                        >
                          Verificar integridade →
                        </Link>
                      </>
                    ) : (
                      <p className="text-xs text-white/45">Ainda sem HDR — execute a missão para materializar prova on-chain local.</p>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
