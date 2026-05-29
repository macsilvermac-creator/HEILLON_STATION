"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { mintApiKey, type ApiKeyMintResponse } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const EXTENSION_CHROME_URL =
  process.env.NEXT_PUBLIC_CHROME_EXTENSION_URL ?? "https://chrome.google.com/webstore";

type StepKey = "welcome" | "key" | "extension";

const STEP_ORDER: StepKey[] = ["welcome", "key", "extension"];

const STEP_LABELS: Record<StepKey, string> = {
  welcome: "Bem-vindo",
  key: "Chave de API",
  extension: "Coletor",
};

export default function OnboardingPage() {
  const router = useRouter();
  const { user, isReady } = useAuth();
  const [step, setStep] = useState<StepKey>("welcome");
  const [minted, setMinted] = useState<ApiKeyMintResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (isReady && !user) router.push("/login?from=/conta/onboarding");
  }, [isReady, user, router]);

  const currentIdx = STEP_ORDER.indexOf(step);

  const handleMint = async () => {
    setBusy(true);
    setErr(null);
    try {
      const result = await mintApiKey("Onboarding — primeira chave");
      setMinted(result);
      setStep("extension");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Falha ao gerar chave.");
    } finally {
      setBusy(false);
    }
  };

  const handleFinish = () => {
    try {
      localStorage.setItem("heillon_onboarding_complete", new Date().toISOString());
    } catch {
      /* ignore */
    }
    router.push("/dashboard");
  };

  if (!isReady || !user) {
    return (
      <section className="mx-auto max-w-3xl px-6 py-24 text-center text-sm text-white/45">
        Carregando…
      </section>
    );
  }

  return (
    <section className="mx-auto max-w-3xl px-6 py-16">
      <header className="mb-10">
        <p className="text-xs uppercase tracking-widest text-gold-400/80">Configuração inicial</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">
          Olá, {user.name.split(" ")[0] || "operador"}. Em 3 passos seu Heillon está pronto.
        </h1>
      </header>

      {/* Stepper */}
      <nav aria-label="Progresso do onboarding" className="mb-10">
        <ol className="flex items-center justify-between text-xs">
          {STEP_ORDER.map((key, idx) => {
            const active = idx <= currentIdx;
            const isNow = idx === currentIdx;
            return (
              <li key={key} className="flex flex-1 items-center gap-3">
                <span
                  className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-[11px] font-semibold ${
                    active
                      ? "border-gold-400/60 bg-gold-400/15 text-gold-200"
                      : "border-white/15 bg-white/[0.02] text-white/35"
                  } ${isNow ? "ring-2 ring-gold-400/40" : ""}`}
                >
                  {idx + 1}
                </span>
                <span className={active ? "text-white" : "text-white/40"}>
                  {STEP_LABELS[key]}
                </span>
                {idx < STEP_ORDER.length - 1 ? (
                  <span className={`mx-2 h-px flex-1 ${active ? "bg-gold-400/30" : "bg-white/10"}`} />
                ) : null}
              </li>
            );
          })}
        </ol>
      </nav>

      {err ? (
        <div role="alert" className="mb-6 rounded-xl border border-rose-500/40 bg-rose-500/10 px-5 py-4 text-sm text-rose-200">
          {err}
        </div>
      ) : null}

      {/* Step content */}
      {step === "welcome" ? (
        <article className="rounded-2xl border border-white/10 bg-white/[0.02] p-8">
          <h2 className="text-xl font-semibold text-white">O que o Heillon faz por você</h2>
          <p className="mt-3 text-sm leading-relaxed text-white/75">
            O Heillon Legal é o <strong>substrato de auditoria de IA jurídica</strong>: cada vez
            que você usa ChatGPT, Claude, Gemini ou outra IA no trabalho, geramos um{" "}
            <strong>HDR (Registro de Auditoria)</strong> assinado com timestamp criptográfico
            RFC 3161 e cadeia de custódia íntegra — com arquitetura pronta para o selo
            ICP-Brasil qualificado.
          </p>
          <ul className="mt-6 space-y-2 text-sm text-white/70">
            <li className="flex items-start gap-2">
              <span className="text-gold-400">✓</span> Cadeia de custódia criptográfica SHA-256
            </li>
            <li className="flex items-start gap-2">
              <span className="text-gold-400">✓</span> Validação contra corpus normativo brasileiro
              (LGPD, CNJ, OAB, CPC, CPP, CLT, Marco Civil)
            </li>
            <li className="flex items-start gap-2">
              <span className="text-gold-400">✓</span> 50 HDRs por mês grátis · upgrade quando precisar
            </li>
          </ul>
          <button
            type="button"
            onClick={() => setStep("key")}
            className="mt-8 rounded-xl bg-gold-400 px-5 py-3 text-sm font-medium text-deep-space-900 transition hover:bg-gold-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-400/60"
          >
            Próximo →
          </button>
        </article>
      ) : null}

      {step === "key" ? (
        <article className="rounded-2xl border border-white/10 bg-white/[0.02] p-8">
          <h2 className="text-xl font-semibold text-white">Gere sua chave de API</h2>
          <p className="mt-3 text-sm leading-relaxed text-white/75">
            A chave conecta a Extensão do Browser (e qualquer outro coletor) à sua conta.
            Vamos criar uma agora — você pode revogar e gerar mais a qualquer momento em{" "}
            <Link href="/conta/api-keys" className="text-gold-300 underline">
              Chaves de API
            </Link>
            .
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={handleMint}
              disabled={busy}
              className="rounded-xl bg-gold-400 px-5 py-3 text-sm font-medium text-deep-space-900 transition hover:bg-gold-300 disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-400/60"
            >
              {busy ? "Gerando…" : "Gerar minha chave"}
            </button>
            <button
              type="button"
              onClick={() => setStep("extension")}
              className="rounded-xl border border-white/15 px-5 py-3 text-sm text-white/75 transition hover:border-white/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40"
            >
              Pular — faço depois
            </button>
          </div>
        </article>
      ) : null}

      {step === "extension" ? (
        <article className="rounded-2xl border border-white/10 bg-white/[0.02] p-8">
          <h2 className="text-xl font-semibold text-white">Instale a Extensão do Browser</h2>
          {minted ? (
            <div className="mt-4 rounded-xl border border-gold-400/30 bg-gold-400/[0.06] p-4">
              <p className="text-xs text-gold-200/85">Sua chave (copie agora — não será mostrada de novo):</p>
              <code className="mt-2 block overflow-x-auto whitespace-nowrap font-mono text-xs text-gold-100">
                {minted.plaintext_key}
              </code>
              <button
                type="button"
                onClick={() => navigator.clipboard?.writeText(minted.plaintext_key)}
                className="mt-2 text-xs text-gold-200/80 underline-offset-4 hover:underline focus-visible:outline-none"
              >
                Copiar chave
              </button>
            </div>
          ) : null}
          <p className="mt-6 text-sm leading-relaxed text-white/75">
            A extensão observa quando você usa ChatGPT/Claude/Gemini e gera HDRs em background.
            Você continua trabalhando normalmente — o Heillon cuida do registro.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <a
              href={EXTENSION_CHROME_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-xl bg-gold-400 px-5 py-3 text-sm font-medium text-deep-space-900 transition hover:bg-gold-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-400/60"
            >
              Instalar Extensão Chrome →
            </a>
            <button
              type="button"
              onClick={handleFinish}
              className="rounded-xl border border-white/15 px-5 py-3 text-sm text-white/75 transition hover:border-white/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40"
            >
              Concluir e ir para o painel
            </button>
          </div>
        </article>
      ) : null}
    </section>
  );
}
