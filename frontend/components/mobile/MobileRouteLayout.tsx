"use client";

import { BottomTabBar } from "@/components/mobile/BottomTabBar";
import { InstallPromptGlass } from "@/components/mobile/InstallPromptGlass";
import { OfflineBanner } from "@/components/mobile/OfflineBanner";
import type { ReactNode } from "react";

export function MobileRouteLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-[100dvh] bg-deep-space-900">
      <OfflineBanner />
      <div className="pb-safe-tabs pt-safe-mobile mb-44">{children}</div>
      <BottomTabBar />
      <InstallPromptGlass />
    </div>
  );
}
