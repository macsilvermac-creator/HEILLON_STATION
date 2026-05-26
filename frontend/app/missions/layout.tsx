import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Casos · Heillon Legal",
  description:
    "Diário de casos com auditoria criptográfica de IA. Cadeia HDR, evidências e relatórios forenses por mandato.",
};

export default function MissionsLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
