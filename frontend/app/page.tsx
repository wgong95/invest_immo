"use client";

import { useState, useCallback } from "react";
import { analyser } from "@/lib/api";
import { Params, AnalyseResult, FlatConfig } from "@/lib/types";
import ParamPanel from "@/components/ParamPanel";
import StrategyCards from "@/components/StrategyCards";
import PatrimoineChart from "@/components/PatrimoineChart";
import CashFlowChart from "@/components/CashFlowChart";
import DetailTable from "@/components/DetailTable";
import ResumeBar from "@/components/ResumeBar";
import FlatComparePanel from "@/components/FlatComparePanel";
import FlatComparisonSummary from "@/components/FlatComparisonSummary";
import { exportComparisonExcel, exportComparisonPdf } from "@/lib/report";

const DEFAULT_PARAMS: Params = {
  apport: 250000,
  taux_interet: 3.3,
  revenu_mensuel_brut: 7000,
  prix_m2_achat: 11429,
  loyer_m2: 38.5,
  loyer_meuble_m2: 43,
  surface: 29.75,
  duree_pret_ans: 10,
  frais_notaire_pct: 8.0,
  charges_copro_mensuelle: 150,
  taxe_fonciere_mensuelle: 125,
  vacance_locative_pct: 5,
  gestion_locative_pct: 0,
  tmi: 30,
  revalorisation_bien_pct: 3.0,
  revalorisation_loyer_pct: 0.5,
  horizon_ans: 20,
  rendement_scpi: 4,
  taux_actualisation: 4.0,
};

type FlatAnalysis = {
  flat: FlatConfig;
  result: AnalyseResult;
};

function createDefaultFlats(params: Params): FlatConfig[] {
  return [
    {
      id: "flat_1",
      name: "Bien A",
      enabled: true,
      prix_m2_achat: params.prix_m2_achat,
      loyer_m2: params.loyer_m2,
      loyer_meuble_m2: params.loyer_meuble_m2,
      surface: params.surface,
      frais_notaire_pct: params.frais_notaire_pct,
      charges_copro_mensuelle: params.charges_copro_mensuelle,
      taxe_fonciere_mensuelle: params.taxe_fonciere_mensuelle,
      vacance_locative_pct: params.vacance_locative_pct,
      gestion_locative_pct: params.gestion_locative_pct,
    },
    {
      id: "flat_2",
      name: "Bien B",
      enabled: false,
      prix_m2_achat: params.prix_m2_achat,
      loyer_m2: params.loyer_m2,
      loyer_meuble_m2: params.loyer_meuble_m2,
      surface: params.surface,
      frais_notaire_pct: params.frais_notaire_pct,
      charges_copro_mensuelle: params.charges_copro_mensuelle,
      taxe_fonciere_mensuelle: params.taxe_fonciere_mensuelle,
      vacance_locative_pct: params.vacance_locative_pct,
      gestion_locative_pct: params.gestion_locative_pct,
    },
    {
      id: "flat_3",
      name: "Bien C",
      enabled: false,
      prix_m2_achat: params.prix_m2_achat,
      loyer_m2: params.loyer_m2,
      loyer_meuble_m2: params.loyer_meuble_m2,
      surface: params.surface,
      frais_notaire_pct: params.frais_notaire_pct,
      charges_copro_mensuelle: params.charges_copro_mensuelle,
      taxe_fonciere_mensuelle: params.taxe_fonciere_mensuelle,
      vacance_locative_pct: params.vacance_locative_pct,
      gestion_locative_pct: params.gestion_locative_pct,
    },
    {
      id: "flat_4",
      name: "Bien D",
      enabled: false,
      prix_m2_achat: params.prix_m2_achat,
      loyer_m2: params.loyer_m2,
      loyer_meuble_m2: params.loyer_meuble_m2,
      surface: params.surface,
      frais_notaire_pct: params.frais_notaire_pct,
      charges_copro_mensuelle: params.charges_copro_mensuelle,
      taxe_fonciere_mensuelle: params.taxe_fonciere_mensuelle,
      vacance_locative_pct: params.vacance_locative_pct,
      gestion_locative_pct: params.gestion_locative_pct,
    },
  ];
}

export default function Home() {
  const [params, setParams] = useState<Params>(DEFAULT_PARAMS);
  const [flats, setFlats] = useState<FlatConfig[]>(() => createDefaultFlats(DEFAULT_PARAMS));
  const [analyses, setAnalyses] = useState<FlatAnalysis[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeFlatId, setActiveFlatId] = useState<string | null>(null);
  const [activeStrategyByFlat, setActiveStrategyByFlat] = useState<Record<string, string | null>>({});

  const run = useCallback(async (p: Params) => {
    const enabledFlats = flats.filter((f) => f.enabled).slice(0, 4);
    if (enabledFlats.length === 0) {
      setError("Activez au moins un bien a comparer.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const nextAnalyses = await Promise.all(
        enabledFlats.map(async (flat) => {
          const overridden: Params = {
            ...p,
            prix_m2_achat: flat.prix_m2_achat,
            loyer_m2: flat.loyer_m2,
            loyer_meuble_m2: flat.loyer_meuble_m2,
            surface: flat.surface,
            frais_notaire_pct: flat.frais_notaire_pct,
            charges_copro_mensuelle: flat.charges_copro_mensuelle,
            taxe_fonciere_mensuelle: flat.taxe_fonciere_mensuelle,
            vacance_locative_pct: flat.vacance_locative_pct,
            gestion_locative_pct: flat.gestion_locative_pct,
          };
          const result = await analyser(overridden);
          return { flat, result };
        })
      );

      setAnalyses(nextAnalyses);
      setActiveFlatId(nextAnalyses[0]?.flat.id ?? null);
      setActiveStrategyByFlat(Object.fromEntries(nextAnalyses.map((entry) => [entry.flat.id, null])));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  }, [flats]);

  const handleChange = (p: Params) => {
    setParams(p);
  };

  const selected = analyses.find((entry) => entry.flat.id === activeFlatId) ?? analyses[0] ?? null;
  const activeStrategy = selected ? activeStrategyByFlat[selected.flat.id] ?? null : null;
  const featuredStrategy = selected
    ? selected.result.strategies.find((s) => s.id === activeStrategy) ?? selected.result.strategies[0] ?? null
    : null;

  const setActiveStrategy = (strategyId: string | null) => {
    if (!selected) return;
    setActiveStrategyByFlat((prev) => ({ ...prev, [selected.flat.id]: strategyId }));
  };

  return (
    <div className="flex min-h-screen">
      {/* Left sidebar — parameters */}
      <aside className="w-[360px] shrink-0 bg-white border-r border-slate-200 flex flex-col">
        <div className="p-4 border-b border-slate-200 bg-blue-700">
          <h1 className="text-white font-bold text-lg leading-tight">
            Invest Immo Paris
          </h1>
          <p className="text-blue-200 text-xs mt-0.5">Analyse de stratégies locatives</p>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          <ParamPanel params={params} onChange={handleChange} />
          <div className="mt-5 pt-4 border-t border-slate-200">
            <FlatComparePanel
              flats={flats}
              defaults={{
                prix_m2_achat: params.prix_m2_achat,
                loyer_m2: params.loyer_m2,
                loyer_meuble_m2: params.loyer_meuble_m2,
                surface: params.surface,
                frais_notaire_pct: params.frais_notaire_pct,
                charges_copro_mensuelle: params.charges_copro_mensuelle,
                taxe_fonciere_mensuelle: params.taxe_fonciere_mensuelle,
                vacance_locative_pct: params.vacance_locative_pct,
                gestion_locative_pct: params.gestion_locative_pct,
              }}
              onChange={setFlats}
            />
          </div>
        </div>
        <div className="p-4 border-t border-slate-200">
          <button
            onClick={() => run(params)}
            disabled={loading}
            className="w-full bg-blue-700 hover:bg-blue-800 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg transition-colors text-sm"
          >
            {loading ? "Calcul en cours..." : "Analyser les biens"}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto p-6">
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            {error} — Vérifiez que le backend est démarré sur le port 8000.
          </div>
        )}

        {analyses.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full min-h-[60vh] text-slate-400">
            <div className="text-6xl mb-4">🏙️</div>
            <p className="text-lg font-medium text-slate-500">
              Configurez vos hypotheses, activez jusqu'a 4 biens, puis lancez l'analyse.
            </p>
            <p className="text-sm mt-1">
              5 strategies seront comparees pour chaque bien : Location nue, LMNP, Airbnb, SCPI, Residence principale.
            </p>
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-700" />
          </div>
        )}

        {selected && !loading && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2 flex-wrap">
                {analyses.map((entry) => {
                  const isActive = selected.flat.id === entry.flat.id;
                  return (
                    <button
                      key={entry.flat.id}
                      onClick={() => setActiveFlatId(entry.flat.id)}
                      className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${
                        isActive
                          ? "bg-blue-700 text-white border-blue-700"
                          : "bg-white text-slate-600 border-slate-200 hover:border-blue-400"
                      }`}
                    >
                      {entry.flat.name}
                    </button>
                  );
                })}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => exportComparisonPdf(analyses)}
                  className="px-3 py-1.5 text-xs rounded-md bg-slate-800 text-white hover:bg-slate-900"
                >
                  Export PDF
                </button>
                <button
                  onClick={() => exportComparisonExcel(analyses)}
                  className="px-3 py-1.5 text-xs rounded-md bg-emerald-600 text-white hover:bg-emerald-700"
                >
                  Export Excel
                </button>
              </div>
            </div>

            <FlatComparisonSummary analyses={analyses} />
            <ResumeBar resume={selected.result.resume} strategy={featuredStrategy} />
            <StrategyCards
              strategies={selected.result.strategies}
              activeId={activeStrategy}
              onSelect={setActiveStrategy}
            />
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <PatrimoineChart strategies={selected.result.strategies} horizon={params.horizon_ans} />
              <CashFlowChart strategies={selected.result.strategies} horizon={params.horizon_ans} />
            </div>
            {activeStrategy && (
              <DetailTable
                strategy={selected.result.strategies.find((s) => s.id === activeStrategy)!}
              />
            )}
          </div>
        )}
      </main>
    </div>
  );
}
