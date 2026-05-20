import { DocsContent } from "@/components/docs/DocsContent";
import { BodyAdminGuide } from "@/content/documentation/bodies";
import { DOCS_UPDATED_FALLBACK } from "@/lib/docs-registry";

export default function Page() {
  return (
    <DocsContent
      title="Guia do administrador"
      subtitle="Governança mínima: organizações internas vs clientes externos, segurança, normas e relatórios controlados."
      lastUpdated={DOCS_UPDATED_FALLBACK}
      related={[
        { href: "/docs/compliance", label: "Guia de conformidade" },
        { href: "/dashboard", label: "Painel do operador (app)" },
        { href: "/agent-config", label: "Modelos e agent-config (app)" },
        { href: "/normative", label: "Hub normativo (app)" },
      ]}
    >
      <BodyAdminGuide />
    </DocsContent>
  );
}
