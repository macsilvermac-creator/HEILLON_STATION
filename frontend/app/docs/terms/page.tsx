import { DocsContent } from "@/components/docs/DocsContent";
import { BodyTerms } from "@/content/documentation/bodies";
import { DOCS_UPDATED_FALLBACK } from "@/lib/docs-registry";

export default function Page() {
  return (
    <DocsContent
      title="Termos de uso"
      subtitle="Condições mínimas de utilização dos serviços Heillon MVP. Substitua / complemente com contratos firmados casa-fora."
      lastUpdated={DOCS_UPDATED_FALLBACK}
      related={[
        { href: "/docs/privacy", label: "Política de Privacidade" },
        { href: "/docs", label: "Central de Documentação" },
      ]}
    >
      <BodyTerms />
    </DocsContent>
  );
}
