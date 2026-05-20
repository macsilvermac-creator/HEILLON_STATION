import { DocsContent } from "@/components/docs/DocsContent";
import { BodyExpertGuide } from "@/content/documentation/bodies";
import { DOCS_UPDATED_FALLBACK } from "@/lib/docs-registry";

export default function Page() {
  return (
    <DocsContent
      title="Guia do perito técnico / forense digital"
      subtitle="Fluxos operativos especializados: ingestões, relatórios, integração HDR e segurança mínima exigível."
      lastUpdated={DOCS_UPDATED_FALLBACK}
      related={[
        { href: "/docs/chain-of-custody", label: "Manual da cadeia de custódia" },
        { href: "/ingestion", label: "Ingestão de evidências (app)" },
        { href: "/diary", label: "Diário EASY (app)" },
      ]}
    >
      <BodyExpertGuide />
    </DocsContent>
  );
}
