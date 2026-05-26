import Link from "next/link";

export const metadata = {
  title: "Página não encontrada · Heillon Legal",
};

export default function NotFound() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-24 text-center">
      <p className="text-xs uppercase tracking-widest text-gold-400/80">404</p>
      <h1 className="mt-3 text-3xl font-semibold text-white">Esta rota não existe.</h1>
      <p className="mt-4 text-sm text-white/60">
        A URL que você digitou não corresponde a nenhuma página da plataforma.
      </p>
      <div className="mt-10 flex justify-center gap-3">
        <Link
          href="/"
          className="rounded-full border border-gold-400/40 bg-gold-400/10 px-5 py-2 text-sm font-medium text-gold-200 transition hover:bg-gold-400/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-400/60"
        >
          Página inicial
        </Link>
        <Link
          href="/docs"
          className="rounded-full border border-white/15 px-5 py-2 text-sm text-white/70 transition hover:border-white/30 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40"
        >
          Documentação
        </Link>
      </div>
    </div>
  );
}
