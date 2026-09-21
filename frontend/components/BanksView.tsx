"use client";

import { useState } from "react";
import { compareLoans } from "@/lib/api";
import { LoanOffer, LoanOfferResult } from "@/lib/types";
import { exportLoanComparisonJson, exportLoanComparisonPdf } from "@/lib/report";

const fmt = (n: number) =>
  new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);

const fmtPct = (n: number | null | undefined) =>
  n === null || n === undefined ? "—" : `${n.toFixed(2)} %`;

let nextId = 3;

function makeOffer(id: string, nom: string): LoanOffer {
  return {
    id,
    nom,
    montant_emprunte: 177478,
    taux_interet: 3.36,
    taux_assurance: 0.17,
    duree_pret_ans: 20,
    frais_dossier: 900,
    frais_garantie: 2600,
  };
}

function NumberField({
  label,
  value,
  unit,
  onChange,
}: {
  label: string;
  value: number;
  unit?: string;
  onChange: (v: number) => void;
}) {
  const [raw, setRaw] = useState(String(value));

  const commit = (input: string) => {
    const normalized = input.replace(",", ".").trim();
    if (normalized === "" || normalized === "." || normalized === "-" || normalized === "-.") {
      return;
    }
    const parsed = Number(normalized);
    if (!Number.isFinite(parsed)) return;
    onChange(parsed);
  };

  return (
    <label className="flex flex-col gap-0.5 text-[11px] text-slate-500">
      {label}
      <div className="flex items-center gap-1">
        <input
          type="text"
          inputMode="decimal"
          value={raw}
          onChange={(e) => {
            setRaw(e.target.value);
            commit(e.target.value);
          }}
          onBlur={() => {
            commit(raw);
            setRaw(String(value));
          }}
          className="w-full border border-slate-200 rounded-md px-2 py-1 text-xs bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {unit && <span className="text-[10px] text-slate-400 whitespace-nowrap">{unit}</span>}
      </div>
    </label>
  );
}

export default function BanksView() {
  const [offers, setOffers] = useState<LoanOffer[]>([
    makeOffer("offer_1", "Banque A"),
    makeOffer("offer_2", "Banque B"),
  ]);
  const [results, setResults] = useState<LoanOfferResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateOffer = (id: string, patch: Partial<LoanOffer>) => {
    setOffers((prev) => prev.map((o) => (o.id === id ? { ...o, ...patch } : o)));
  };

  const addOffer = () => {
    const id = `offer_${nextId++}`;
    setOffers((prev) => [...prev, makeOffer(id, `Banque ${prev.length + 1}`)]);
  };

  const removeOffer = (id: string) => {
    setOffers((prev) => prev.filter((o) => o.id !== id));
    setResults((prev) => (prev ? prev.filter((r) => r.id !== id) : prev));
  };

  const compare = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await compareLoans(offers);
      setResults(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  };

  const bestId = results && results.length > 0
    ? results.reduce((best, r) => ((r.taeg ?? Infinity) < (best.taeg ?? Infinity) ? r : best)).id
    : null;

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800">Comparateur d&apos;offres de prêt</h1>
        <p className="text-sm text-slate-500 mt-1">
          Comparez le TAEG, la mensualité et le coût total du crédit entre plusieurs offres bancaires
          pour un même montant emprunté.
        </p>
      </div>

      <div className="space-y-3">
        {offers.map((offer, idx) => (
          <div key={offer.id} className="rounded-lg border border-slate-200 bg-white p-3 space-y-2">
            <div className="flex items-center justify-between">
              <input
                value={offer.nom}
                onChange={(e) => updateOffer(offer.id, { nom: e.target.value || `Banque ${idx + 1}` })}
                className="font-semibold text-sm border border-slate-200 rounded-md px-2 py-1 bg-slate-50"
              />
              {offers.length > 1 && (
                <button
                  onClick={() => removeOffer(offer.id)}
                  className="text-xs text-red-600 hover:text-red-800"
                >
                  Supprimer
                </button>
              )}
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
              <NumberField
                label="Montant emprunté"
                unit="€"
                value={offer.montant_emprunte}
                onChange={(v) => updateOffer(offer.id, { montant_emprunte: v })}
              />
              <NumberField
                label="Taux d'intérêt"
                unit="%"
                value={offer.taux_interet}
                onChange={(v) => updateOffer(offer.id, { taux_interet: v })}
              />
              <NumberField
                label="Taux d'assurance"
                unit="%"
                value={offer.taux_assurance}
                onChange={(v) => updateOffer(offer.id, { taux_assurance: v })}
              />
              <NumberField
                label="Durée"
                unit="ans"
                value={offer.duree_pret_ans}
                onChange={(v) => updateOffer(offer.id, { duree_pret_ans: Math.round(v) })}
              />
              <NumberField
                label="Frais de dossier"
                unit="€"
                value={offer.frais_dossier}
                onChange={(v) => updateOffer(offer.id, { frais_dossier: v })}
              />
              <NumberField
                label="Frais de garantie"
                unit="€"
                value={offer.frais_garantie}
                onChange={(v) => updateOffer(offer.id, { frais_garantie: v })}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={addOffer}
          className="px-3 py-1.5 text-xs rounded-md border border-slate-300 bg-white text-slate-700 hover:border-blue-400"
        >
          + Ajouter une offre
        </button>
        <button
          onClick={() => void compare()}
          disabled={loading || offers.length === 0}
          className="px-4 py-1.5 text-xs rounded-md bg-blue-700 text-white hover:bg-blue-800 disabled:opacity-50"
        >
          {loading ? "Calcul en cours..." : "Comparer"}
        </button>
        {results && results.length > 0 && (
          <>
            <button
              onClick={() => exportLoanComparisonPdf(offers, results)}
              className="px-3 py-1.5 text-xs rounded-md bg-slate-800 text-white hover:bg-slate-900"
            >
              Export PDF
            </button>
            <button
              onClick={() => exportLoanComparisonJson(offers, results)}
              className="px-3 py-1.5 text-xs rounded-md bg-indigo-600 text-white hover:bg-indigo-700"
            >
              Export JSON
            </button>
          </>
        )}
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error} — Vérifiez que le backend est démarré sur le port 8000.
        </div>
      )}

      {results && results.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-slate-600 text-xs uppercase">
              <tr>
                <th className="text-left px-3 py-2">Offre</th>
                <th className="text-right px-3 py-2">Mensualité (créd.)</th>
                <th className="text-right px-3 py-2">Mensualité (assur.)</th>
                <th className="text-right px-3 py-2">Mensualité totale</th>
                <th className="text-right px-3 py-2">Intérêts totaux</th>
                <th className="text-right px-3 py-2">Coût assurance</th>
                <th className="text-right px-3 py-2">Frais annexes</th>
                <th className="text-right px-3 py-2">Coût total crédit</th>
                <th className="text-right px-3 py-2">TAEG</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r) => (
                <tr
                  key={r.id}
                  className={`border-t border-slate-100 ${r.id === bestId ? "bg-emerald-50" : ""}`}
                >
                  <td className="px-3 py-2 font-medium text-slate-700">
                    {r.nom}
                    {r.id === bestId && (
                      <span className="ml-2 text-[10px] font-semibold text-emerald-700 bg-emerald-100 rounded-full px-2 py-0.5">
                        Meilleur TAEG
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-right">{fmt(r.mensualite)}</td>
                  <td className="px-3 py-2 text-right">{fmt(r.mensualite_assurance)}</td>
                  <td className="px-3 py-2 text-right font-semibold">{fmt(r.mensualite_totale)}</td>
                  <td className="px-3 py-2 text-right">{fmt(r.interets_totaux)}</td>
                  <td className="px-3 py-2 text-right">{fmt(r.cout_assurance_total)}</td>
                  <td className="px-3 py-2 text-right">{fmt(r.frais_annexes)}</td>
                  <td className="px-3 py-2 text-right font-semibold">{fmt(r.cout_total_credit)}</td>
                  <td className="px-3 py-2 text-right font-bold">{fmtPct(r.taeg)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
