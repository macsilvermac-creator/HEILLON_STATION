import { AuditPackageDownloader } from "@/components/AuditPackageDownloader";
import { HDRChain } from "@/components/HDRChain";

export default async function MissionDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: missionId } = await params;

  return (
    <div className="mx-auto max-w-5xl space-y-10 px-4 pb-28 pt-32 sm:px-6 md:pt-36 lg:pb-36">
      <div>
        <h1 className="text-gradient text-3xl font-semibold tracking-tight">Missão `{missionId}`</h1>
        <p className="mt-2 text-sm text-white/60">
          Corrente de custódia computacional com registos HDR encadeados e pacote forense PDF/A + manifesto JSON.
        </p>
      </div>
      <HDRChain missionId={missionId} />
      <AuditPackageDownloader missionId={missionId} />
    </div>
  );
}
