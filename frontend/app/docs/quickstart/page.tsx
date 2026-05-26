import { DocsContent } from "@/components/docs/DocsContent";
import { BodyQuickstart } from "@/content/documentation/bodies";
import { DOCS_UPDATED_FALLBACK } from "@/lib/docs-registry";

export default function Page() {
  return (
    <DocsContent
      title="Início rápido — 5 minutos"
      subtitle="Do zero ao primeiro HDR verificável em 5 passos. Não requer configuração de ambiente."
      lastUpdated={DOCS_UPDATED_FALLBACK}
      related={[
        { href: "/docs/usage",            label: "Manual completo" },
        { href: "/docs/chain-of-custody", label: "Cadeia de custódia" },
        { href: "/docs/architecture",     label: "Arquitetura do sistema" },
      ]}
    >
      <BodyQuickstart />
    </DocsContent>
  );
}
