import { MissionPlanner } from "@/components/MissionPlanner";

export function EliteFeaturesSection() {
  return (
    <section id="workspace" className="relative z-10 mx-auto mt-[-40px] max-w-6xl px-5 pb-20 lg:mt-[-80px]">
      <div className="glass-card glass-card-hover p-8 lg:p-10">
        <div className="mb-8 flex flex-col gap-2">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-gold-500/85">Easy Orchestration</p>
          <h2 className="text-3xl font-semibold text-white">Modo Missão em painel líquido</h2>
          <p className="max-w-2xl text-sm text-white/55">
            O planeador comunica diretamente com{" "}
            <span className="font-mono text-xs text-white/85">POST /mission/plan</span> e mantém auditoria HDR para cada execução
            EASY.
          </p>
        </div>
        <MissionPlanner />
      </div>
    </section>
  );
}
