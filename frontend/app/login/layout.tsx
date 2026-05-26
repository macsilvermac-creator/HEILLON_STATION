import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Entrar · Heillon Legal",
  description: "Acesso de operadores judiciários e DPO à plataforma Heillon Legal.",
};

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
