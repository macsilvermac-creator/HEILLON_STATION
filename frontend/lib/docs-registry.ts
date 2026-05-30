/**
 * Índice da Central de Documentação — Heillon Legal (Beta Privado).
 * Atualizado: 30 de maio de 2026 — coletores, quota e conta.
 */

export type DocsCategoryKey = "start" | "manuals" | "legal" | "guides" | "faq" | "changelog";

export type DocEntryMeta = {
  href: string;
  title: string;
  category: DocsCategoryKey;
  /** Texto concatenado para busca instantânea (título + descrição + palavras-chave). */
  searchBlob: string;
  description: string;
};

export const DOCS_UPDATED_FALLBACK = "30 de maio de 2026";

export const DOCS_CATEGORY_LABELS: Record<DocsCategoryKey, { label: string; icon: string }> = {
  start:     { label: "Início rápido",  icon: "🚀" },
  manuals:   { label: "Manuais",        icon: "📘" },
  legal:     { label: "Legal",          icon: "⚖️" },
  guides:    { label: "Guias",          icon: "🎯" },
  faq:       { label: "FAQ",            icon: "❓" },
  changelog: { label: "Changelog",      icon: "📝" },
};

export const DOC_ENTRIES: DocEntryMeta[] = [
  // ── Início rápido ──────────────────────────────────────────────────────────
  {
    href: "/docs/quickstart",
    title: "Início rápido — 5 minutos",
    category: "start",
    description: "Do zero ao primeiro HDR verificável: conta, chave de API e coletor.",
    searchBlob:
      "quickstart início rápido primeiro hdr conta registo chave api coletor extensão gateway captura passiva ingestão caso verificar verificação 5 minutos onboarding",
  },
  {
    href: "/docs/architecture",
    title: "Arquitetura do sistema",
    category: "start",
    description: "Stack tecnológico, 20+ domínios DDD, coletores, segurança em camadas.",
    searchBlob:
      "arquitetura sistema stack fastapi next.js postgresql redis ddd dominios coletores extensão gateway tier quota caddy sentry postmark segurança jwt fernet csp hsts tls",
  },
  {
    href: "/docs/regulations",
    title: "Cobertura regulatória global",
    category: "start",
    description: "7 jurisdições + ISO 42001 — LGPD, EU AI Act, CCPA, UAE PDPL, APAC.",
    searchBlob:
      "regulatório conformidade lgpd eu ai act gdpr eidas ccpa colorado oab cnj uae pdpl singapore australia iso 42001 apac jurisdições",
  },
  {
    href: "/docs/glossary",
    title: "Glossário — vernáculo jurídico",
    category: "start",
    description: "Tradução dos termos técnicos (HDR, Caso, Cadeia de Custódia) para o português jurídico.",
    searchBlob:
      "glossário glossario dicionario termos técnicos hdr caso missão cadeia custódia conformidade auditada legitimidade computacional icp-brasil ripd dpia soberania modelos vernáculo jurídico tradução",
  },

  // ── Manuais ────────────────────────────────────────────────────────────────
  {
    href: "/docs/usage",
    title: "Manual de uso geral",
    category: "manuals",
    description: "Coletores, conta e quota, chaves de API, casos, verificação e modelos de IA.",
    searchBlob:
      "manual uso plataforma autenticação cookie httponly coletores extensão browser gateway mcp api captura passiva chave api heillon_live quota planos free pro team enterprise conta eliminação caso missão easy planear executar aprovar diário ingestão evidências verificar hdr agent-config normas modelos de ia soberania ollama openai anthropic",
  },
  {
    href: "/docs/chain-of-custody",
    title: "Manual da cadeia de custódia",
    category: "manuals",
    description: "HDR, SHA-256, RFC 3161, ICP-Brasil, CAdES-BES e valor probatório.",
    searchBlob:
      "hdr heillon decision record cadeia custódia sha256 rfc3161 timestamp icp-brasil cades-bes assinatura digital encadeamento previous_hdr portal verificação integridade tribunal pki pkcs12",
  },

  // ── Legal ──────────────────────────────────────────────────────────────────
  {
    href: "/docs/lgpd",
    title: "Guia LGPD",
    category: "legal",
    description: "Lei 13.709/2018, princípios, centro de privacidade e RIPD.",
    searchBlob:
      "lgpd lei 13709 titular dados pessoais base legal ripd dpo anpd 72h portabilidade zip consentimento granular marco civil privacidade direitos art18",
  },
  {
    href: "/docs/terms",
    title: "Termos de uso",
    category: "legal",
    description: "Condições do serviço, responsabilidades e limitações.",
    searchBlob: "termos condições uso serviço responsabilidade jurisdição disclaimers SLA contrato",
  },
  {
    href: "/docs/privacy",
    title: "Política de privacidade",
    category: "legal",
    description: "Tratamento de dados, bases legais, direitos do titular.",
    searchBlob:
      "privacidade dados pessoais operador controlador segurança retenção jwt fernet bcrypt contacto titular direitos art18 dpo dpia",
  },

  // ── Guias ──────────────────────────────────────────────────────────────────
  {
    href: "/docs/compliance",
    title: "Guia de conformidade",
    category: "guides",
    description: "Relatórios LGPD, EU AI Act, ISO 42001 — Heillon Global Compliance Score.",
    searchBlob:
      "conformidade compliance lgpd relatório frameworks ai act iso 42001 colorado ccpa oab cnj uae score bronze prata ouro platina tier",
  },
  {
    href: "/docs/expert",
    title: "Guia do perito forense",
    category: "guides",
    description: "Workflow pericial completo: ingestão, missão, pacote forense, tribunal.",
    searchBlob:
      "perito pericial laudo tribunal protocolo cadeia custódia forense pdf/a executive_report chain.json manifest sig verificação adversarial",
  },
  {
    href: "/docs/admin",
    title: "Guia do administrador",
    category: "guides",
    description: "Deploy, variáveis de produção, coletores, quota, billing, admin e observabilidade.",
    searchBlob:
      "admin gestão organização multi-tenant agent-config modelos docker compose caddy postgresql redis health fernet auth secret key verification public base corpus normativo rbac coletores quota tier billing webhook hmac heillon_admin_token sentry postmark observabilidade",
  },

  // ── FAQ ────────────────────────────────────────────────────────────────────
  {
    href: "/docs/faq",
    title: "Perguntas frequentes",
    category: "faq",
    description: "Respostas por perfil: perito, advogado, magistrado e administrador.",
    searchBlob:
      "faq perguntas dúvidas perito advogado juiz magistrado tribunal admin login mobile pwa jwt cadeia prova icp-brasil anos depois verificar sem conta coletores extensão gateway chave api quota plano free eliminar conta hdr",
  },

  // ── Changelog ──────────────────────────────────────────────────────────────
  {
    href: "/docs/changelog",
    title: "Changelog · até o Beta Privado",
    category: "changelog",
    description: "Histórico de releases — substrato de coletores, quota e conta para o beta.",
    searchBlob:
      "changelog releases versão fase roadmap história actualização beta coletores extensão gateway tier quota conta onboarding caddy sentry segurança pwa corpus normativo iso42001 eu ai act uae apac malpractice score",
  },
];

export function filterDocsByQuery(query: string): DocEntryMeta[] {
  const q = query.trim().toLowerCase();
  if (!q) return DOC_ENTRIES;

  const words = q.split(/\s+/).filter(Boolean);

  function score(blob: string): number {
    const b = blob.toLowerCase();
    let s = 0;
    if (b.includes(q)) s += 8;
    for (const w of words) {
      if (w.length >= 3 && b.includes(w)) s += 2;
    }
    return s;
  }

  return DOC_ENTRIES.map((doc) => ({ doc, score: score(doc.searchBlob + " " + doc.title.toLowerCase()) }))
    .filter(({ score }) => score > 0)
    .sort((a, b) => b.score - a.score)
    .map(({ doc }) => doc);
}
