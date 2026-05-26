"use client";

import { useEffect } from "react";
import Link from "next/link";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error("Heillon Legal: erro na rota", error);
  }, [error]);

  return (
    <div className="mx-auto max-w-3xl px-6 py-24 text-center">
      <p className="text-xs uppercase tracking-widest text-rose-300/80">Erro inesperado</p>
      <h1 className="mt-3 text-3xl font-semibold text-white">Algo saiu fora do roteiro.</h1>
      <p className="mt-4 text-sm text-white/60">
        Registrámos o incidente. Tente novamente ou volte para o painel principal.
      </p>
      {error.digest ? (
        <p className="mt-6 font-mono text-[11px] text-white/30">ref: {error.digest}</p>
      ) : null}
      <div className="mt-10 flex justify-center gap-3">
        <button
          type="button"
          onClick={reset}
          className="rounded-full border border-gold-400/40 bg-gold-400/10 px-5 py-2 text-sm font-medium text-gold-200 transition hover:bg-gold-400/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-400/60"
        >
          Tentar de novo
        </button>
        <Link
          href="/dashboard"
          className="rounded-full border border-white/15 px-5 py-2 text-sm text-white/70 transition hover:border-white/30 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40"
        >
          Voltar ao painel
        </Link>
      </div>
    </div>
  );
}
