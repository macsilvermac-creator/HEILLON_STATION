import { MissionPlanner } from "@/components/MissionPlanner";

export function EliteFeaturesSection() {
  return (
    <section id="workspace" className="relative z-10 mx-auto mt-8 max-w-6xl px-5 pb-20">
      <div className="glass-card glass-card-hover p-8 lg:p-10">
        <div className="mb-8 flex flex-col gap-2">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-gold-500/85">Espaço de análise</p>
          <h2 className="text-3xl font-semibold text-white">Inicie a análise de um caso</h2>
          <p className="max-w-2xl text-sm text-white/55">
            Descreva o caso em linguagem natural. O Heillon planeia a análise e mantém um registo
            de auditoria HDR de cada passo — pronto para verificação pública.
          </p>
        </div>
        <MissionPlanner />
      </div>
    </section>
  );
}
