import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Conformidade · Heillon Legal",
  description: "Relatórios de conformidade LGPD, GDPR, EU AI Act, CNJ 615 e ISO 42001 — gerados a partir do registo HDR.",
};

export default function ComplianceLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
