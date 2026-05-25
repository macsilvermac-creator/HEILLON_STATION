"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const PIE_COLORS = ["#d4af37", "#34d399", "#60a5fa", "#f472b6", "#a78bfa", "#fb923c", "#94a3b8"];

interface LifecycleEntry {
  name: string;
  v: number;
}
interface AgentEntry {
  name: string;
  value: number;
}

interface Props {
  lifecycleData: LifecycleEntry[];
  agentPieData: AgentEntry[];
}

export default function DashboardCharts({ lifecycleData, agentPieData }: Props) {
  return (
    <div className="mb-10 grid gap-6 lg:grid-cols-2">
      <div className="glass-elite rounded-2xl border border-white/10 p-5">
        <h3 className="text-sm font-semibold text-white">Ciclo das análises</h3>
        <p className="mt-1 text-[11px] text-white/40">Distribuição agregada no período.</p>
        <div className="mt-4 h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={lifecycleData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
              <XAxis dataKey="name" tick={{ fill: "rgba(255,255,255,0.45)", fontSize: 11 }} />
              <YAxis tick={{ fill: "rgba(255,255,255,0.35)", fontSize: 10 }} allowDecimals={false} />
              <Tooltip
                contentStyle={{
                  background: "rgba(15,23,42,0.95)",
                  border: "1px solid rgba(255,255,255,0.12)",
                  borderRadius: "12px",
                  fontSize: "12px",
                }}
              />
              <Bar dataKey="v" fill="#d4af37" radius={[6, 6, 0, 0]} name="Missões" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="glass-elite rounded-2xl border border-white/10 p-5">
        <h3 className="text-sm font-semibold text-white">Assistentes utilizados</h3>
        <p className="mt-1 text-[11px] text-white/40">Frequência relativa no período.</p>
        <div className="mt-4 h-56 w-full">
          {agentPieData.length ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={agentPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={72} label>
                  {agentPieData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} stroke="rgba(0,0,0,0.2)" />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "rgba(15,23,42,0.95)",
                    border: "1px solid rgba(255,255,255,0.12)",
                    borderRadius: "12px",
                    fontSize: "12px",
                  }}
                />
                <Legend wrapperStyle={{ fontSize: "11px", color: "rgba(255,255,255,0.55)" }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-full items-center justify-center text-xs text-white/40">
              Sem frequências de agente — execute missões para povoar.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
