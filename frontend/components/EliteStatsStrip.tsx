"use client";

import Link from "next/link";
import { motion } from "framer-motion";

const metrics = [
  { label: "Soberania de modelo", hint: "Ollama • OpenAI • Anthropic • API compatível" },
  { label: "Custódia criptográfica", hint: "HDR encadeadas com verificação pública" },
  { label: "Forensic-grade", hint: "PDF executivo assinável + manifests Ed25519" },
];

export function EliteStatsStrip() {
  return (
    <section className="relative z-10 mx-auto -mt-8 max-w-6xl px-5">
      <div className="grid gap-4 md:grid-cols-3">
        {metrics.map((item, index) => (
          <motion.div
            key={item.label}
            initial={{ opacity: 0, y: 26 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ delay: index * 0.12, duration: 0.6 }}
            className="glass-card glass-card-hover p-5 text-left"
          >
            <div className="text-lg font-semibold text-white">{item.label}</div>
            <p className="mt-2 text-sm text-white/55">{item.hint}</p>
            <div className="mt-6 h-px w-full bg-white/10" />
            <Link href="/agent-config" className="mt-4 inline-flex text-xs font-semibold text-gold-400" data-cursor-hover>
              Configurar modelos →
            </Link>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
