import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Painel · Heillon Legal",
  description: "Visão consolidada do uso de IA, conformidade normativa e cadeia de custódia.",
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
