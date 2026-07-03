import { AnalyseResult, FlatConfig } from "@/lib/types";

interface FlatAnalysis {
  flat: FlatConfig;
  result: AnalyseResult;
}

const fmtE = (n: number) =>
  new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);

const fmtPct = (n: number) => `${n.toFixed(1)}%`;

export default function FlatComparisonSummary({ analyses }: { analyses: FlatAnalysis[] }) {
  if (analyses.length === 0) return null;

  return (
    <div className="bg-white rounded-xl shadow-sm p-4 overflow-x-auto">
      <h2 className="font-semibold text-slate-700 mb-3 text-sm">Comparatif multi-biens (vue rapide)</h2>
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="bg-slate-50 text-slate-500 text-right">
            <th className="text-left px-3 py-2 font-medium">Bien</th>
            <th className="px-3 py-2 font-medium">Prix total</th>
            <th className="px-3 py-2 font-medium">Charges/an</th>
            <th className="px-3 py-2 font-medium">Taxe fonciere/an</th>
            <th className="px-3 py-2 font-medium">Notaire</th>
            <th className="text-left px-3 py-2 font-medium">Meilleure strategie (TRI)</th>
            <th className="px-3 py-2 font-medium">TRI</th>
            <th className="px-3 py-2 font-medium">Cash flow moy.</th>
            <th className="px-3 py-2 font-medium">Patrimoine final</th>
          </tr>
        </thead>
        <tbody>
          {analyses.map(({ flat, result }) => {
            const bestByTri = [...result.strategies]
              .filter((s) => s.tri !== null)
              .sort((a, b) => (b.tri ?? -999) - (a.tri ?? -999))[0] ?? result.strategies[0];
            return (
              <tr key={flat.id} className="border-t border-slate-100 hover:bg-slate-50 text-right">
                <td className="text-left px-3 py-1.5 font-medium text-slate-700">{flat.name}</td>
                <td className="px-3 py-1.5">{fmtE(Math.round(flat.prix_m2_achat * flat.surface))}</td>
                <td className="px-3 py-1.5">{fmtE(Math.round(flat.charges_copro_mensuelle * 12))}</td>
                <td className="px-3 py-1.5">{fmtE(Math.round(flat.taxe_fonciere_mensuelle * 12))}</td>
                <td className="px-3 py-1.5">{fmtPct(flat.frais_notaire_pct)}</td>
                <td className="text-left px-3 py-1.5">{bestByTri.nom}</td>
                <td className="px-3 py-1.5">{bestByTri.tri !== null ? `${bestByTri.tri}%` : "N/A"}</td>
                <td className={`px-3 py-1.5 ${bestByTri.cash_flow_moyen >= 0 ? "text-emerald-700" : "text-red-600"}`}>
                  {fmtE(bestByTri.cash_flow_moyen)}/mois
                </td>
                <td className="px-3 py-1.5 font-semibold">{fmtE(bestByTri.patrimoine_net_final)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
