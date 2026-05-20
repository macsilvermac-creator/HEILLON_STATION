import { DocsContent } from "@/components/docs/DocsContent";
import { BodyPrivacy } from "@/content/documentation/bodies";
import { DOCS_UPDATED_FALLBACK } from "@/lib/docs-registry";

export default function Page() {
  return (
    <DocsContent
      title="Política de Privacidade"
      subtitle="Resumo operacional sobre categorias tratadas pelo MVP Heillon Legal."
      lastUpdated={DOCS_UPDATED_FALLBACK}
      related={[
        { href: "/docs/terms", label: "Termos de uso" },
        { href: "/docs/lgpd", label: "Guia LGPD" },
      ]}
    >
      <BodyPrivacy />
    </DocsContent>
  );
}
