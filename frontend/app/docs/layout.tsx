import type { Metadata } from "next";
import type { ReactNode } from "react";

import { DocsShell } from "@/components/docs/DocsShell";

export const metadata: Metadata = {
  title: "Documentação · Heillon Legal",
  description: "Central de documentação: manuais, LGPD, cadeia de custódia HDR e conformidade.",
};

export default function DocsLayout({ children }: { children: ReactNode }) {
  return <DocsShell>{children}</DocsShell>;
}
