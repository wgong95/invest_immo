"use client";

import { useEffect, useState } from "react";
import { Params } from "@/lib/types";

interface Props {
  params: Params;
  onChange: (p: Params) => void;
}

function Field({
  label,
  value,
  field,
  unit,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  value: number;
  field: keyof Params;
  unit?: string;
  min?: number;
  max?: number;
  step?: number;
  onChange: (f: keyof Params, v: number) => void;
}) {
  const [raw, setRaw] = useState(String(value));

  useEffect(() => {
    setRaw(String(value));
  }, [value]);

  const commit = (input: string) => {
    const normalized = input.replace(",", ".").trim();
    if (normalized === "" || normalized === "." || normalized === "-" || normalized === "-.") {
      return;
    }
    const parsed = Number(normalized);
    if (!Number.isFinite(parsed)) {
      return;
    }
    let next = parsed;
    if (min !== undefined) next = Math.max(min, next);
    if (max !== undefined) next = Math.min(max, next);
    onChange(field, next);
  };

  return (
    <div className="flex flex-col gap-0.5">
      <label className="text-xs text-slate-500 font-medium">{label}</label>
      <div className="flex items-center gap-1">
        <input
          type="text"
          inputMode="decimal"
          value={raw}
          onChange={(e) => {
            const nextRaw = e.target.value;
            setRaw(nextRaw);
            commit(nextRaw);
          }}
          onBlur={() => {
            commit(raw);
            setRaw(String(value));
          }}
          className="flex-1 border border-slate-200 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50"
        />
        {unit && <span className="text-xs text-slate-400 whitespace-nowrap">{unit}</span>}
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-5">
      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">{title}</h3>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

export default function ParamPanel({ params, onChange }: Props) {
  const set = (f: keyof Params, v: number) => onChange({ ...params, [f]: v });

  return (
    <div>
      <Section title="Profil emprunteur">
        <Field label="Apport personnel" value={params.apport} field="apport" unit="€" step={5000} min={0} onChange={set} />
        <Field label="Revenu mensuel brut" value={params.revenu_mensuel_brut} field="revenu_mensuel_brut" unit="€/mois" step={100} onChange={set} />
        <Field label="TMI (tranche marginale)" value={params.tmi} field="tmi" unit="%" min={0} max={45} step={1} onChange={set} />
      </Section>

      <Section title="Crédit immobilier">
        <Field label="Taux d'intérêt" value={params.taux_interet} field="taux_interet" unit="%" min={0} max={10} step={0.05} onChange={set} />
        <Field
          label="Rendement exigé (VAN)"
          value={params.taux_actualisation}
          field="taux_actualisation"
          unit="%"
          min={0}
          max={15}
          step={0.1}
          onChange={set}
        />
        <Field label="Durée du prêt" value={params.duree_pret_ans} field="duree_pret_ans" unit="ans" min={5} max={30} onChange={set} />
        <Field label="Frais de notaire" value={params.frais_notaire_pct} field="frais_notaire_pct" unit="%" min={0} max={12} step={0.5} onChange={set} />
      </Section>

      <Section title="Charges & fiscalité">
        <Field label="Charges copropriété" value={params.charges_copro_mensuelle} field="charges_copro_mensuelle" unit="€/mois" step={10} onChange={set} />
        <Field label="Taxe foncière" value={params.taxe_fonciere_mensuelle} field="taxe_fonciere_mensuelle" unit="€/mois" step={10} onChange={set} />
        <Field label="Vacance locative" value={params.vacance_locative_pct} field="vacance_locative_pct" unit="%" min={0} max={30} step={0.5} onChange={set} />
        <Field label="Frais de gestion" value={params.gestion_locative_pct} field="gestion_locative_pct" unit="%" min={0} max={15} step={0.5} onChange={set} />
      </Section>

      <Section title="Hypothèses de marché">
        <Field label="Loyer non meublé" value={params.loyer_m2} field="loyer_m2" unit="€/m2" min={0} step={0.5} onChange={set} />
        <Field label="Loyer meublé (LMNP)" value={params.loyer_meuble_m2} field="loyer_meuble_m2" unit="€/m2" min={0} step={0.5} onChange={set} />
        <Field label="Revalorisation bien" value={params.revalorisation_bien_pct} field="revalorisation_bien_pct" unit="%/an" min={-5} max={10} step={0.5} onChange={set} />
        <Field label="Revalorisation loyers" value={params.revalorisation_loyer_pct} field="revalorisation_loyer_pct" unit="%/an" min={-5} max={10} step={0.5} onChange={set} />
        <Field label="Rendement SCPI" value={params.rendement_scpi} field="rendement_scpi" unit="%" min={1} max={10} step={0.1} onChange={set} />
        <Field label="Horizon de simulation" value={params.horizon_ans} field="horizon_ans" unit="ans" min={5} max={30} onChange={set} />
      </Section>
    </div>
  );
}
