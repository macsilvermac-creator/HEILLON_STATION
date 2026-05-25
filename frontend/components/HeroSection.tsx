"use client";

import dynamic from "next/dynamic";
import { useRef, useState } from "react";
import { motion, useMotionValueEvent, useScroll, useTransform } from "framer-motion";

const Hero3DScene = dynamic(
  () => import("./Hero3DScene").then((m) => ({ default: m.Hero3DScene })),
  {
    ssr: false,
    loading: () => (
      <div className="pointer-events-none absolute inset-0 z-0 bg-gradient-to-br from-deep-space-900 to-black" />
    ),
  }
);

export function HeroSection() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollScalar, setScrollScalar] = useState(0);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end start"],
  });

  useMotionValueEvent(scrollYProgress, "change", (latest) => {
    setScrollScalar(latest);
  });

  const opacity = useTransform(scrollYProgress, [0, 0.85], [1, 0.15]);
  const scale = useTransform(scrollYProgress, [0, 1], [1, 0.94]);
  const y = useTransform(scrollYProgress, [0, 1], [0, 96]);

  return (
    <div ref={containerRef} className="relative h-[min(100vh,940px)] overflow-hidden pt-36">
      <div className="hidden lg:block">
        <Hero3DScene scrollProgress={scrollScalar} />
      </div>
      <div className="absolute inset-0 z-[1] bg-gradient-to-br from-deep-space-800 via-deep-space-900 to-black lg:bg-transparent" />

      <motion.div style={{ opacity, scale, y }} className="relative z-10 flex min-h-[60vh] flex-col items-center justify-center px-6 text-center lg:min-h-[70vh]">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15, duration: 0.75 }}
          className="glass-card mb-8 inline-flex items-center gap-2 px-6 py-2"
        >
          <span className="h-2 w-2 animate-pulse rounded-full bg-gold-500 shadow-lg shadow-gold-500/30" />
          <span className="text-sm text-white/80">Soberania de modelo · Custódia criptográfica HDR</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 34 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25, duration: 0.8 }}
          className="section-title max-w-4xl"
        >
          Cada decisão da IA, imutável e verificável
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.8 }}
          className="mt-6 max-w-2xl text-base text-white/60 md:text-lg"
        >
          Plataforma com cadeia de custódia algorítmica, diário forensic-grade e espaço público para provar integridade —
          incluindo o seu modelo soberano por agente.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.55, duration: 0.8 }}
          className="mt-10 flex flex-col gap-4 sm:flex-row"
        >
          <a href="/ingestion" data-cursor-hover className="btn-gold text-center">
            Começar missão
          </a>
          <a href="/verification" data-cursor-hover className="btn-glass text-center">
            Verificar prova
          </a>
        </motion.div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.1, duration: 0.8 }}
        className="pointer-events-none absolute bottom-10 left-1/2 z-10 hidden -translate-x-1/2 md:block"
      >
        <div className="flex h-11 w-6 items-start justify-center rounded-full border-2 border-white/15 py-2">
          <motion.div
            className="h-3 w-[3px] rounded-full bg-gold-500"
            animate={{ y: [0, 10, 0] }}
            transition={{ repeat: Infinity, duration: 2.15, ease: "easeInOut" }}
          />
        </div>
      </motion.div>
    </div>
  );
}
