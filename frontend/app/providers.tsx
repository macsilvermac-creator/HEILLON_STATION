"use client";

import { CookieConsent } from "@/components/CookieConsent";
import { OnboardingTour } from "@/components/onboarding/OnboardingTour";
import { AuthProvider } from "@/lib/auth-context";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      {children}
      <OnboardingTour />
      <CookieConsent />
    </AuthProvider>
  );
}
