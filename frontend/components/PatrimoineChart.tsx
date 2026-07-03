"use client";

import { Strategy } from "@/lib/types";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
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

export default function PatrimoineChart({ strategies, horizon }: Props) {
  const data = Array.from({ length: horizon }, (_, i) => {
    const an = i + 1;
    const point: Record<string, number | string> = { an: `An ${an}` };
    for (const s of strategies) {
      const row = s.yearly[i];
      if (row) point[s.id] = row.patrimoine_net;
    }
    return point;
  });

  return (
    <div className="bg-white rounded-xl shadow-sm p-4">
      <h2 className="font-semibold text-slate-700 mb-4 text-sm">Patrimoine net par stratégie (€)</h2>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="an" tick={{ fontSize: 11 }} interval={Math.floor(horizon / 5)} />
          <YAxis tickFormatter={fmt} tick={{ fontSize: 11 }} width={70} />
          <Tooltip formatter={(v: number) => fmt(v)} />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          {strategies.map((s) => (
            <Line
              key={s.id}
              type="monotone"
              dataKey={s.id}
              name={s.nom}
              stroke={COLORS[s.id]}
              strokeWidth={2}
              dot={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
