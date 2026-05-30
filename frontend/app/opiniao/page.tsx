"use client";

/**
 * /opiniao — Pesquisa de opinião do beta (Fase 32).
 *
 * Captura, dentro do próprio sistema, a avaliação do operador em quatro eixos
 * (usabilidade, experiência, funcionalidades e "entrega o que promete"), além
 * de NPS, intenção de adoção e texto livre. Submete para POST /feedback
 * autenticado pelo cookie de sessão. Sem PII de terceiros — é a opinião do
 * próprio usuário sobre o produto.
 */

import { useState } from "react";

import {
  submitBetaFeedback,
  type FeedbackSubmission,
} from "@/lib/api";

const SCALE = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10] as const;

const ADOPT_OPTIONS: { value: string; label: string }[] = [
  { value: "now", label: "Sim, em até 30 dias" },
  { value: "3-6m", label: "Sim, em 3–6 meses" },
  { value: "12m", label: "Sim, em 12+ meses" },
  { value: "depends", label: "Depende de ajustes" },
  { value: "no", label: "Não adotaria" },
];

interface AxisDef {
  key: "usability" | "experience" | "functionality" | "delivers" | "nps";
  title: string;
  hint: string;
  low: string;
  high: string;
}

const AXES: AxisDef[] = [
  {
    key: "usability",
    title: "Usabilidade",
    hint: "Quão fácil foi operar o Heillon no seu fluxo de trabalho?",
    low: "Difícil",
    high: "Intuitivo",
  },
  {
    key: "experience",
    title: "Experiência",
    hint: "Como foi sua experiência geral com a plataforma?",
    low: "Frustrante",
    high: "Excelente",
  },
  {
    key: "functionality",
    title: "Funcionalidades",
    hint: "As funcionalidades atendem o que você precisa no seu trabalho jurídico?",
    low: "Faltam coisas",
    high: "Completo",
  },
  {
    key: "delivers",
    title: "Entrega o que promete",
    hint: "Cadeia de custódia que vale em juízo, invisível no uso — o Heillon cumpre?",
    low: "Não cumpre",
    high: "Cumpre",
  },
  {
    key: "nps",
    title: "Recomendação",
    hint: "Quanto você recomendaria o Heillon a um(a) colega em situação parecida?",
    low: "Jamais",
    high: "Com certeza",
  },
];

function ScaleRow({
  axis,
  value,
  onChange,
}: {
  axis: AxisDef;
  value: number | null;
  onChange: (v: number) => void;
}) {
  return (
    <fieldset className="rounded-xl border border-white/10 bg-white/5 p-5">
      <legend className="px-1 text-sm font-semibold text-white">{axis.title}</legend>
      <p className="mb-3 text-xs text-white/55">{axis.hint}</p>
      <div className="flex flex-wrap gap-1.5" role="radiogroup" aria-label={axis.title}>
        {SCALE.map((n) => {
          const selected = value === n;
          return (
            <button
              key={n}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => onChange(n)}
              className={`h-9 w-9 rounded-md border text-sm font-medium transition ${
                selected
                  ? "border-gold-400/70 bg-gold-400/85 text-deep-space-900"
                  : "border-white/15 bg-deep-space-900/60 text-white/70 hover:border-gold-400/40 hover:text-white"
              }`}
            >
              {n}
            </button>
          );
        })}
      </div>
      <div className="mt-2 flex justify-between text-[11px] text-white/35">
        <span>{axis.low}</span>
        <span>{axis.high}</span>
      </div>
    </fieldset>
  );
}

function TextField({
  label,
  hint,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  hint?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="block rounded-xl border border-white/10 bg-white/5 p-5">
      <span className="text-sm font-semibold text-white">{label}</span>
      {hint ? <span className="mt-1 block text-xs text-white/55">{hint}</span> : null}
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        maxLength={2000}
        rows={3}
        className="mt-3 w-full rounded-md border border-white/15 bg-deep-space-900 px-3 py-2 text-sm text-white placeholder:text-white/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-400/60"
      />
    </label>
  );
}

export default function OpiniaoPage() {
  const [scores, setScores] = useState<Record<string, number | null>>({
    usability: null,
    experience: null,
    functionality: null,
    delivers: null,
    nps: null,
  });
  const [adopt, setAdopt] = useState<string | null>(null);
  const [mostValuable, setMostValuable] = useState("");
  const [frictions, setFrictions] = useState("");
  const [improvements, setImprovements] = useState("");
  const [contactOk, setContactOk] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasAnyAnswer =
    Object.values(scores).some((v) => v !== null) ||
    adopt !== null ||
    mostValuable.trim() !== "" ||
    frictions.trim() !== "" ||
    improvements.trim() !== "";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!hasAnyAnswer) {
      setError("Responda ao menos um campo antes de enviar.");
      return;
    }
    setSubmitting(true);
    setError(null);
    const payload: FeedbackSubmission = {
      usability: scores.usability,
      experience: scores.experience,
      functionality: scores.functionality,
      delivers: scores.delivers,
      nps: scores.nps,
      adopt,
      most_valuable: mostValuable.trim() || null,
      frictions: frictions.trim() || null,
      improvements: improvements.trim() || null,
      contact_ok: contactOk,
    };
    try {
      await submitBetaFeedback(payload);
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao enviar opinião.");
    } finally {
      setSubmitting(false);
    }
  }

  if (done) {
    return (
      <main className="mx-auto max-w-2xl px-5 py-20 text-center">
        <div className="glass-card p-10">
          <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-full bg-gold-400/20 text-2xl text-gold-300">
            ✓
          </div>
          <h1 className="text-2xl font-semibold text-white">Opinião registrada</h1>
          <p className="mt-3 text-sm text-white/60">
            Obrigado — o seu retorno molda diretamente o que o produto se torna.
            Você pode revisitar esta página a qualquer momento para enviar uma
            nova avaliação conforme seu uso evolui.
          </p>
          <button
            type="button"
            onClick={() => {
              setDone(false);
              setScores({
                usability: null,
                experience: null,
                functionality: null,
                delivers: null,
                nps: null,
              });
              setAdopt(null);
              setMostValuable("");
              setFrictions("");
              setImprovements("");
              setContactOk(false);
            }}
            className="btn-glass mt-8 inline-flex"
          >
            Enviar outra avaliação
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl px-5 py-12">
      <header className="mb-8">
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-gold-500/85">
          Programa Beta
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Deixe sua opinião</h1>
        <p className="mt-3 max-w-xl text-sm text-white/55">
          Sua avaliação honesta é o material mais valioso do beta. Leva ~3 minutos.
          Responda só o que fizer sentido — nenhum campo é obrigatório.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-5">
        <section className="space-y-4">
          {AXES.map((axis) => (
            <ScaleRow
              key={axis.key}
              axis={axis}
              value={scores[axis.key]}
              onChange={(v) => setScores((s) => ({ ...s, [axis.key]: v }))}
            />
          ))}
        </section>

        <fieldset className="rounded-xl border border-white/10 bg-white/5 p-5">
          <legend className="px-1 text-sm font-semibold text-white">
            Você adotaria o Heillon na sua organização?
          </legend>
          <div className="mt-3 flex flex-col gap-2">
            {ADOPT_OPTIONS.map((opt) => (
              <label
                key={opt.value}
                className={`flex cursor-pointer items-center gap-3 rounded-md border px-3 py-2 text-sm transition ${
                  adopt === opt.value
                    ? "border-gold-400/60 bg-gold-400/10 text-white"
                    : "border-white/10 text-white/70 hover:border-white/25"
                }`}
              >
                <input
                  type="radio"
                  name="adopt"
                  value={opt.value}
                  checked={adopt === opt.value}
                  onChange={() => setAdopt(opt.value)}
                  className="accent-gold-400"
                />
                {opt.label}
              </label>
            ))}
          </div>
        </fieldset>

        <TextField
          label="A maior razão para o Heillon existir"
          hint="Em poucas frases, com as suas palavras (não as nossas)."
          value={mostValuable}
          onChange={setMostValuable}
          placeholder="Na minha percepção, o Heillon importa porque…"
        />
        <TextField
          label="Maiores fricções ou problemas"
          hint="O que travou, confundiu ou quebrou? Isso é ouro para nós."
          value={frictions}
          onChange={setFrictions}
          placeholder="O que mais te incomodou…"
        />
        <TextField
          label="Melhorias que você pediria"
          hint="Se pudesse pedir 1–3 coisas, quais seriam?"
          value={improvements}
          onChange={setImprovements}
          placeholder="Eu adoraria que o Heillon…"
        />

        <label className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 p-5 text-sm text-white/75">
          <input
            type="checkbox"
            checked={contactOk}
            onChange={(e) => setContactOk(e.target.checked)}
            className="h-4 w-4 accent-gold-400"
          />
          Quero continuar conectado ao time de produto para conversar sobre o beta.
        </label>

        {error ? (
          <div
            role="alert"
            className="rounded-md border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200"
          >
            {error}
          </div>
        ) : null}

        <div className="flex items-center justify-between gap-4 pt-2">
          <p className="text-xs text-white/40">
            Suas respostas são agregadas de forma de-identificada para análise.
          </p>
          <button
            type="submit"
            disabled={submitting || !hasAnyAnswer}
            className="btn-gold disabled:opacity-50"
          >
            {submitting ? "Enviando…" : "Enviar opinião"}
          </button>
        </div>
      </form>
    </main>
  );
}
