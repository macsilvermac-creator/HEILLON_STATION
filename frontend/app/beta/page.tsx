"use client";

/**
 * /beta — Landing pública de convite ao beta freemium (Fase 32).
 *
 * Página de divulgação fora do chrome do console (ver ConditionalAppShell):
 * traz seu próprio header e footer. Mantém a identidade visual da UI
 * (glass-card, tokens gold, Hero3DScene) para criar afinidade imediata com
 * o produto. CTA principal leva a /register; secundário a /login.
 *
 * Sem preços/planos: o programa é freemium durante o beta privado. A oferta
 * comercial fica para pós-CNPJ.
 */

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import {
  motion,
  useMotionValueEvent,
  useScroll,
  useTransform,
} from "framer-motion";

const Hero3DScene = dynamic(
  () => import("@/components/Hero3DScene").then((m) => ({ default: m.Hero3DScene })),
  {
    ssr: false,
    loading: () => (
      <div className="pointer-events-none absolute inset-0 z-0 bg-gradient-to-br from-deep-space-900 to-black" />
    ),
  }
);

const PILLARS: { title: string; body: string }[] = [
  {
    title: "Cadeia de custódia que vale em juízo",
    body: "Cada decisão da IA vira um HDR imutável — encadeado por SHA-256, selado com timestamp RFC 3161. Prova técnica de integridade, não promessa.",
  },
  {
    title: "Invisível no uso",
    body: "A captura roda em segundo plano via extensão ou gateway. Você trabalha como sempre; o registro forense se forma sozinho.",
  },
  {
    title: "Soberania de modelo",
    body: "Escolha o provedor e o modelo por agente. O Heillon audita o que foi usado, sem amarrar você a um fornecedor.",
  },
  {
    title: "Verificação pública",
    body: "Qualquer parte pode conferir a prova de integridade de um registro sem acessar o conteúdo sensível.",
  },
];

const STEPS: { n: string; title: string; body: string }[] = [
  {
    n: "01",
    title: "Crie sua conta",
    body: "Cadastro em minutos. Acesso freemium durante o beta privado, sem cartão.",
  },
  {
    n: "02",
    title: "Conecte um coletor",
    body: "Instale a extensão Chrome ou aponte o gateway de API. A captura começa na hora.",
  },
  {
    n: "03",
    title: "Gere provas verificáveis",
    body: "Cada uso de IA produz um HDR auditável — pronto para conformidade e para juízo.",
  },
];

function LandingHeader() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-colors ${
        scrolled
          ? "border-b border-white/10 bg-deep-space-900/85 backdrop-blur"
          : "border-b border-transparent"
      }`}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
        <a href="/beta" className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-gold-500 shadow-lg shadow-gold-500/30" />
          <span className="text-sm font-semibold uppercase tracking-[0.22em] text-white">
            Heillon <span className="text-gold-400">Legal</span>
          </span>
        </a>
        <nav className="flex items-center gap-3 text-sm">
          <a
            href="/login"
            className="rounded-md px-3 py-1.5 text-white/70 transition hover:text-white"
          >
            Entrar
          </a>
          <a href="/register" className="btn-gold px-4 py-1.5 text-sm">
            Participar do beta
          </a>
        </nav>
      </div>
    </header>
  );
}

function LandingHero() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollScalar, setScrollScalar] = useState(0);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end start"],
  });
  useMotionValueEvent(scrollYProgress, "change", (v) => setScrollScalar(v));

  const opacity = useTransform(scrollYProgress, [0, 0.85], [1, 0.15]);
  const scale = useTransform(scrollYProgress, [0, 1], [1, 0.94]);
  const y = useTransform(scrollYProgress, [0, 1], [0, 96]);

  return (
    <div
      ref={containerRef}
      className="relative h-[min(100vh,940px)] overflow-hidden pt-36"
    >
      <div className="hidden lg:block">
        <Hero3DScene scrollProgress={scrollScalar} />
      </div>
      <div className="absolute inset-0 z-[1] bg-gradient-to-br from-deep-space-800 via-deep-space-900 to-black lg:bg-transparent" />

      <motion.div
        style={{ opacity, scale, y }}
        className="relative z-10 flex min-h-[60vh] flex-col items-center justify-center px-6 text-center lg:min-h-[70vh]"
      >
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15, duration: 0.75 }}
          className="glass-card mb-8 inline-flex items-center gap-2 px-6 py-2"
        >
          <span className="h-2 w-2 animate-pulse rounded-full bg-gold-500 shadow-lg shadow-gold-500/30" />
          <span className="text-sm text-white/80">
            Beta privado · Acesso freemium para advogados
          </span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 34 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25, duration: 0.8 }}
          className="section-title max-w-4xl"
        >
          Prove a integridade de cada decisão da sua IA
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.8 }}
          className="mt-6 max-w-2xl text-base text-white/60 md:text-lg"
        >
          O Heillon Legal registra cada uso de IA no seu trabalho jurídico e o
          transforma em prova imutável — cadeia de custódia criptográfica que
          vale em juízo, invisível no dia a dia. Participe do beta sem custo.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.55, duration: 0.8 }}
          className="mt-10 flex flex-col gap-4 sm:flex-row"
        >
          <a href="/register" className="btn-gold text-center">
            Criar conta gratuita
          </a>
          <a href="/login" className="btn-glass text-center">
            Já tenho conta
          </a>
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8, duration: 0.8 }}
          className="mt-5 text-xs text-white/40"
        >
          Sem cartão de crédito · Cancele quando quiser
        </motion.p>
      </motion.div>
    </div>
  );
}

export default function BetaLandingPage() {
  return (
    <div className="relative min-h-screen bg-deep-space-900 text-white">
      <LandingHeader />
      <LandingHero />

      {/* Pilares de valor */}
      <section className="mx-auto max-w-6xl px-5 py-20">
        <div className="mb-10 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-gold-500/85">
            Por que o Heillon
          </p>
          <h2 className="mt-2 text-3xl font-semibold text-white">
            Substrato forense para a IA no Direito
          </h2>
        </div>
        <div className="grid gap-5 sm:grid-cols-2">
          {PILLARS.map((p) => (
            <div key={p.title} className="glass-card glass-card-hover p-7">
              <h3 className="text-lg font-semibold text-white">{p.title}</h3>
              <p className="mt-3 text-sm text-white/60">{p.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Como funciona */}
      <section className="mx-auto max-w-6xl px-5 pb-20">
        <div className="mb-10 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-gold-500/85">
            Como começar
          </p>
          <h2 className="mt-2 text-3xl font-semibold text-white">
            Do cadastro à primeira prova em minutos
          </h2>
        </div>
        <div className="grid gap-5 md:grid-cols-3">
          {STEPS.map((s) => (
            <div key={s.n} className="glass-card p-7">
              <p className="text-3xl font-bold text-gold-400/80">{s.n}</p>
              <h3 className="mt-3 text-lg font-semibold text-white">{s.title}</h3>
              <p className="mt-2 text-sm text-white/60">{s.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA final */}
      <section className="mx-auto max-w-4xl px-5 pb-24">
        <div className="glass-card glass-card-hover p-10 text-center lg:p-14">
          <h2 className="text-3xl font-semibold text-white">
            Garanta sua vaga no beta privado
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-sm text-white/60">
            Estamos abrindo acesso a um grupo limitado de advogados e equipes
            jurídicas. Acesso freemium, suporte direto do time de produto e voz
            ativa no que o Heillon se torna.
          </p>
          <div className="mt-8 flex flex-col justify-center gap-4 sm:flex-row">
            <a href="/register" className="btn-gold text-center">
              Participar do beta
            </a>
            <a href="/login" className="btn-glass text-center">
              Entrar
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-5 py-8 text-xs text-white/40 sm:flex-row">
          <span>
            © {new Date().getFullYear()} Heillon Legal · Substrato de auditoria
            forense para IA
          </span>
          <nav className="flex items-center gap-4">
            <a href="/privacy" className="transition hover:text-white/70">
              Privacidade
            </a>
            <a href="/docs" className="transition hover:text-white/70">
              Documentação
            </a>
            <a href="/login" className="transition hover:text-white/70">
              Entrar
            </a>
          </nav>
        </div>
      </footer>
    </div>
  );
}
