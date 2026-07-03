"use client";

import { Strategy } from "@/lib/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

const COLORS: Record<string, string> = {
  location_nue: "#0ea5e9",
  lmnp_meuble: "#10b981",
  airbnb: "#f97316",
  scpi: "#a855f7",
  residence_principale: "#f43f5e",
};

const fmt = (v: number) =>
  new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", notation: "compact", maximumFractionDigits: 0 }).format(v);

interface Props {
  strategies: Strategy[];
  horizon: number;
}

export default function CashFlowChart({ strategies, horizon }: Props) {
  // Show every 5 years + year 1
  const years = [1, 5, 10, 15, 20].filter((y) => y <= horizon);

  const data = years.map((an) => {
    const point: Record<string, number | string> = { an: `An ${an}` };
    for (const s of strategies) {
      const row = s.yearly[an - 1];
      if (row) point[s.id] = Math.round(row.cash_flow / 12); // mensuel
    }
    return point;
  });

  return (
    <div className="bg-white rounded-xl shadow-sm p-4">
      <h2 className="font-semibold text-slate-700 mb-4 text-sm">Cash flow mensuel net par stratégie (€/mois)</h2>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="an" tick={{ fontSize: 11 }} />
          <YAxis tickFormatter={fmt} tick={{ fontSize: 11 }} width={70} />
          <Tooltip formatter={(v: number) => fmt(v)} />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          <ReferenceLine y={0} stroke="#94a3b8" strokeWidth={1.5} />
          {strategies.map((s) => (
            <Bar key={s.id} dataKey={s.id} name={s.nom} fill={COLORS[s.id]} radius={[2, 2, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
