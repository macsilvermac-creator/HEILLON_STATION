"use client";

import { useMemo, useState } from "react";

import {
  persistAuthBearer,
  listAgentConfigs,
  putAgentModelConfig,
  registerLegalOperator,
  testAgentModel,
} from "@/lib/api";

const DEFAULT_AGENTS = [
  "ocr-agent",
  "classification-agent",
  "analysis-agent",
  "clustering-agent",
  "prioritization-agent",
  "extraction-agent",
  "summarization-agent",
];

type SourceChoice = "stub" | "ollama" | "openai" | "anthropic" | "custom";

export default function AgentConfigPage() {
  const [email, setEmail] = useState("operator@court.demo");
  const [secret, setSecret] = useState("mudar-esta-password-para-testes-longos");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [configs, setConfigs] = useState<Record<string, unknown>[]>([]);
  const [selected, setSelected] = useState("analysis-agent");
  const [source, setSource] = useState<SourceChoice>("stub");
  const [modelName, setModelName] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [probe, setProbe] = useState<unknown>(null);

  const modelHint = useMemo(() => {
    if (source === "ollama") return "Ex.: llama3.2, qwen3:8b…";
    if (source === "openai") return "Ex.: gpt-5, gpt-4o-mini…";
    if (source === "anthropic") return "Ex.: claude-3-5-sonnet-latest…";
    return "Nome do modelo hospedado no endpoint personalizado.";
  }, [source]);

  const refresh = async () => {
    setBusy("A sincronizar configurações…");
    try {
      const rows = await listAgentConfigs();
      setConfigs(Array.isArray(rows) ? (rows as Record<string, unknown>[]) : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sem sessão válida?");
    } finally {
      setBusy(null);
    }
  };

  const handleBootstrap = async () => {
    setBusy("A criar conta demo…");
    setError("");
    try {
      const suffix = crypto.randomUUID().slice(0, 8);
      await registerLegalOperator({
        email: email.includes("@") ? email : `${email}-${suffix}@court.demo`,
        name: `Operador ${suffix}`,
        password: secret,
        role: "admin",
        organization_id: `org_${suffix}`,
      });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha onboarding.");
    } finally {
      setBusy(null);
    }
  };

  const handleLogout = () => {
    persistAuthBearer(null);
    setConfigs([]);
  };

  const handleSave = async () => {
    setBusy("A gravar…");
    setError("");
    try {
      const patch: Record<string, unknown> = {
        source,
        model_name: modelName.trim() || null,
        api_base_url: baseUrl.trim() || null,
      };
      if (apiKey.trim().length > 0) patch.api_key = apiKey.trim();
      await putAgentModelConfig(selected, patch);
      setApiKey("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Persistência falhou.");
    } finally {
      setBusy(null);
    }
  };

  const handleProbe = async () => {
    setBusy("A testar ligação…");
    setError("");
    try {
      setProbe(await testAgentModel(selected));
    } catch (err) {
      setProbe({ status: "error", detail: err instanceof Error ? err.message : String(err) });
    } finally {
      setBusy(null);
    }
  };

  const activeRow =
    configs.find((row) => typeof row.agent_id === "string" && row.agent_id === selected) ?? {};

  const keyFlag = typeof activeRow.api_key_is_set === "boolean" ? activeRow.api_key_is_set : false;

  return (
    <div className="mx-auto max-w-5xl pb-36 pt-40">
      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.33em] text-gold-500/85">Fase 5 · Soberania</p>
        <h1 className="text-gradient text-4xl font-semibold tracking-tight">Modelos soberanos por agente</h1>
        <p className="max-w-3xl text-sm text-white/60">
          Persistência encriptada (Fernet) no SQLite do backend · Necessário token JWT válido através de{" "}
          <span className="font-mono text-[11px] text-white/80">persistAuthBearer()</span>.
        </p>
      </div>

      <div className="mt-10 grid gap-6 lg:grid-cols-[1fr_1.05fr]">
        <section className="glass-card glass-card-hover space-y-4 p-6">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-sm font-semibold text-white">Sessão rápida</h2>
            <button type="button" data-cursor-hover className="text-xs text-gold-400" onClick={handleLogout}>
              Limpar bearer
            </button>
          </div>
          <label className="block space-y-2 text-xs text-white/60">
            Email operador demo
            <input
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="w-full rounded-xl border border-white/10 bg-deep-space-800/95 px-3 py-2 text-sm text-white"
            />
          </label>
          <label className="block space-y-2 text-xs text-white/60">
            Password
            <input
              type="password"
              value={secret}
              onChange={(event) => setSecret(event.target.value)}
              className="w-full rounded-xl border border-white/10 bg-deep-space-800/95 px-3 py-2 text-sm text-white"
            />
          </label>
          <button type="button" data-cursor-hover className="btn-gold w-full text-sm" onClick={() => void handleBootstrap()}>
            Registrar + token automático
          </button>
          <button type="button" data-cursor-hover className="btn-glass w-full text-sm" onClick={() => void refresh()}>
            Refrescar catálogo
          </button>
          {busy ? <p className="text-xs text-white/45">{busy}</p> : null}
          {error ? <p className="text-xs text-rose-400">{error}</p> : null}
        </section>

        <section className="glass-card glass-card-hover space-y-4 p-6">
          <h2 className="text-sm font-semibold text-white">Editor por agente</h2>

          <label className="block space-y-2 text-xs text-white/60">
            Agente EASY
            <select
              value={selected}
              onChange={(event) => setSelected(event.target.value)}
              className="w-full rounded-xl border border-white/10 bg-deep-space-800/95 px-3 py-2 text-sm text-white"
            >
              {DEFAULT_AGENTS.map((agentId) => (
                <option key={agentId} value={agentId}>
                  {agentId}
                </option>
              ))}
            </select>
          </label>

          <label className="block space-y-2 text-xs text-white/60">
            Fonte de inferência
            <select
              value={source}
              onChange={(event) => setSource(event.target.value as SourceChoice)}
              className="w-full rounded-xl border border-white/10 bg-deep-space-800/95 px-3 py-2 text-sm text-white"
            >
              <option value="stub">STUB (determinístico EASY)</option>
              <option value="ollama">Ollama (OpenAI compat /v1)</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic Messages</option>
              <option value="custom">API compatível Chat Completions</option>
            </select>
          </label>

          <label className="block space-y-2 text-xs text-white/60">
            Nome modelo <span className="text-[10px] text-white/40">({modelHint})</span>
            <input
              value={modelName}
              onChange={(event) => setModelName(event.target.value)}
              className="w-full rounded-xl border border-white/10 bg-deep-space-800/95 px-3 py-2 text-sm text-white"
              placeholder={
                typeof activeRow.model_name === "string" && activeRow.model_name.length ? String(activeRow.model_name) : "opcional…"
              }
            />
          </label>

          <label className="block space-y-2 text-xs text-white/60">
            Endpoint base opcional (Ollama / proxy / VPC)
            <input
              value={baseUrl}
              onChange={(event) => setBaseUrl(event.target.value)}
              className="w-full rounded-xl border border-white/10 bg-deep-space-800/95 px-3 py-2 font-mono text-[11px] text-white"
              placeholder={
                typeof activeRow.api_base_url === "string"
                  ? String(activeRow.api_base_url)
                  : "http://127.0.0.1:11434/v1"
              }
            />
          </label>

          <label className="block space-y-2 text-xs text-white/60">
            API key transitória (persistida encriptada) — atual:{" "}
            <span className={keyFlag ? "text-emerald-400" : "text-amber-300"}>{keyFlag ? "definida" : "não definida"}</span>
            <input
              type="password"
              autoComplete="off"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              className="w-full rounded-xl border border-white/10 bg-deep-space-800/95 px-3 py-2 text-sm text-white"
              placeholder={keyFlag ? "••••••• (deixar vazio para manter)" : "cole o segredo apenas no browser local"}
            />
          </label>

          <div className="flex flex-wrap gap-3 pt-3">
            <button type="button" data-cursor-hover className="btn-gold text-sm" onClick={() => void handleSave()}>
              Persistir modelo
            </button>
            <button type="button" data-cursor-hover className="btn-glass text-sm" onClick={() => void handleProbe()}>
              Testar chamada sintética
            </button>
          </div>

          {probe ? (
            <pre className="mt-4 max-h-60 overflow-auto rounded-xl border border-white/10 bg-black/35 p-3 text-[11px] text-white">
              {JSON.stringify(probe, null, 2)}
            </pre>
          ) : null}
        </section>
      </div>

      <section className="glass-card mt-10 p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">Snapshot JSON</h2>
          <span className="text-[11px] text-white/40">{configs.length ? `${configs.length} linhas` : "Sem dados"}</span>
        </div>
        <pre className="mt-4 max-h-[280px] overflow-auto text-[11px] text-white/70">
          {configs.length ? JSON.stringify(configs, null, 2) : "// autentica-se para pré-visualizar configs persistidas"}
        </pre>
      </section>
    </div>
  );
}
