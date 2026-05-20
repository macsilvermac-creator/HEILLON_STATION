import { HeroSection } from "@/components/HeroSection";

import { EliteFeaturesSection } from "@/components/EliteFeaturesSection";
import { EliteStatsStrip } from "@/components/EliteStatsStrip";

export default function EliteMissionHome() {
  return (
    <div className="relative pb-28">
      <HeroSection />
      <EliteStatsStrip />
      <EliteFeaturesSection />
    </div>
  );
}
