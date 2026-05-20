import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Documentação · Heillon Mobile",
  description: "Central de documentação otimizada para PWA.",
};

export default function MobileDocsLayout({ children }: { children: ReactNode }) {
  return children;
}
