import { EliteFeaturesSection } from "@/components/EliteFeaturesSection";
import { EliteStatsStrip } from "@/components/EliteStatsStrip";

export default function EliteMissionHome() {
  return (
    <div className="relative pt-10 pb-28">
      <EliteStatsStrip />
      <EliteFeaturesSection />
    </div>
  );
}
