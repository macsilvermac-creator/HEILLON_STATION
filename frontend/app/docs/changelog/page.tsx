import { DocsContent } from "@/components/docs/DocsContent";
import { BodyChangelog } from "@/content/documentation/bodies";
import { DOCS_UPDATED_FALLBACK } from "@/lib/docs-registry";

export default function Page() {
  return (
    <DocsContent
      title="Changelog & release notes (Fases 1 a 10)"
      subtitle="Resumo institucional do roadmap Heillon MVP conforme já documentado oficialmente até a Central de Docs."
      lastUpdated={DOCS_UPDATED_FALLBACK}
      related={[
        { href: "/docs", label: "Voltar ao hub Docs" },
        { href: "/docs/compliance", label: "Conformidade" },
      ]}
    >
      <BodyChangelog />
    </DocsContent>
  );
}
