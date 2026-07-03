import { Strategy, YearlyRow } from "@/lib/types";

const fmtE = (n: number | undefined) =>
  n === undefined
    ? "—"
    : new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);

const fmtPct = (n: number | undefined) =>
  n === undefined ? "—" : `${n.toFixed(2)} %`;

const bg = (v: number) =>
  v > 0 ? "text-emerald-700 font-semibold" : v < 0 ? "text-red-600 font-semibold" : "";

const LABEL: Record<string, string> = {
  location_nue: "Location Nue",
  lmnp_meuble: "LMNP Meublé",
  airbnb: "Location Courte Durée",
  scpi: "SCPI",
  residence_principale: "Résidence Principale",
};

type StrategyId = Strategy["id"];

function hintText(
  strategyId: StrategyId,
  column: "interets" | "charges" | "mensualite" | "impot" | "cashflow" | "amortissement"
): string {
  if (column === "interets") {
    return "Somme des intérêts du crédit sur l'année (12 mois du tableau d'amortissement).";
  }

  if (column === "mensualite") {
    return "Mensualité annuelle = mensualité de crédit x 12 pendant la durée du prêt, puis 0 après.";
  }

  if (column === "cashflow") {
    if (strategyId === "scpi") {
      return "Cash flow/mois = (revenus SCPI - impôt) / 12, arrondi à l'euro.";
    }
    if (strategyId === "residence_principale") {
      return "Cash flow/mois = (loyer économisé - mensualité - charges - taxe foncière) / 12, arrondi à l'euro.";
    }
    return "Cash flow/mois = (loyer annuel - mensualité - charges - impôt) / 12, arrondi à l'euro.";
  }

  if (column === "amortissement") {
    return "LMNP: amortissement comptable (bien + mobilier). Réduit la base imposable, sans sortie de trésorerie.";
  }

  if (column === "charges") {
    if (strategyId === "airbnb") {
      return "Charges annuelles = copropriété + taxe foncière + frais plateforme + conciergerie + ménage.";
    }
    if (strategyId === "scpi") {
      return "SCPI: pas de charges d'exploitation affichées dans ce tableau.";
    }
    if (strategyId === "residence_principale") {
      return "Charges annuelles = copropriété + taxe foncière.";
    }
    return "Charges annuelles = copropriété + taxe foncière + gestion locative éventuelle.";
  }

  if (strategyId === "location_nue") {
    return "Location nue: impôt sur revenu foncier net. Si déficit, avantage fiscal plafonné (10 700 EUR/an).";
  }
  if (strategyId === "lmnp_meuble" || strategyId === "airbnb") {
    return "LMNP/BIC: impôt = BIC imposable x (TMI + prélèvements sociaux). Si BIC <= 0, impôt = 0.";
  }
  if (strategyId === "scpi") {
    return "SCPI: impôt = revenus SCPI x (TMI + prélèvements sociaux).";
  }
  return "Résidence principale: pas d'impôt locatif dans ce modèle.";
}

function HintHeader({
  label,
  hint,
  alignLeft,
}: {
  label: string;
  hint: string;
  alignLeft?: boolean;
}) {
  return (
    <th className={`${alignLeft ? "text-left" : "text-right"} px-3 py-2 font-medium`}>
      <span className={`inline-flex items-center gap-1.5 ${alignLeft ? "" : "justify-end"} group relative`}>
        <span>{label}</span>
        <button
          type="button"
          aria-label={`Aide calcul ${label}`}
          className="h-4 w-4 rounded-full border border-slate-300 text-[10px] leading-none text-slate-500 bg-white hover:bg-slate-100"
        >
          i
        </button>
        <span
          role="tooltip"
          className={`pointer-events-none absolute z-20 w-64 rounded-md border border-slate-200 bg-white p-2 text-[11px] font-normal text-slate-600 shadow-lg opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100 ${alignLeft ? "left-0 top-full mt-1 text-left" : "right-0 top-full mt-1 text-left"}`}
        >
          {hint}
        </span>
      </span>
    </th>
  );
}

export default function DetailTable({ strategy }: { strategy: Strategy }) {
  const isScpi = strategy.id === "scpi";
  const isRp = strategy.id === "residence_principale";

  return (
    <div className="bg-white rounded-xl shadow-sm p-4 overflow-x-auto">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-semibold text-slate-700 text-sm">
          Détail annuel — {LABEL[strategy.id] ?? strategy.nom}
        </h2>
        <div className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
          Rendement brut: {strategy.rendement_brut.toFixed(2)} %
        </div>
      </div>
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="bg-slate-50 text-slate-500 text-right">
            <th className="text-left px-3 py-2 font-medium">Année</th>
            {!isScpi && !isRp && <th className="px-3 py-2 font-medium">Loyer annuel</th>}
            {isRp && <th className="px-3 py-2 font-medium">Loyer économisé</th>}
            {isScpi && <th className="px-3 py-2 font-medium">Revenus SCPI</th>}
            {!isScpi && !isRp && (
              <HintHeader label="Intérêts" hint={hintText(strategy.id, "interets")} />
            )}
            <HintHeader label="Charges" hint={hintText(strategy.id, "charges")} />
            {!isScpi && (
              <HintHeader label="Mensualité" hint={hintText(strategy.id, "mensualite")} />
            )}
            {strategy.id === "lmnp_meuble" && (
              <HintHeader label="Amortissement" hint={hintText(strategy.id, "amortissement")} />
            )}
            <HintHeader label="Impôt" hint={hintText(strategy.id, "impot")} />
            <HintHeader label="Cash flow/mois" hint={hintText(strategy.id, "cashflow")} />
            <th className="px-3 py-2 font-medium">Rent. nette locative</th>
            <th className="px-3 py-2 font-medium">Rent. nette totale</th>
            <th className="px-3 py-2 font-medium">Rent. nette après financement</th>
            <th className="px-3 py-2 font-medium">Cash flow yield</th>
            {!isScpi && <th className="px-3 py-2 font-medium">Valeur bien</th>}
            {!isScpi && <th className="px-3 py-2 font-medium">Capital restant</th>}
            <th className="px-3 py-2 font-medium">Patrimoine net</th>
          </tr>
        </thead>
        <tbody>
          {strategy.yearly.map((row: YearlyRow) => (
            <tr key={row.annee} className="border-t border-slate-100 hover:bg-slate-50 text-right">
              <td className="text-left px-3 py-1.5 font-medium text-slate-700">An {row.annee}</td>
              {!isScpi && !isRp && <td className="px-3 py-1.5">{fmtE(row.loyer_annuel)}</td>}
              {isRp && <td className="px-3 py-1.5">{fmtE(row.loyer_economise)}</td>}
              {isScpi && <td className="px-3 py-1.5">{fmtE(row.loyer_annuel)}</td>}
              {!isScpi && !isRp && <td className="px-3 py-1.5 text-red-500">{fmtE(row.interets)}</td>}
              <td className="px-3 py-1.5 text-red-500">{fmtE(row.charges)}</td>
              {!isScpi && <td className="px-3 py-1.5 text-red-500">{fmtE(row.mensualite_an)}</td>}
              {strategy.id === "lmnp_meuble" && <td className="px-3 py-1.5 text-slate-400">{fmtE(row.amortissement)}</td>}
              <td className="px-3 py-1.5 text-red-500">{fmtE(row.impot)}</td>
              <td className={`px-3 py-1.5 ${bg(Math.round(row.cash_flow / 12))}`}>
                {fmtE(Math.round(row.cash_flow / 12))}
              </td>
              <td className="px-3 py-1.5">{fmtPct(row.rentabilite_nette_locative_hors_revalo_pct)}</td>
              <td className="px-3 py-1.5">{fmtPct(row.rentabilite_nette_totale_avec_revalo_pct)}</td>
              <td className="px-3 py-1.5">{fmtPct(row.rentabilite_nette_apres_financement_pct)}</td>
              <td className="px-3 py-1.5">{fmtPct(row.cash_flow_yield_pct)}</td>
              {!isScpi && <td className="px-3 py-1.5">{fmtE(row.valeur_bien)}</td>}
              {!isScpi && <td className="px-3 py-1.5 text-red-400">{fmtE(row.capital_restant)}</td>}
              <td className={`px-3 py-1.5 font-semibold ${row.patrimoine_net > 0 ? "text-emerald-700" : "text-red-600"}`}>
                {fmtE(row.patrimoine_net)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
