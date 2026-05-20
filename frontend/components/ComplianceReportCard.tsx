"use client";

type CompliancePreview = {
  mission_id?: string;
  framework_id?: string;
  framework_name?: string;
  total_hdrs?: number;
  compliant_hdrs?: number;
  generated_at?: string;
};

interface ComplianceReportCardProps {
  report: CompliancePreview | null;
  error?: string | null;
  busy?: boolean;
}

export function ComplianceReportCard({ report, error, busy }: ComplianceReportCardProps) {
  if (busy) {
    return (
      <div className="rounded-xl border border-white/10 bg-white/[0.04] p-4 text-xs text-white/60">
        A gerar relatório de conformidade…
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-500/30 bg-rose-950/40 p-4 text-xs text-rose-200">{error}</div>
    );
  }

  if (!report) {
    return (
      <div className="rounded-xl border border-white/10 bg-white/[0.04] p-4 text-xs text-white/50">
        Gere um relatório para esta missão (âncoras normativas pós-execução).
      </div>
    );
  }

  const total = report.total_hdrs ?? 0;
  const compliant = report.compliant_hdrs ?? 0;
  const rate = total > 0 ? Math.round((compliant / total) * 100) : 0;

  return (
    <div className="space-y-3 rounded-xl border border-gold-500/35 bg-deep-space-800/70 p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="text-xs font-semibold uppercase tracking-widest text-gold-400">Relatório</span>
        <span className="font-mono text-[11px] text-white/55">{report.framework_id}</span>
      </div>
      <h3 className="text-sm font-semibold text-white">{report.framework_name}</h3>
      <dl className="grid grid-cols-2 gap-3 text-[11px] text-white/65">
        <div>
          <dt className="text-white/40">HDRs</dt>
          <dd className="font-medium text-emerald-200">{total}</dd>
        </div>
        <div>
          <dt className="text-white/40">Compliant (heur.)</dt>
          <dd className="font-medium text-emerald-200">
            {compliant} ({rate}%)
          </dd>
        </div>
      </dl>
      {report.generated_at ? (
        <p className="text-[10px] text-white/35">Gerado em {report.generated_at}</p>
      ) : null}
    </div>
  );
}
