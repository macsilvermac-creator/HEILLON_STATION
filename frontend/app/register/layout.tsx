import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Criar conta · Heillon Legal",
  description: "Cadastro de operadores judiciários, peritos e auditores para a plataforma Heillon Legal.",
};

export default function RegisterLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
