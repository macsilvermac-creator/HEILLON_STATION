import type { Metadata } from "next";

import { DocsContent } from "@/components/docs/DocsContent";
import { Callout } from "@/components/docs/DocsPrimitives";
import { DOCS_UPDATED_FALLBACK } from "@/lib/docs-registry";

export const metadata: Metadata = {
  title: "Glossário · Heillon Legal",
  description:
    "Dicionário de termos técnicos do Heillon Legal traduzidos para a linguagem jurídica brasileira: HDR, Caso, Cadeia de Custódia, etc.",
};

type Term = {
  term: string;
  shortFor?: string;
  definition: string;
  exemplo?: string;
  aka?: string[];
};

const TERMS: Term[] = [
  {
    term: "HDR",
    shortFor: "Heillon Detailed Record",
    definition:
      "Registro de Auditoria de IA — é o nome técnico do registro forense que documenta, com selo criptográfico, cada vez que uma IA foi usada num caso. Cada HDR contém: quem usou (operador), quando (timestamp criptográfico RFC 3161), qual modelo, qual prompt, qual saída e qual decisão humana foi tomada.",
    exemplo:
      "Quando o advogado pede à IA para resumir um acórdão, um HDR é criado e assinado. Esse registro é imutável e pode ser apresentado em juízo para provar boa-fé na utilização da IA.",
    aka: ["Registro de Auditoria de IA", "Ata Eletrônica do Uso de IA"],
  },
  {
    term: "Caso",
    definition:
      "Conjunto de HDRs encadeados que documentam uma operação jurídica completa (uma petição, um parecer, uma análise pericial). Cada caso tem um identificador único (mission_id no backend) e sua cadeia de auditoria pode ser verificada externamente.",
    aka: ["Mission", "Missão", "Mandato"],
  },
  {
    term: "Cadeia de Custódia",
    definition:
      "Sequência cronológica e criptograficamente encadeada de HDRs. Cada HDR aponta para o anterior via hash SHA-256, formando uma corrente que não pode ser adulterada sem invalidar todos os elos seguintes. Conceito derivado do Direito Probatório (CPP art. 158-A a 158-F).",
  },
  {
    term: "Corpus Normativo",
    definition:
      "Base de regras jurídicas multi-jurisdição embarcada no sistema (LGPD, GDPR, EU AI Act, CNJ 615/2025, OAB 001/2024, ISO 42001, Colorado SB 205, CCPA, UAE PDPL, UK GDPR, Singapore PDPA). Cada operação é confrontada com essas regras em tempo real e violações são bloqueadas ou sinalizadas.",
  },
  {
    term: "ICP-Brasil",
    shortFor: "Infraestrutura de Chaves Públicas Brasileira",
    definition:
      "Sistema de certificação digital regulamentado pela MP 2.200-2/2001. A arquitetura do Heillon está preparada para Autoridades de Carimbo do Tempo (TSA) ICP-Brasil (Serpro/Certisign), que conferem ao timestamp valor jurídico equivalente a documento físico assinado. Durante o beta, os HDRs usam timestamp criptográfico RFC 3161; o selo ICP-Brasil qualificado entra na sequência.",
  },
  {
    term: "Conformidade Auditada",
    definition:
      "Estado em que toda operação de IA tem trilha completa, validada contra o corpus normativo e assinada com timestamp criptográfico (RFC 3161). Substitui o termo anterior 'Legitimidade Computacional' por uma expressão mais próxima do vernáculo jurídico.",
    aka: ["Legitimidade Computacional (termo antigo)"],
  },
  {
    term: "Relatório Forense Executivo",
    definition:
      "Documento PDF/A-3 gerado a partir da cadeia de HDRs de um caso, contendo: linha do tempo, evidências usadas, regras normativas verificadas, decisões humanas tomadas, e selo de tempo criptográfico (RFC 3161). Defensável perante juízo, OAB, CNJ, ANPD, ou auditorias internas.",
  },
  {
    term: "Selo Verificável",
    definition:
      "URL pública (/verification/{hdr_id}) onde qualquer pessoa pode confirmar, sem autenticação, a integridade de um registro: hash, timestamp RFC 3161, assinatura Ed25519 e cadeia.",
  },
  {
    term: "RIPD / DPIA",
    shortFor: "Relatório de Impacto à Proteção de Dados",
    definition:
      "Documento exigido pela LGPD (art. 38) e GDPR (Art. 35) para operações de alto risco com dados pessoais. O Heillon gera RIPD/DPIA automaticamente a partir da cadeia de HDRs do caso.",
  },
  {
    term: "Soberania de Modelos",
    definition:
      "Capacidade de rodar a IA inteiramente em infraestrutura controlada (Ollama local + on-premise), sem dependência de OpenAI/Anthropic/Google e sem envio de dados confidenciais ao exterior. Garantia ao sigilo profissional (OAB art. 7º, XIX) e à soberania de dados (LGPD).",
  },
];

export default function GlossaryPage() {
  return (
    <DocsContent
      title="Glossário"
      subtitle="Dicionário dos termos técnicos do Heillon Legal traduzidos para o vernáculo jurídico brasileiro."
      lastUpdated={DOCS_UPDATED_FALLBACK}
      related={[
        { href: "/docs/quickstart", label: "Início rápido" },
        { href: "/docs/architecture", label: "Arquitetura" },
        { href: "/docs/chain-of-custody", label: "Cadeia de custódia" },
      ]}
    >
      <Callout variant="info" title="Por que este glossário existe">
        Pesquisa com 17 operadores jurídicos brasileiros (advogados, juízes, delegados, DPO,
        procuradores, peritos) mostrou que termos como{" "}
        <strong>&ldquo;HDR&rdquo;</strong>, <strong>&ldquo;Missão&rdquo;</strong> e{" "}
        <strong>&ldquo;Legitimidade Computacional&rdquo;</strong> são percebidos como linguagem
        estrangeira ao Direito. Mantemos os termos técnicos no código (estabilidade de API), mas a
        UI agora usa equivalentes do vernáculo jurídico — &ldquo;Caso&rdquo;,
        &ldquo;Registro de Auditoria de IA&rdquo;, &ldquo;Conformidade Auditada&rdquo;.
      </Callout>

      <dl className="mt-10 space-y-8">
        {TERMS.map((t) => (
          <div
            key={t.term}
            className="rounded-2xl border border-white/10 bg-white/[0.02] p-6"
          >
            <dt className="flex flex-wrap items-baseline gap-3">
              <span className="text-xl font-semibold text-white">{t.term}</span>
              {t.shortFor ? (
                <span className="text-xs uppercase tracking-wider text-gold-300/80">
                  {t.shortFor}
                </span>
              ) : null}
            </dt>
            <dd className="mt-3 text-sm leading-relaxed text-white/70">{t.definition}</dd>
            {t.exemplo ? (
              <dd className="mt-3 rounded-lg border border-gold-400/15 bg-gold-400/[0.04] px-4 py-3 text-xs text-white/60">
                <strong className="text-gold-200">Exemplo:</strong> {t.exemplo}
              </dd>
            ) : null}
            {t.aka && t.aka.length > 0 ? (
              <dd className="mt-3 text-[11px] uppercase tracking-wider text-white/35">
                Também conhecido como: {t.aka.join(" · ")}
              </dd>
            ) : null}
          </div>
        ))}
      </dl>
    </DocsContent>
  );
}
