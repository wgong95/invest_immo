import { Strategy } from "@/lib/types";
import clsx from "clsx";

const fmt = (n: number) =>
  new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);

const COLORS: Record<string, string> = {
  location_nue: "border-sky-400",
  lmnp_meuble: "border-emerald-400",
  airbnb: "border-orange-400",
  scpi: "border-purple-400",
  residence_principale: "border-rose-400",
};

const BG: Record<string, string> = {
  location_nue: "bg-sky-50",
  lmnp_meuble: "bg-emerald-50",
  airbnb: "bg-orange-50",
  scpi: "bg-purple-50",
  residence_principale: "bg-rose-50",
};

const BADGE: Record<string, string> = {
  location_nue: "bg-sky-100 text-sky-800",
  lmnp_meuble: "bg-emerald-100 text-emerald-800",
  airbnb: "bg-orange-100 text-orange-800",
  scpi: "bg-purple-100 text-purple-800",
  residence_principale: "bg-rose-100 text-rose-800",
};

interface Props {
  strategies: Strategy[];
  activeId: string | null;
  onSelect: (id: string | null) => void;
}

export default function StrategyCards({ strategies, activeId, onSelect }: Props) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4">
      {strategies.map((s) => {
        const isActive = activeId === s.id;
        return (
          <button
            key={s.id}
            onClick={() => onSelect(isActive ? null : s.id)}
            className={clsx(
              "text-left rounded-xl border-l-4 p-4 transition-all shadow-sm hover:shadow-md",
              COLORS[s.id],
              isActive ? BG[s.id] + " ring-2 ring-offset-1 ring-blue-500" : "bg-white"
            )}
          >
            <div className="flex items-start justify-between mb-2">
              <span className={clsx("text-xs font-semibold px-2 py-0.5 rounded-full", BADGE[s.id])}>
                {s.nom}
              </span>
              <div className="flex flex-col items-end gap-1">
                {s.tri !== null && (
                  <span className="text-xs font-bold text-slate-600">TRI {s.tri}%</span>
                )}
                {s.is_recommended && (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">
                    Recommandé
                  </span>
                )}
              </div>
            </div>

            <Metric label="Cash flow moy." value={fmt(s.cash_flow_moyen) + "/mois"} positive={s.cash_flow_moyen >= 0} />
            <Metric label="Patrimoine final" value={fmt(s.patrimoine_net_final)} positive />
            <Metric label="VAN" value={fmt(s.van)} positive={s.van >= 0} />
            <Metric
              label="DSCR (an 1)"
              value={s.dscr === null ? "—" : s.dscr.toFixed(2) + "x"}
              positive={s.dscr === null ? undefined : s.dscr >= 1}
            />
            <Metric
              label="CoC (an 1)"
              value={s.coc_return_pct.toFixed(2) + " %"}
              positive={s.coc_return_pct >= 0}
            />
            <Metric label="Stress VAN" value={fmt(s.stress_van)} positive={s.stress_van >= 0} />
            {s.mensualite > 0 && (
              <Metric label="Mensualité crédit" value={fmt(s.mensualite) + "/mois"} />
            )}
            {s.loyer_mensuel > 0 && (
              <Metric label="Loyer mensuel" value={fmt(s.loyer_mensuel) + "/mois"} />
            )}
            <Metric
              label="Rent. nette période"
              value={s.rentabilite_nette_sur_periode.toFixed(2) + " %"}
            />

            <p className={clsx("text-[11px] mt-1", s.is_candidate ? "text-emerald-700" : "text-red-600")}>
              {s.is_candidate ? "Candidat (VAN > 0)" : "Hors candidat (VAN <= 0)"}
              {" · "}
              {s.stress_pass ? "Stress: OK" : "Stress: fragile"}
            </p>

            <p className="text-xs text-slate-400 mt-2 leading-snug">{s.description}</p>
            <p className="text-xs text-blue-600 mt-1 font-medium">
              {isActive ? "▲ Masquer le détail" : "▼ Voir le détail"}
            </p>
          </button>
        );
      })}
    </div>
  );
}

function Metric({ label, value, positive }: { label: string; value: string; positive?: boolean }) {
  return (
    <div className="flex justify-between items-baseline mb-0.5">
      <span className="text-xs text-slate-500">{label}</span>
      <span className={clsx("text-sm font-bold", positive === false ? "text-red-600" : positive === true ? "text-slate-800" : "text-slate-700")}>
        {value}
      </span>
    </div>
  );
}
