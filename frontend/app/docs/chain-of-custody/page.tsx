import { DocsContent } from "@/components/docs/DocsContent";
import { BodyChainCustody } from "@/content/documentation/bodies";
import { DOCS_UPDATED_FALLBACK } from "@/lib/docs-registry";

export default function Page() {
  return (
    <DocsContent
      title="Manual da cadeia de custódia"
      subtitle="Como funcionam HDR, SHA-256, carimbos temporais, encadeamentos e evidências públicas dentro do modelo Heillon."
      lastUpdated={DOCS_UPDATED_FALLBACK}
      related={[
        { href: "/verification", label: "Portal de verificação (app)" },
        { href: "/docs/usage", label: "Manual de uso geral" },
      ]}
    >
      <BodyChainCustody />
    </DocsContent>
  );
}
