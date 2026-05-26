import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";

import "./globals.css";
import { ConditionalAppShell } from "@/components/ConditionalAppShell";
import { Providers } from "@/app/providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-jetbrains",
});

export const viewport: Viewport = {
  themeColor: "#D4AF37",
  colorScheme: "dark",
};

export const metadata: Metadata = {
  title: {
    default: "Heillon Legal · Auditoria forense de IA jurídica",
    template: "%s",
  },
  description:
    "Plataforma de auditoria criptográfica do uso de IA em advocacia, judiciário e perícia. Cadeia de custódia com timestamp ICP-Brasil, corpus normativo LGPD/GDPR/EU AI Act/CNJ 615.",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Heillon Legal",
  },
  formatDetection: {
    telephone: false,
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt" className={`${inter.variable} ${jetbrains.variable}`}>
      <body className="min-h-screen overflow-x-hidden bg-deep-space-900 text-white antialiased">
        <Providers>
          <ConditionalAppShell>{children}</ConditionalAppShell>
        </Providers>
      </body>
    </html>
  );
}
