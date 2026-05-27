import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Minha Conta · Heillon Legal",
  description: "Quota, plano, chaves de API e onboarding.",
};

export default function ContaLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
