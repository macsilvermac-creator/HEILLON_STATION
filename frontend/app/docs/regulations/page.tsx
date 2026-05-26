import { DocsContent } from "@/components/docs/DocsContent";
import { BodyRegulations } from "@/content/documentation/bodies";
import { DOCS_UPDATED_FALLBACK } from "@/lib/docs-registry";

export default function Page() {
  return (
    <DocsContent
      title="Cobertura regulatória global"
      subtitle="7 jurisdições + ISO 42001:2023 — LGPD, EU AI Act, CCPA, UAE PDPL, APAC e mais."
      lastUpdated={DOCS_UPDATED_FALLBACK}
      related={[
        { href: "/docs/lgpd",       label: "Guia LGPD" },
        { href: "/docs/compliance", label: "Guia de conformidade" },
        { href: "/docs/changelog",  label: "Changelog de releases" },
      ]}
    >
      <BodyRegulations />
    </DocsContent>
  );
}
