import { DocsContent } from "@/components/docs/DocsContent";
import { BodyArchitecture } from "@/content/documentation/bodies";
import { DOCS_UPDATED_FALLBACK } from "@/lib/docs-registry";

export default function Page() {
  return (
    <DocsContent
      title="Arquitetura do sistema"
      subtitle="Stack tecnológico, 18 domínios DDD, segurança em camadas e fluxo de dados fim-a-fim."
      lastUpdated={DOCS_UPDATED_FALLBACK}
      related={[
        { href: "/docs/quickstart",       label: "Início rápido" },
        { href: "/docs/chain-of-custody", label: "Cadeia de custódia HDR" },
        { href: "/docs/admin",            label: "Guia do administrador" },
      ]}
    >
      <BodyArchitecture />
    </DocsContent>
  );
}
