import { DocsContent } from "@/components/docs/DocsContent";
import { BodyComplianceGuide } from "@/content/documentation/bodies";
import { DOCS_UPDATED_FALLBACK } from "@/lib/docs-registry";

export default function Page() {
  return (
    <DocsContent
      title="Guia de conformidade (LGPD, AI Act & ISO/IEC 42001)"
      subtitle="Orientação institucional mínima para integrar relatórios Heillon aos quadros jurídico-normativos modernos."
      lastUpdated={DOCS_UPDATED_FALLBACK}
      related={[
        { href: "/normative", label: "Dashboard normativo" },
        { href: "/diary", label: "Diário EASY (app)" },
        { href: "/ingestion", label: "Ingestão de evidências (app)" },
      ]}
    >
      <BodyComplianceGuide />
    </DocsContent>
  );
}
