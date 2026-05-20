import { DocsContent } from "@/components/docs/DocsContent";
import { BodyManualUsage } from "@/content/documentation/bodies";
import { DOCS_UPDATED_FALLBACK } from "@/lib/docs-registry";

export default function Page() {
  return (
    <DocsContent
      title="Manual de uso geral"
      subtitle="Orientação sobre autenticação, missões EASY, ingestão protegida, verificação pública e integração com relatórios forenses / normativos."
      lastUpdated={DOCS_UPDATED_FALLBACK}
      related={[
        { href: "/docs/chain-of-custody", label: "Manual da cadeia de custódia" },
        { href: "/docs/lgpd", label: "Guia LGPD" },
        { href: "/docs/faq", label: "FAQ" },
      ]}
    >
      <BodyManualUsage />
    </DocsContent>
  );
}
