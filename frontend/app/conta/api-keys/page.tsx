"use client";

import { useEffect, useState } from "react";

import {
  listApiKeys,
  mintApiKey,
  revokeApiKey,
  type ApiKeyPublic,
  type ApiKeyMintResponse,
} from "@/lib/api";

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("pt-BR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKeyPublic[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [newKeyName, setNewKeyName] = useState("");
  const [creating, setCreating] = useState(false);
  const [mintedKey, setMintedKey] = useState<ApiKeyMintResponse | null>(null);
  const [copyState, setCopyState] = useState<"idle" | "copied">("idle");

  const refresh = async () => {
    setLoading(true);
    try {
      const list = await listApiKeys();
      setKeys(list);
      setErr(null);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Falha ao listar chaves.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    setCreating(true);
    try {
      const minted = await mintApiKey(newKeyName.trim());
      setMintedKey(minted);
      setNewKeyName("");
      await refresh();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Falha ao gerar chave.");
    } finally {
      setCreating(false);
    }
  };

  const handleCopy = async () => {
    if (!mintedKey) return;
    try {
      await navigator.clipboard.writeText(mintedKey.plaintext_key);
      setCopyState("copied");
      setTimeout(() => setCopyState("idle"), 2500);
    } catch {
      // clipboard unavailable — user can manually select
    }
  };

  const handleRevoke = async (id: string) => {
    if (!confirm("Revogar esta chave? Aplicações que usam essa chave deixarão de funcionar imediatamente.")) {
      return;
    }
    try {
      await revokeApiKey(id);
      await refresh();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Falha ao revogar.");
    }
  };

  const activeKeys = keys.filter((k) => k.revoked_at === null);
  const revokedKeys = keys.filter((k) => k.revoked_at !== null);

  return (
    <section className="mx-auto max-w-5xl px-6 py-16">
      <header className="mb-10">
        <p className="text-xs uppercase tracking-widest text-gold-400/80">Minha Conta</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Chaves de API</h1>
        <p className="mt-2 max-w-2xl text-sm text-white/60">
          Chaves usadas por coletores (Extensão do Browser, MCP Gateway, integrações próprias).
          A chave em texto-claro é exibida UMA vez no momento da criação — armazene em local seguro.
        </p>
      </header>

      {err ? (
        <div role="alert" className="mb-6 rounded-xl border border-rose-500/40 bg-rose-500/10 px-5 py-4 text-sm text-rose-200">
          {err}
        </div>
      ) : null}

      {/* Modal de chave recém-criada */}
      {mintedKey ? (
        <div
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="minted-key-title"
          className="mb-8 rounded-2xl border border-gold-400/50 bg-gold-400/[0.06] p-6"
        >
          <h2 id="minted-key-title" className="text-lg font-semibold text-gold-100">
            ✓ Chave criada: {mintedKey.name}
          </h2>
          <p className="mt-2 text-sm text-gold-100/85">
            Copie agora — não será mostrada novamente. Após fechar este aviso, só restará o prefixo
            (<code className="font-mono">{mintedKey.prefix}…</code>) para identificação visual.
          </p>
          <div className="mt-4 flex items-center gap-2 rounded-lg border border-white/15 bg-deep-space-900/60 p-3 font-mono text-xs">
            <code className="flex-1 overflow-x-auto whitespace-nowrap text-gold-100">
              {mintedKey.plaintext_key}
            </code>
            <button
              type="button"
              onClick={handleCopy}
              className="shrink-0 rounded-md border border-gold-400/40 px-3 py-1 text-gold-200 transition hover:bg-gold-400/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-400/60"
            >
              {copyState === "copied" ? "Copiado!" : "Copiar"}
            </button>
          </div>
          <button
            type="button"
            onClick={() => setMintedKey(null)}
            className="mt-4 text-xs text-gold-200/70 underline-offset-4 hover:text-gold-100 hover:underline focus-visible:outline-none"
          >
            Já guardei — fechar
          </button>
        </div>
      ) : null}

      {/* Form criação */}
      <form
        onSubmit={handleCreate}
        className="mb-10 rounded-2xl border border-white/10 bg-white/[0.02] p-6"
      >
        <h2 className="text-base font-semibold text-white">Gerar nova chave</h2>
        <p className="mt-1 text-xs text-white/55">
          Dê um nome que identifique onde a chave será usada (ex.: &ldquo;Browser Chrome
          pessoal&rdquo;, &ldquo;Servidor de produção&rdquo;).
        </p>
        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label htmlFor="api-key-name" className="mb-1 block text-xs text-white/55">
              Nome
            </label>
            <input
              id="api-key-name"
              name="name"
              type="text"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              maxLength={120}
              required
              placeholder="Extensão do Browser - Notebook pessoal"
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-white/30 focus:border-gold-500/60 focus:outline-none focus:ring-1 focus:ring-gold-500/40"
            />
          </div>
          <button
            type="submit"
            disabled={creating || !newKeyName.trim()}
            className="rounded-xl bg-gold-400 px-5 py-3 text-sm font-medium text-deep-space-900 transition hover:bg-gold-300 disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-400/60"
          >
            {creating ? "Gerando…" : "Gerar chave"}
          </button>
        </div>
      </form>

      {/* Lista ativa */}
      <section className="mb-12">
        <h2 className="mb-4 text-base font-semibold text-white">
          Chaves ativas{" "}
          <span className="text-xs font-normal text-white/45">({activeKeys.length})</span>
        </h2>
        {loading ? (
          <p className="text-sm text-white/45">Carregando…</p>
        ) : activeKeys.length === 0 ? (
          <p className="rounded-xl border border-white/10 bg-white/[0.02] p-6 text-sm text-white/55">
            Você ainda não tem chaves ativas. Crie uma acima para usar com a Extensão do Browser ou o MCP Gateway.
          </p>
        ) : (
          <ul className="space-y-3">
            {activeKeys.map((k) => (
              <li
                key={k.api_key_id}
                className="rounded-xl border border-white/10 bg-white/[0.02] p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-white">{k.name}</p>
                    <p className="mt-1 font-mono text-[11px] text-white/45">
                      {k.prefix}… · criada em {formatDate(k.created_at)}
                    </p>
                    <p className="mt-1 text-[11px] text-white/35">
                      Último uso: {formatDate(k.last_used_at)}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRevoke(k.api_key_id)}
                    className="rounded-md border border-rose-500/40 px-3 py-1.5 text-xs text-rose-200 transition hover:bg-rose-500/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-400/60"
                  >
                    Revogar
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Lista revogada */}
      {revokedKeys.length > 0 ? (
        <section>
          <h2 className="mb-4 text-base font-semibold text-white/55">
            Histórico revogado{" "}
            <span className="text-xs font-normal text-white/35">({revokedKeys.length})</span>
          </h2>
          <ul className="space-y-2">
            {revokedKeys.map((k) => (
              <li
                key={k.api_key_id}
                className="rounded-xl border border-white/[0.05] bg-white/[0.01] p-3 text-xs text-white/35"
              >
                <span className="font-medium text-white/55">{k.name}</span>
                <span className="ml-2 font-mono">({k.prefix}…)</span>
                <span className="ml-2">revogada em {formatDate(k.revoked_at)}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </section>
  );
}
