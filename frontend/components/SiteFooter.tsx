import Link from "next/link";

const FOOTER_COLUMNS = [
  {
    title: "Legal · LGPD",
    links: [
      { label: "Termos de uso", href: "/docs/terms" },
      { label: "Política de privacidade", href: "/docs/privacy" },
      { label: "Guia LGPD", href: "/docs/lgpd" },
      { label: "Guia de conformidade", href: "/docs/compliance" },
    ],
  },
  {
    title: "Ajuda",
    links: [
      { label: "Central de docs", href: "/docs" },
      { label: "FAQ", href: "/docs/faq" },
      { label: "Changelog", href: "/docs/changelog" },
    ],
  },
  {
    title: "Operação",
    links: [
      { label: "Início", href: "/" },
      { label: "Diário", href: "/diary" },
      { label: "Verificação pública", href: "/verification" },
    ],
  },
] as const;

export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-white/[0.08] bg-deep-space-900/95 py-14 text-[12px] text-white/54">
      <div className="mx-auto grid max-w-6xl gap-10 px-6 md:grid-cols-[1.35fr_repeat(3,1fr)]">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gold-500">
              <span className="text-xs font-bold text-deep-space-900">H</span>
            </div>
            <div className="leading-tight">
              <span className="block text-[10px] uppercase tracking-[0.25em] text-white/42">Legal</span>
              <span className="font-semibold text-white/88">Heillon</span>
            </div>
          </div>
          <p className="mt-4 max-w-sm leading-relaxed text-white/52">
            Auditoria criptográfica do uso de IA em direito. Registro forense (HDR), corpus normativo
            multi-jurisdição e timestamp RFC 3161 (arquitetura pronta para ICP-Brasil) — desenvolvimento contínuo (MVP).
          </p>
        </div>
        {FOOTER_COLUMNS.map((col) => (
          <div key={col.title}>
            <p className="mb-4 text-[10px] font-semibold uppercase tracking-[0.3em] text-gold-500/92">{col.title}</p>
            <ul className="space-y-2 text-white/60">
              {col.links.map((l) => (
                <li key={l.href}>
                  <Link href={l.href} className="underline-offset-4 hover:text-gold-300 hover:underline">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="mx-auto mt-12 max-w-6xl px-6 text-[11px] text-white/35">
        Este rodapé reúne ligações legais rápidas. Consulte sempre os documentos completos antes de usar dados reais ou
        suportes definitivos nos tribunais.
      </div>
    </footer>
  );
}
