"use client";

import { ChangeEvent, useEffect, useRef, useState } from "react";
import { FlatConfig, Params } from "@/lib/types";

interface Props {
  flats: FlatConfig[];
  defaults: Pick<Params, "prix_m2_achat" | "loyer_m2" | "loyer_meuble_m2" | "surface" | "frais_notaire_pct" | "charges_copro_mensuelle" | "taxe_fonciere_mensuelle" | "vacance_locative_pct" | "gestion_locative_pct">;
  onChange: (flats: FlatConfig[]) => void;
}

function updateFlat(flats: FlatConfig[], id: string, patch: Partial<FlatConfig>): FlatConfig[] {
  return flats.map((flat) => (flat.id === id ? { ...flat, ...patch } : flat));
}

type FlatConfigFile = {
  version: 1;
  type: "invest-immo-flat-config";
  savedAt: string;
  flat: FlatConfig;
};

const REQUIRED_NUMERIC_FIELDS: Array<keyof FlatConfig> = [
  "prix_m2_achat",
  "loyer_m2",
  "loyer_meuble_m2",
  "surface",
  "frais_notaire_pct",
  "charges_copro_mensuelle",
  "taxe_fonciere_mensuelle",
  "vacance_locative_pct",
  "gestion_locative_pct",
];

function sanitizeFlat(flat: FlatConfig): FlatConfig | null {
  if (!flat.id || !flat.name) return null;
  for (const field of REQUIRED_NUMERIC_FIELDS) {
    const value = flat[field];
    if (typeof value !== "number" || !Number.isFinite(value)) {
      return null;
    }
  }
  return {
    ...flat,
    enabled: Boolean(flat.enabled),
  };
}

function makeFileName(flat: FlatConfig): string {
  const safeName = flat.name
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9_-]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .toLowerCase();
  return `flat_${safeName || flat.id}.json`;
}

export default function FlatComparePanel({ flats, defaults, onChange }: Props) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [ioMessage, setIoMessage] = useState<string | null>(null);
  const [exportFlatIds, setExportFlatIds] = useState<string[]>(() =>
    flats.filter((flat) => flat.enabled).map((flat) => flat.id)
  );

  useEffect(() => {
    setExportFlatIds((prev) => {
      const validIds = new Set(flats.map((flat) => flat.id));
      const kept = prev.filter((id) => validIds.has(id));
      if (kept.length > 0) return kept;
      return flats.filter((flat) => flat.enabled).map((flat) => flat.id);
    });
  }, [flats]);

  const toggleExportFlat = (id: string, checked: boolean) => {
    setExportFlatIds((prev) => {
      if (checked) {
        if (prev.includes(id)) return prev;
        return [...prev, id];
      }
      return prev.filter((item) => item !== id);
    });
  };

  const toggleFlat = (flat: FlatConfig, enabled: boolean) => {
    const patch = enabled && !flat.enabled
      ? {
          enabled,
          prix_m2_achat: defaults.prix_m2_achat,
          loyer_m2: defaults.loyer_m2,
          loyer_meuble_m2: defaults.loyer_meuble_m2,
          surface: defaults.surface,
          frais_notaire_pct: defaults.frais_notaire_pct,
          charges_copro_mensuelle: defaults.charges_copro_mensuelle,
          taxe_fonciere_mensuelle: defaults.taxe_fonciere_mensuelle,
          vacance_locative_pct: defaults.vacance_locative_pct,
          gestion_locative_pct: defaults.gestion_locative_pct,
        }
      : { enabled };

    onChange(updateFlat(flats, flat.id, patch));
  };

  const handleExport = async () => {
    const selectedFlats = flats.filter((flat) => exportFlatIds.includes(flat.id));
    if (selectedFlats.length === 0) {
      setIoMessage("Aucun bien selectionne pour l'export.");
      return;
    }

    const filesToExport = selectedFlats.map((flat) => {
      const payload: FlatConfigFile = {
        version: 1,
        type: "invest-immo-flat-config",
        savedAt: new Date().toISOString(),
        flat,
      };
      return {
        name: makeFileName(flat),
        content: JSON.stringify(payload, null, 2),
      };
    });

    const win = window as Window & {
      showDirectoryPicker?: () => Promise<{
        getFileHandle: (
          name: string,
          options?: { create?: boolean }
        ) => Promise<{ createWritable: () => Promise<{ write: (data: string) => Promise<void>; close: () => Promise<void> }> }>;
      }>;
    };

    if (typeof win.showDirectoryPicker === "function") {
      try {
        const dirHandle = await win.showDirectoryPicker();
        for (const file of filesToExport) {
          const fileHandle = await dirHandle.getFileHandle(file.name, { create: true });
          const writable = await fileHandle.createWritable();
          await writable.write(file.content);
          await writable.close();
        }
        setIoMessage(`${filesToExport.length} fichier(s) exporte(s) dans le dossier choisi.`);
        return;
      } catch {
        // User cancel or permission issue: fallback to download behavior below.
      }
    }

    filesToExport.forEach((file) => {
      const blob = new Blob([file.content], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = file.name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
    setIoMessage(`${filesToExport.length} fichier(s) exporte(s). Le navigateur ne permet pas la selection d'un dossier ici.`);
  };

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleImportFiles = async (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []);
    event.target.value = "";
    if (files.length === 0) return;

    const imported: FlatConfig[] = [];
    let invalidCount = 0;

    for (const file of files) {
      try {
        const raw = JSON.parse(await file.text()) as Partial<FlatConfigFile> & { flat?: FlatConfig };
        if (raw.type !== "invest-immo-flat-config" || !raw.flat) {
          invalidCount += 1;
          continue;
        }
        const sanitized = sanitizeFlat(raw.flat);
        if (!sanitized) {
          invalidCount += 1;
          continue;
        }
        imported.push(sanitized);
      } catch {
        invalidCount += 1;
      }
    }

    if (imported.length === 0) {
      setIoMessage("Aucun fichier valide importe.");
      return;
    }

    const byId = new Map(imported.map((f) => [f.id, f]));
    const usedImportIds = new Set<string>();

    const next = flats.map((flat) => {
      const found = byId.get(flat.id);
      if (!found) return flat;
      usedImportIds.add(found.id);
      return { ...found, id: flat.id };
    });

    const extras = imported.filter((f) => !usedImportIds.has(f.id));
    if (extras.length > 0) {
      let cursor = 0;
      for (let i = 0; i < next.length && cursor < extras.length; i += 1) {
        const alreadyReplacedById = usedImportIds.has(next[i].id);
        if (alreadyReplacedById) continue;
        next[i] = { ...extras[cursor], id: next[i].id };
        cursor += 1;
      }
    }

    onChange(next);
    const importedCount = imported.length;
    setIoMessage(
      invalidCount > 0
        ? `${importedCount} fichier(s) importe(s), ${invalidCount} ignore(s).`
        : `${importedCount} fichier(s) importe(s).`
    );
  };

  return (
    <div className="space-y-3">
      <div>
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Biens a comparer (max 4)</h3>
        <p className="text-[11px] text-slate-400 mt-1">
          Les champs globaux ci-dessus servent de valeurs par defaut quand vous activez un nouveau bien.
        </p>
        <div className="mt-2 flex items-center gap-2">
          <details className="relative">
            <summary className="list-none cursor-pointer px-2.5 py-1 text-[11px] rounded-md border border-slate-300 bg-white text-slate-700">
              Biens a exporter ({exportFlatIds.length})
            </summary>
            <div className="absolute z-20 mt-1 w-56 rounded-md border border-slate-200 bg-white p-2 shadow-md">
              <p className="text-[11px] text-slate-500 mb-1">Selection JSON export</p>
              <div className="space-y-1">
                {flats.map((flat, idx) => (
                  <label key={flat.id} className="flex items-center gap-2 text-[11px] text-slate-700">
                    <input
                      type="checkbox"
                      checked={exportFlatIds.includes(flat.id)}
                      onChange={(e) => toggleExportFlat(flat.id, e.target.checked)}
                    />
                    <span>{flat.name || `Bien ${idx + 1}`}</span>
                    {!flat.enabled && <span className="text-slate-400">(inactif)</span>}
                  </label>
                ))}
              </div>
            </div>
          </details>
          <button
            type="button"
            onClick={() => {
              void handleExport();
            }}
            className="px-2.5 py-1 text-[11px] rounded-md bg-slate-700 text-white hover:bg-slate-800"
          >
            Exporter configs JSON
          </button>
          <button
            type="button"
            onClick={handleImportClick}
            className="px-2.5 py-1 text-[11px] rounded-md bg-blue-700 text-white hover:bg-blue-800"
          >
            Importer configs JSON
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json,.json"
            multiple
            onChange={handleImportFiles}
            className="hidden"
          />
        </div>
        {ioMessage && <p className="text-[11px] text-slate-500 mt-1">{ioMessage}</p>}
      </div>
      {flats.map((flat, idx) => (
        <div key={flat.id} className="rounded-lg border border-slate-200 bg-slate-50 p-2.5 space-y-2">
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-xs font-medium text-slate-600">
              <input
                type="checkbox"
                checked={flat.enabled}
                onChange={(e) => toggleFlat(flat, e.target.checked)}
              />
              Activer bien {idx + 1}
            </label>
            <input
              value={flat.name}
              onChange={(e) => onChange(updateFlat(flats, flat.id, { name: e.target.value || `Bien ${idx + 1}` }))}
              className="w-28 border border-slate-200 rounded-md px-2 py-1 text-xs bg-white"
            />
          </div>

          <div className="grid grid-cols-3 gap-1.5">
            <NumberField
              label="Prix/m2"
              value={flat.prix_m2_achat}
              onChange={(v) => onChange(updateFlat(flats, flat.id, { prix_m2_achat: v }))}
            />
            <NumberField
              label="Prix total"
              value={Math.round(flat.prix_m2_achat * flat.surface)}
              onChange={(v) => {
                const safeSurface = flat.surface > 0 ? flat.surface : 0.01;
                onChange(updateFlat(flats, flat.id, { prix_m2_achat: v / safeSurface }));
              }}
            />
            <NumberField
              label="Loyer non meublé/m2"
              value={flat.loyer_m2}
              onChange={(v) => onChange(updateFlat(flats, flat.id, { loyer_m2: v }))}
            />
            <NumberField
              label="Loyer meublé/m2"
              value={flat.loyer_meuble_m2}
              onChange={(v) => onChange(updateFlat(flats, flat.id, { loyer_meuble_m2: v }))}
            />
            <NumberField
              label="Surface"
              value={flat.surface}
              step={0.01}
              onChange={(v) => onChange(updateFlat(flats, flat.id, { surface: v }))}
            />
          </div>

          <div className="grid grid-cols-2 gap-1.5">
            <NumberField
              label="Notaire (%)"
              value={flat.frais_notaire_pct}
              onChange={(v) => onChange(updateFlat(flats, flat.id, { frais_notaire_pct: v }))}
            />
            <NumberField
              label="Charges (€/an)"
              value={Math.round(flat.charges_copro_mensuelle * 12)}
              onChange={(v) => onChange(updateFlat(flats, flat.id, { charges_copro_mensuelle: v / 12 }))}
            />
            <NumberField
              label="Taxe fonciere (€/an)"
              value={Math.round(flat.taxe_fonciere_mensuelle * 12)}
              onChange={(v) => onChange(updateFlat(flats, flat.id, { taxe_fonciere_mensuelle: v / 12 }))}
            />
            <NumberField
              label="Vacance (%)"
              value={flat.vacance_locative_pct}
              onChange={(v) => onChange(updateFlat(flats, flat.id, { vacance_locative_pct: v }))}
            />
            <NumberField
              label="Gestion (%)"
              value={flat.gestion_locative_pct}
              onChange={(v) => onChange(updateFlat(flats, flat.id, { gestion_locative_pct: v }))}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function NumberField({
  label,
  value,
  step,
  onChange,
  disabled,
}: {
  label: string;
  value: number;
  step?: number;
  onChange: (n: number) => void;
  disabled?: boolean;
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
    onChange(parsed);
  };

  return (
    <label className="flex flex-col gap-0.5 text-[11px] text-slate-500">
      {label}
      <input
        type="text"
        inputMode="decimal"
        value={raw}
        disabled={disabled}
        onChange={(e) => {
          const nextRaw = e.target.value;
          setRaw(nextRaw);
          commit(nextRaw);
        }}
        onBlur={() => {
          commit(raw);
          setRaw(String(value));
        }}
        className={`border border-slate-200 rounded-md px-1.5 py-1 text-xs text-slate-700 ${disabled ? "bg-slate-100" : "bg-white"}`}
      />
    </label>
  );
}
