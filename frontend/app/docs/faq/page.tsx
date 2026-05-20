import { DocsContent } from "@/components/docs/DocsContent";
import { BodyFAQ } from "@/content/documentation/bodies";
import { DOCS_UPDATED_FALLBACK } from "@/lib/docs-registry";

export default function Page() {
  return (
    <DocsContent
      title="Perguntas frequentes"
      subtitle="FAQ segmentada por perfil (Admin, Advogado, Juiz da prova técnica, Perito)."
      lastUpdated={DOCS_UPDATED_FALLBACK}
      related={[
        { href: "/docs/usage", label: "Manual de uso geral" },
        { href: "/docs/expert", label: "Guia do perito" },
      ]}
    >
      <BodyFAQ />
    </DocsContent>
  );
}
