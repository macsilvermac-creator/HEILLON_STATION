import { DocsContent } from "@/components/docs/DocsContent";
import { BodyLgpd } from "@/content/documentation/bodies";
import { DOCS_UPDATED_FALLBACK } from "@/lib/docs-registry";

export default function Page() {
  return (
    <DocsContent
      title="Guia LGPD (Lei 13.709/2018)"
      subtitle="Mapeamento de princípios legais básicos às ferramentas MVP Heillon Legal e orientação institucional mínima."
      lastUpdated={DOCS_UPDATED_FALLBACK}
      related={[
        { href: "/docs/privacy", label: "Política de Privacidade" },
        { href: "/normative", label: "Hub normativo (app)" },
        { href: "/docs/compliance", label: "Guia de conformidade" },
      ]}
    >
      <BodyLgpd />
    </DocsContent>
  );
}
