import { Resume, Strategy } from "@/lib/types";

const fmt = (n: number) =>
  new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);

const fmtPct = (n: number | null | undefined) =>
  n === null || n === undefined ? "—" : `${n.toFixed(2)} %`;

const emphasis = (v: number) =>
  v > 0 ? "text-emerald-100" : v < 0 ? "text-red-100" : "text-blue-100";

export default function ResumeBar({
  resume,
  strategy,
}: {
  resume: Resume;
  strategy?: Strategy | null;
}) {
  const items = [
    { label: "Prix d'achat", value: fmt(resume.prix_achat) },
    { label: "Frais de notaire", value: fmt(resume.frais_notaire) },
    { label: "Coût total", value: fmt(resume.cout_total) },
    { label: "Emprunt", value: fmt(resume.emprunt) },
    { label: "Mensualité", value: fmt(resume.mensualite) + "/mois" },
    { label: "Loyer brut", value: fmt(resume.loyer_mensuel_brut) + "/mois" },
  ];

  return (
    <div className="bg-blue-700 rounded-xl p-4 space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {items.map((item) => (
          <div key={item.label} className="text-center">
            <p className="text-blue-200 text-xs">{item.label}</p>
            <p className="text-white font-bold text-sm mt-0.5 whitespace-nowrap">{item.value}</p>
          </div>
        ))}
      </div>

      <div className="rounded-lg border border-blue-500/50 bg-blue-800/40 p-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wide text-blue-200">
              Indicateurs a privilegier
            </p>
            <p className="text-xs text-blue-100 mt-0.5">
              TRI net + cash flow + stress test
            </p>
          </div>
          {strategy && (
            <span className="rounded-full bg-white/10 px-2.5 py-1 text-[11px] font-medium text-white">
              Strategie: {strategy.nom}
            </span>
          )}
        </div>

        <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
          <div className="rounded-md bg-white/5 px-3 py-2">
            <p className="text-[11px] text-blue-200">TRI net</p>
            <p className="mt-0.5 font-bold text-white">{fmtPct(strategy?.tri)}</p>
          </div>
          <div className="rounded-md bg-white/5 px-3 py-2">
            <p className="text-[11px] text-blue-200">Cash flow moyen</p>
            <p className={`mt-0.5 font-bold ${strategy ? emphasis(strategy.cash_flow_moyen) : "text-white"}`}>
              {strategy ? `${fmt(strategy.cash_flow_moyen)}/mois` : "—"}
            </p>
          </div>
          <div className="rounded-md bg-white/5 px-3 py-2">
            <p className="text-[11px] text-blue-200">Stress test</p>
            <p className="mt-0.5 font-bold text-white">A verifier</p>
            <p className="text-[11px] text-blue-200 mt-0.5">Vacance, loyers, charges, revente</p>
          </div>
        </div>
      </div>
    </div>
  );
}
