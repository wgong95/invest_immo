import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import * as XLSX from "xlsx";
import { AnalyseResult, FlatConfig } from "./types";

export interface FlatAnalysis {
  flat: FlatConfig;
  result: AnalyseResult;
}

const STRATEGY_LABEL: Record<string, string> = {
  location_nue: "Location Nue",
  lmnp_meuble: "LMNP Meuble",
  airbnb: "Location Courte Duree",
  scpi: "SCPI",
  residence_principale: "Residence Principale",
};

const fmtEuro = (n: number | null | undefined) => {
  if (n === null || n === undefined || Number.isNaN(n)) return "-";
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(n);
};

const fmtPct = (n: number | null | undefined) => {
  if (n === null || n === undefined || Number.isNaN(n)) return "-";
  return `${n.toFixed(2)}%`;
};

function summaryRows(analyses: FlatAnalysis[]) {
  return analyses.flatMap(({ flat, result }) =>
    result.strategies.map((strategy) => ({
      Bien: flat.name,
      "Prix total": Math.round(flat.prix_m2_achat * flat.surface),
      "Prix m2": flat.prix_m2_achat,
      "Loyer m2": flat.loyer_m2,
      Surface: flat.surface,
      "Notaire (%)": flat.frais_notaire_pct,
      "Charges copro (EUR/an)": Math.round(flat.charges_copro_mensuelle * 12),
      "Taxe fonciere (EUR/an)": Math.round(flat.taxe_fonciere_mensuelle * 12),
      "Vacance (%)": flat.vacance_locative_pct,
      "Gestion (%)": flat.gestion_locative_pct,
      Strategie: strategy.nom,
      "TRI (%)": strategy.tri ?? "N/A",
      "Cash flow moyen (EUR/mois)": strategy.cash_flow_moyen,
      "Patrimoine net final (EUR)": strategy.patrimoine_net_final,
      "Rendement brut (%)": strategy.rendement_brut,
    }))
  );
}

export function exportComparisonExcel(analyses: FlatAnalysis[]) {
  const wb = XLSX.utils.book_new();

  const summary = summaryRows(analyses);
  const wsSummary = XLSX.utils.json_to_sheet(summary);
  XLSX.utils.book_append_sheet(wb, wsSummary, "Comparatif");

  const yearly = analyses.flatMap(({ flat, result }) =>
    result.strategies.flatMap((strategy) =>
      strategy.yearly.map((row) => ({
        Bien: flat.name,
        Strategie: strategy.nom,
        Annee: row.annee,
        "Cash flow annuel": row.cash_flow,
        "Patrimoine net": row.patrimoine_net,
        "Interets": row.interets ?? "",
        "Mensualite": row.mensualite_an ?? "",
        "Impot": row.impot ?? "",
      }))
    )
  );
  const wsYearly = XLSX.utils.json_to_sheet(yearly);
  XLSX.utils.book_append_sheet(wb, wsYearly, "Detail_annuel");

  XLSX.writeFile(wb, `rapport_invest_immo_${new Date().toISOString().slice(0, 10)}.xlsx`);
}

export function exportComparisonPdf(analyses: FlatAnalysis[]) {
  if (analyses.length === 0) return;

  const doc = new jsPDF({ orientation: "landscape" });
  const marginX = 14;

  doc.setFontSize(14);
  doc.text("Invest Immo - Rapport comparatif multi-biens", 14, 14);
  doc.setFontSize(10);
  doc.text(`Genere le ${new Date().toLocaleDateString("fr-FR")}`, 14, 20);

  const rows = summaryRows(analyses).map((r) => [
    r.Bien,
    r.Strategie,
    String(r["TRI (%)"]),
    String(r["Cash flow moyen (EUR/mois)"]),
    String(r["Patrimoine net final (EUR)"]),
  ]);

  autoTable(doc, {
    startY: 26,
    head: [["Bien", "Strategie", "TRI (%)", "Cash flow (EUR/mois)", "Patrimoine final (EUR)"]],
    body: rows,
    styles: { fontSize: 8 },
    headStyles: { fillColor: [30, 64, 175] },
  });

  analyses.forEach(({ flat, result }, flatIndex) => {
    doc.addPage("a4", "landscape");

    doc.setFontSize(13);
    doc.text(`Bien ${flatIndex + 1}: ${flat.name}`, marginX, 14);
    doc.setFontSize(9);
    doc.text("Parametres du bien", marginX, 20);

    autoTable(doc, {
      startY: 22,
      theme: "grid",
      head: [["Champ", "Valeur", "Champ", "Valeur"]],
      body: [
        ["Prix/m2", fmtEuro(flat.prix_m2_achat), "Surface", `${flat.surface.toFixed(2)} m2`],
        ["Prix total", fmtEuro(Math.round(flat.prix_m2_achat * flat.surface)), "Loyer/m2", fmtEuro(flat.loyer_m2)],
        ["Notaire", fmtPct(flat.frais_notaire_pct), "Charges copro/mois", fmtEuro(flat.charges_copro_mensuelle)],
        ["Taxe fonciere/mois", fmtEuro(flat.taxe_fonciere_mensuelle), "Vacance", fmtPct(flat.vacance_locative_pct)],
        ["Gestion", fmtPct(flat.gestion_locative_pct), "", ""],
      ],
      styles: { fontSize: 8 },
      headStyles: { fillColor: [30, 64, 175] },
      columnStyles: { 0: { cellWidth: 55 }, 1: { cellWidth: 55 }, 2: { cellWidth: 55 }, 3: { cellWidth: 55 } },
      margin: { left: marginX, right: marginX },
    });

    const summaryStartY = (doc as jsPDF & { lastAutoTable?: { finalY: number } }).lastAutoTable?.finalY
      ? (doc as jsPDF & { lastAutoTable?: { finalY: number } }).lastAutoTable!.finalY + 8
      : 58;

    doc.setFontSize(9);
    doc.text("Resume des strategies", marginX, summaryStartY - 2);

    autoTable(doc, {
      startY: summaryStartY,
      head: [["Strategie", "TRI", "Cash flow moy./mois", "Patrimoine final", "Rendement brut"]],
      body: result.strategies.map((s) => [
        STRATEGY_LABEL[s.id] ?? s.nom,
        s.tri === null ? "N/A" : fmtPct(s.tri),
        fmtEuro(s.cash_flow_moyen),
        fmtEuro(s.patrimoine_net_final),
        fmtPct(s.rendement_brut),
      ]),
      styles: { fontSize: 8 },
      headStyles: { fillColor: [15, 118, 110] },
      margin: { left: marginX, right: marginX },
    });

    result.strategies.forEach((s) => {
      doc.addPage("a4", "landscape");

      doc.setFontSize(12);
      doc.text(`${flat.name} - ${STRATEGY_LABEL[s.id] ?? s.nom}`, marginX, 14);
      doc.setFontSize(8);
      doc.text(s.description, marginX, 20);

      const isScpi = s.id === "scpi";
      const isRp = s.id === "residence_principale";
      const isLmnp = s.id === "lmnp_meuble";

      const head = ["Annee"];
      if (!isScpi && !isRp) head.push("Loyer annuel");
      if (isRp) head.push("Loyer economise");
      if (isScpi) head.push("Revenus SCPI");
      if (!isScpi && !isRp) head.push("Interets");
      head.push("Charges");
      if (!isScpi) head.push("Mensualite");
      if (isLmnp) head.push("Amortissement");
      head.push("Impot", "Cash flow/mois");
      if (!isScpi) head.push("Valeur bien", "Capital restant");
      head.push("Patrimoine net");

      const body = s.yearly.map((row) => {
        const values: string[] = [String(row.annee)];
        if (!isScpi && !isRp) values.push(fmtEuro(row.loyer_annuel));
        if (isRp) values.push(fmtEuro(row.loyer_economise));
        if (isScpi) values.push(fmtEuro(row.loyer_annuel));
        if (!isScpi && !isRp) values.push(fmtEuro(row.interets));
        values.push(fmtEuro(row.charges));
        if (!isScpi) values.push(fmtEuro(row.mensualite_an));
        if (isLmnp) values.push(fmtEuro(row.amortissement));
        values.push(fmtEuro(row.impot));
        values.push(fmtEuro(Math.round(row.cash_flow / 12)));
        if (!isScpi) values.push(fmtEuro(row.valeur_bien), fmtEuro(row.capital_restant));
        values.push(fmtEuro(row.patrimoine_net));
        return values;
      });

      autoTable(doc, {
        startY: 24,
        head: [head],
        body,
        styles: { fontSize: 7, cellPadding: 1.5 },
        headStyles: { fillColor: [30, 64, 175] },
        margin: { left: marginX, right: marginX },
      });
    });
  });

  doc.save(`rapport_invest_immo_${new Date().toISOString().slice(0, 10)}.pdf`);
}
