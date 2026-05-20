import { MobileRouteLayout } from "@/components/mobile/MobileRouteLayout";

export const metadata = {
  title: "Heillon Legal · Mobile",
  description: "PWA — legitimidade na palma da mão.",
};

export default function MobileRootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <MobileRouteLayout>{children}</MobileRouteLayout>;
}
