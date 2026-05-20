/**
 * Índice da Central de Documentação — metadados e texto pesquisável (Fase 10).
 */

export type DocsCategoryKey = "manuals" | "legal" | "guides" | "faq" | "changelog";

export type DocEntryMeta = {
  href: string;
  title: string;
  category: DocsCategoryKey;
  /** Texto concatenado para busca instantânea (título + descrição + palavras-chave). */
  searchBlob: string;
  description: string;
};

export const DOCS_UPDATED_FALLBACK = "19 de maio de 2026";

export const DOCS_CATEGORY_LABELS: Record<DocsCategoryKey, { label: string; icon: string }> = {
  manuals: { label: "Manuais", icon: "📘" },
  legal: { label: "Legal", icon: "⚖️" },
  guides: { label: "Guias", icon: "🎯" },
  faq: { label: "FAQ", icon: "❓" },
  changelog: { label: "Changelog", icon: "📝" },
};

export const DOC_ENTRIES: DocEntryMeta[] = [
  {
    href: "/docs/usage",
    title: "Manual de uso geral",
    category: "manuals",
    description: "Fluxo completo: conta, missões, verificação, pacotes forenses.",
    searchBlob:
      "manual uso plataforma missão easy planear executar aprovar diário ingestão evidências pacote forense verificar hdr agent-config normativo",
  },
  {
    href: "/docs/chain-of-custody",
    title: "Manual da cadeia de custódia",
    category: "manuals",
    description: "HDR, SHA-256, RFC 3161, encadeamento e valor probatório.",
    searchBlob:
      "hdr heillon decision record cadena custódia sha256 rfc3161 timestamp anterior previous_hdr portal verificação integridade tribunal",
  },
  {
    href: "/docs/lgpd",
    title: "Guia LGPD",
    category: "legal",
    description: "Lei 13.709/2018, princípios, relatórios e direitos do titular.",
    searchBlob:
      "lgpd lei 13709 titular dados pessoais base legal relatório conformidade anonimização consentimento dados sensíveis anpd",
  },
  {
    href: "/docs/terms",
    title: "Termos de uso",
    category: "legal",
    description: "Condições do serviço, responsabilidades e limitações.",
    searchBlob: "termos condições uso serviço responsabilidade jurisdição disclaimers MVP",
  },
  {
    href: "/docs/privacy",
    title: "Política de privacidade",
    category: "legal",
    description: "Tratamento de dados na Heillon Legal (MVP).",
    searchBlob:
      "privacidade dados pessoais operador controlador segurança retenção cookies localStorage jwt bcrypt contacto titular direitos art 18",
  },
  {
    href: "/docs/compliance",
    title: "Guia de conformidade",
    category: "guides",
    description: "Relatórios LGPD (e extensível a AI Act / ISO 42001).",
    searchBlob:
      "conformidade compliance lgpd relatório frameworks ai act iso 42001 hub normativo ancoragens",
  },
  {
    href: "/docs/expert",
    title: "Guia do perito",
    category: "guides",
    description: "Workflow pericial: ingestão, cadeia, exportação judicial.",
    searchBlob:
      "perito pericial laudo tribunal protocolo cadeia custódia forense dossier EASY",
  },
  {
    href: "/docs/admin",
    title: "Guia do administrador",
    category: "guides",
    description: "Organização, utilizadores, agentes e normas.",
    searchBlob:
      "admin gestão organização multi-tenant agent-config modelos bearer missões rbac",
  },
  {
    href: "/docs/faq",
    title: "Perguntas frequentes",
    category: "faq",
    description: "Respostas por perfil: perito, advogado, juiz e administração.",
    searchBlob:
      "faq perguntas dúvidas perito advogado juiz tribunal admin login mobile PWA JWT",
  },
  {
    href: "/docs/changelog",
    title: "Changelog · Release notes",
    category: "changelog",
    description: "Histórico de releases do MVP (Fases 1–10).",
    searchBlob:
      "changelog releases versão fase roadmap história actualização segurança pwa corpus normativo",
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
