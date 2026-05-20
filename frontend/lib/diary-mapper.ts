import type { TimelineEvent } from "@/components/GlassTimeline";

type MissionLite = Record<string, unknown>;

type DagNodeLite = {
  node_id?: string;
  agent_id?: string;
  description?: string;
};

function statusForMission(meta: MissionLite): TimelineEvent["status"] {
  const raw = typeof meta.status === "string" ? meta.status.toLowerCase() : "pending";
  if (raw === "completed") return "completed";
  if (raw === "failed" || raw === "aborted") return "failed";

  const normative = meta.normative_result as { allowed?: boolean } | undefined;
  if (normative && normative.allowed === false && raw !== "pending") return "blocked";

  if (raw === "pending") return "pending";
  return "pending";
}

function primaryTimestamp(meta: MissionLite): string {
  const cand =
    (meta.completed_at as string | undefined) ||
    (meta.executed_at as string | undefined) ||
    (meta.approved_at as string | undefined) ||
    (meta.created_at as string | undefined) ||
    new Date().toISOString();

  return typeof cand === "string" ? cand : new Date().toISOString();
}

export function buildTimelineEntries(missions: MissionLite[]): TimelineEvent[] {
  const flattened: TimelineEvent[] = [];

  for (const mission of missions) {
    const hdrsRaw = mission.hdrs_generated;
    const hdrs = Array.isArray(hdrsRaw) ? (hdrsRaw as string[]) : [];
    const dag = mission.dag as { nodes?: DagNodeLite[] } | undefined;
    const nodes = Array.isArray(dag?.nodes) ? dag!.nodes! : [];

    const descriptionText = typeof mission.description === "string" ? mission.description : "Missão EASY";
    const missionStatus = statusForMission(mission);
    const missionIdShort = typeof mission.mission_id === "string" ? mission.mission_id : "unknown";

    if (hdrs.length && nodes.length) {
      hdrs.forEach((hdrId, index) => {
        const node = nodes[index];
        flattened.push({
          id: `${missionIdShort}-${hdrId}-${index}`,
          title: `${node?.agent_id ?? "agent"} — passo ${index + 1}`,
          description:
            typeof node?.description === "string" ? node.description : `${descriptionText} (execução HDR ${hdrId.slice(0, 10)}…)`,
          timestamp: primaryTimestamp(mission),
          status: hdrId ? missionStatus : missionStatus === "blocked" ? "blocked" : "pending",
          agent: typeof node?.agent_id === "string" ? node.agent_id : "unknown-agent",
          hdrId,
        });
      });

      continue;
    }

    if (hdrs.length) {
      hdrs.forEach((hdrId, index) =>
        flattened.push({
          id: `${missionIdShort}-${hdrId}`,
          title: `${missionIdShort} · HDR ${index + 1}`,
          description: descriptionText.slice(0, 240),
          timestamp: primaryTimestamp(mission),
          status: missionStatus,
          agent: nodes[0]?.agent_id ?? "multi-agent",
          hdrId,
        }),
      );

      continue;
    }

    flattened.push({
      id: `${missionIdShort}-summary`,
      title: `${descriptionText.slice(0, 120)}`,
      description: `Estado dossier EASY: ${typeof mission.status === "string" ? mission.status : "?"}. Planeie, aprove e execute para minerar HDRs verificáveis.`,
      timestamp: primaryTimestamp(mission),
      status: missionStatus,
      agent: nodes[0]?.agent_id ?? "planeamento",
      hdrId: "",
    });
  }

  return flattened.slice(0, 80);
}
