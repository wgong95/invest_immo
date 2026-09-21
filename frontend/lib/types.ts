export interface Params {
  apport: number;
  taux_interet: number;
  taux_assurance: number;
  revenu_mensuel_brut: number;
  prix_m2_achat: number;
  loyer_m2: number;
  loyer_m2_meuble?: number;
  surface: number;
  duree_pret_ans: number;
  frais_notaire_pct: number;
  frais_dossier: number;
  frais_garantie: number;
  charges_copro_mensuelle: number;
  taxe_fonciere_mensuelle: number;
  vacance_locative_pct: number;
  gestion_locative_pct: number;
  tmi: number;
  revalorisation_bien_pct: number;
  revalorisation_loyer_pct: number;
  horizon_ans: number;
  rendement_scpi: number;
  taux_actualisation?: number;
  taux_sans_risque?: number;
  prime_risque_marche?: number;
  beta_u_location_nue?: number;
  beta_u_lmnp?: number;
  beta_u_airbnb?: number;
  beta_u_scpi?: number;
  beta_u_residence_principale?: number;
  stress_cashflow_factor?: number;
  stress_terminal_factor?: number;
}

export interface FlatConfig {
  id: string;
  name: string;
  enabled: boolean;
  prix_m2_achat: number;
  loyer_m2: number;
  loyer_m2_meuble?: number;
  surface: number;
  frais_notaire_pct: number;
  charges_copro_mensuelle: number;
  taxe_fonciere_mensuelle: number;
  vacance_locative_pct: number;
  gestion_locative_pct: number;
}

export interface YearlyRow {
  annee: number;
  loyer_annuel?: number;
  loyer_economise?: number;
  interets?: number;
  charges?: number;
  impot?: number;
  amortissement?: number;
  bic_imposable?: number;
  mensualite_an?: number;
  cash_flow: number;
  valeur_bien?: number;
  capital_restant?: number;
  patrimoine_net: number;
  rentabilite_nette_apres_financement_pct?: number;
  cash_flow_yield_pct?: number;
  rentabilite_nette_locative_hors_revalo_pct?: number;
  rentabilite_nette_totale_avec_revalo_pct?: number;
}

export interface Strategy {
  id: string;
  nom: string;
  description: string;
  mensualite: number;
  loyer_mensuel: number;
  cash_flow_moyen: number;
  patrimoine_net_final: number;
  tri: number | null;
  van: number;
  ke: number;
  beta_u: number;
  beta_l: number;
  discount_rate_used: number;
  tri_minus_ke: number | null;
  dscr: number | null;
  coc_return_pct: number;
  stress_van: number;
  stress_pass: boolean;
  is_candidate: boolean;
  is_recommended: boolean;
  rendement_brut: number;
  rentabilite_nette_sur_periode: number;
  rentabilite_nette_locative_hors_revalo: number;
  rentabilite_nette_totale_avec_revalo: number;
  yearly: YearlyRow[];
}

export interface Resume {
  prix_achat: number;
  frais_notaire: number;
  frais_dossier: number;
  frais_garantie: number;
  cout_total: number;
  emprunt: number;
  mensualite: number;
  mensualite_assurance: number;
  cout_assurance_total: number;
  taeg: number | null;
  interets_totaux: number;
  loyer_mensuel_brut: number;
  rendement_brut_nu: number;
}

export interface AnalyseResult {
  resume: Resume;
  strategies: Strategy[];
}

export interface LoanOffer {
  id: string;
  nom: string;
  montant_emprunte: number;
  taux_interet: number;
  taux_assurance: number;
  duree_pret_ans: number;
  frais_dossier: number;
  frais_garantie: number;
}

export interface LoanOfferResult {
  id: string;
  nom: string;
  mensualite: number;
  mensualite_assurance: number;
  mensualite_totale: number;
  interets_totaux: number;
  cout_assurance_total: number;
  frais_annexes: number;
  cout_total_credit: number;
  taeg: number | null;
}
