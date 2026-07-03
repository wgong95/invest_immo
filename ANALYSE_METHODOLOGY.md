# Invest Immo - Full Analysis Methodology

This document is the authoritative functional specification for how the simulation computes results.

It explains:
- all inputs,
- all formulas,
- all strategy-specific hypotheses,
- all output indicators,
- and the current model limits.

This is a decision-support model, not legal, tax, or accounting advice.

## 1) Scope

Backend endpoint:
- POST /api/analyse

For each run, the backend returns:
- a global summary block,
- 5 strategy analyses:
  - Location Nue
  - LMNP Meuble
  - Location Courte Duree (Airbnb-like)
  - SCPI
  - Residence Principale

Each strategy contains:
- yearly rows from year 1 to horizon,
- synthesized indicators (cash flow moyen, TRI, rendement brut, patrimoine final).

## 2) Input Parameters

## 2.1 Core financing and market inputs

- apport
- taux_interet
- revenu_mensuel_brut
- prix_m2_achat
- loyer_m2
- surface
- duree_pret_ans
- frais_notaire_pct
- charges_copro_mensuelle
- taxe_fonciere_mensuelle
- vacance_locative_pct
- gestion_locative_pct
- tmi
- revalorisation_bien_pct
- revalorisation_loyer_pct
- horizon_ans
- rendement_scpi

## 2.2 LMNP-specific inputs (current model)

- travaux_annuel
- assurance_pno_annuel
- cfe_annuel
- honoraires_comptable_annuel
- amort_frais_acq_annuel

## 2.3 Multi-flat mode overrides

In the multi-flat front-end flow, each flat can override:
- prix_m2_achat
- loyer_m2
- surface
- frais_notaire_pct
- charges_copro_mensuelle
- taxe_fonciere_mensuelle
- vacance_locative_pct
- gestion_locative_pct

The backend is still called once per flat. Each call is independent.

## 3) Core Engine Calculations (used by several strategies)

## 3.1 Acquisition and financing

- prix_achat = prix_m2_achat * surface
- frais_notaire = prix_achat * frais_notaire_pct / 100
- cout_total = prix_achat + frais_notaire
- emprunt = max(0, cout_total - apport)

## 3.2 Loan monthly payment

Let:
- t = taux_interet / 100 / 12
- n = duree_pret_ans * 12

If emprunt <= 0, mensualite = 0.

If t == 0:
- mensualite = emprunt / n

Else (annuity formula):
- mensualite = emprunt * t / (1 - (1 + t)^(-n))

## 3.3 Amortization table

For each month:
- interets_m = capital_restant * t
- amort_m = mensualite - interets_m
- capital_restant = max(0, capital_restant - amort_m)

Yearly helpers:
- interets annuels = sum of monthly interest over the 12 months of year y
- capital restant (year y) = remaining principal at the end of year y

## 3.4 Shared tax rate

- taux_fiscal = (tmi + 17.2) / 100

17.2 is modeled as social contributions.

## 3.5 Shared valuation revaluation

For non-SCPI real estate strategies:
- valeur_bien(y) = prix_achat * (1 + revalorisation_bien_pct / 100)^y

## 4) Strategy Methodology

## 4.1 Strategy A - Location Nue

### Revenue

Base monthly rent:
- loyer_nu = loyer_m2 * surface

Year y annual rent:
- loyer(y) = loyer_nu * 12 * (1 + revalorisation_loyer_pct/100)^(y-1) * (1 - vacance_locative_pct/100)

### Charges

- charges_copro = charges_copro_mensuelle * 12
- tf = taxe_fonciere_mensuelle * 12
- gestion = loyer(y) * gestion_locative_pct / 100

### Tax base and tax

- revenu_foncier = loyer(y) - interets(y) - charges_copro - tf - gestion

If revenu_foncier > 0:
- impot = revenu_foncier * taux_fiscal

Else:
- impot = -min(abs(revenu_foncier), 10700) * tmi / 100

Negative impot here models a tax benefit from deductible deficit (simplified).

### Cash flow

- mensualite_an(y) = mensualite * 12 if y <= duree_pret_ans else 0
- cash_flow(y) = loyer(y) - mensualite_an(y) - charges_copro - tf - gestion - impot

### Patrimoine net

- patrimoine_net(y) = valeur_bien(y) - capital_restant(y)

## 4.2 Strategy B - LMNP Meuble

This strategy was updated to include:
- deductible current charges block,
- amortization capping,
- amortization carryforward,
- deficit carryforward over 10 years.

### Revenue

- loyer_meuble_mensuel = loyer_nu * 1.15
- loyer(y) = loyer_meuble_mensuel * 12 * (1 + revalorisation_loyer_pct/100)^(y-1) * (1 - vacance_locative_pct/100)

### Amortization hypotheses

- mobilier = prix_achat * 0.12
- amort_bien_an = prix_achat * 0.80 / 30
- amort_mob(y) = mobilier / 7 for years 1..7, else 0
- amort_frais_acq_annuel = input parameter

### Step-by-step fiscal pipeline

1) Deductible charges excluding amortization

- charges_courantes(y) =
  interets(y)
  + charges_copro(y)
  + tf(y)
  + gestion(y)
  + travaux_annuel
  + assurance_pno_annuel
  + cfe_annuel
  + honoraires_comptable_annuel

2) BIC before amortization

- bic_avant_amort(y) = loyer(y) - charges_courantes(y)

3) Capped amortization deduction

- amort_total(y) =
  amort_bien_an
  + amort_mob(y)
  + amort_frais_acq_annuel
  + amort_reporte_anterieur

- amort_deductible(y) = min(amort_total(y), max(0, bic_avant_amort(y)))

- amort_reporte_nouveau = amort_total(y) - amort_deductible(y)

4) BIC after amortization

- bic_apres_amort(y) = bic_avant_amort(y) - amort_deductible(y)

5) Deficit carryforward (10-year stock)

The model keeps yearly deficit buckets with 10-year remaining life.

- If bic_apres_amort(y) > 0:
  - apply deficits from existing buckets (oldest first)
  - imputation_deficit(y) = applied amount

- If bic_apres_amort(y) < 0:
  - create a new deficit bucket with:
    - montant = abs(bic_apres_amort(y))
    - annees_restantes = 10

- bic_net_imposable(y) = max(0, bic_apres_amort(y) - imputation_deficit(y))

6) Tax

- impot(y) = bic_net_imposable(y) * taux_fiscal

### Cash flow (economic)

LMNP cash flow remains an economic cash flow:

- cash_flow(y) = loyer(y) - mensualite_an(y) - charges_copro(y) - tf(y) - gestion(y) - impot(y)

Important:
- non-cash accounting items (amortissement) do not leave cash,
- but they affect tax through bic_net_imposable.

### Yearly outputs used in UI

- charges = charges_courantes
- amortissement = amort_deductible
- bic_imposable = bic_net_imposable

## 4.3 Strategy C - Location Courte Duree (Airbnb-like)

### Revenue hypotheses

- revenu_nuitee = loyer_nu * 2.8
- taux_occupation = 0.70
- revenu_mensuel = revenu_nuitee * taux_occupation
- revenu(y) = revenu_mensuel * 12 * (1 + revalorisation_loyer_pct/100)^(y-1)

### Cost hypotheses

- charges_copro = charges_copro_mensuelle * 12
- tf = taxe_fonciere_mensuelle * 12
- plateforme = revenu(y) * 15%
- conciergerie = revenu(y) * 20%
- menage = 150 * 12

### Fiscal base

- mobilier fixed = 20000
- amort_bien_an = prix_achat * 0.80 / 30
- amort_mob = mobilier / 7 for years 1..7, else 0

- bic = revenu(y) - interets(y) - charges_copro - tf - plateforme - conciergerie - menage - amort_bien_an - amort_mob
- impot = max(0, bic) * taux_fiscal

### Cash flow

- cash_flow(y) = revenu(y) - mensualite_an(y) - charges_copro - tf - plateforme - conciergerie - menage - impot

### Patrimoine

- patrimoine_net(y) = valeur_bien(y) - capital_restant(y)

## 4.4 Strategy D - SCPI

### Capital and return hypotheses

- frais_entree = 9%
- capital_net = apport * (1 - 0.09)
- rendement = rendement_scpi / 100
- revalorisation_parts = 1%/year

### Yearly loop

- revenu(y) = valeur_parts(y-1) * rendement
- impot(y) = revenu(y) * taux_fiscal
- cash_flow(y) = revenu(y) - impot(y)
- valeur_parts(y) = valeur_parts(y-1) * (1 + 0.01)

In SCPI rows:
- patrimoine_net = valeur_parts

## 4.5 Strategy E - Residence Principale

### Economic benefit approach

No rental income is modeled.
Instead, the model uses avoided rent:

- loyer_economise(y) = loyer_nu * 12 * (1 + revalorisation_loyer_pct/100)^(y-1)

### Costs and cash flow differential

- charges = charges_copro + tf
- cash_flow(y) = loyer_economise(y) - mensualite_an(y) - charges_copro - tf

### Patrimoine

- patrimoine_net(y) = valeur_bien(y) - capital_restant(y)

## 5) Output Indicators - Definitions

## 5.1 Global summary indicators

- prix_achat
- frais_notaire
- cout_total
- emprunt
- mensualite
- loyer_mensuel_brut
- rendement_brut_nu = (loyer_nu * 12 / prix_achat) * 100

## 5.2 Yearly table indicators

- annee: year index 1..horizon
- loyer_annuel or loyer_economise
- interets: annual interest
- charges: annual expenses block (strategy-dependent)
- mensualite_an: annual debt service while loan is active
- amortissement: LMNP deductible amortization in current year
- impot: annual modeled tax
- cash_flow: annual economic cash flow
- cash flow/mois (UI): round(cash_flow / 12)
- valeur_bien (except SCPI)
- capital_restant (except SCPI)
- patrimoine_net

## 5.3 Strategy-level synthetic indicators

- cash_flow_moyen
  - average monthly cash flow over horizon
  - implementation: round(sum(cash_flow annual rows) / horizon / 12)

- patrimoine_net_final
  - last yearly patrimoine_net

- rendement_brut
  - Location Nue: (loyer_nu * 12 / prix_achat) * 100
  - LMNP: (loyer_meuble * 12 / prix_achat) * 100
  - Courte Duree: (revenu_mensuel * 12 / prix_achat) * 100
  - SCPI: rendement_scpi input
  - Residence Principale: 0

- tri (IRR)
  - computed from yearly cash flow series + terminal value component

## 6) TRI / IRR Construction

## 6.1 General numerical method

- Newton-Raphson iterations
- max iterations: 1000
- tolerance: 1e-8
- return accepted only if rate in a bounded interval (model guardrail)

## 6.2 Cash-flow vectors by strategy

Location Nue:
- initial outflow: -(apport + frais_notaire)
- yearly inflows: annual cash_flow
- final add-on: valeur_fin - capital_restant_fin

LMNP:
- initial outflow: -(apport + frais_notaire + mobilier)
- yearly inflows: annual cash_flow
- final add-on: valeur_fin - capital_restant_fin

Courte Duree:
- initial outflow: -(apport + frais_notaire + mobilier)
- yearly inflows: annual cash_flow
- final add-on: valeur_fin - capital_restant_fin

SCPI:
- initial outflow: -apport
- yearly inflows: annual cash_flow
- final add-on: final valeur_parts

Residence Principale:
- initial outflow: -(apport + frais_notaire)
- yearly inflows: annual cash_flow
- final add-on: valeur_fin

## 7) Rounding and Display Rules

- Most yearly values are rounded to nearest EUR in backend outputs.
- UI cash flow/mois is derived from annual cash flow and then rounded.
- Small annual differences may appear as 0 or +/-1 per month after rounding.

## 8) Modeling Hypotheses and Simplifications

The model intentionally simplifies several real-life topics.

Included assumptions:
- deterministic yearly growth rates,
- deterministic vacancy and management rates,
- deterministic short-term rental multipliers and fee rates,
- fixed SCPI fee and revaluation assumptions,
- simplified deficit and amortization carry mechanisms.

Not fully modeled:
- resale transaction costs and taxation details (except current simplified logic),
- loan insurance and banking ancillary costs,
- maintenance CAPEX lifecycle details,
- legal constraints and regime edge cases,
- inflation by cost line,
- stochastic scenarios (probability distributions, stress cases).

## 9) Consistency Notes

- The methodology document, backend formulas, UI tables, and PDF export should remain aligned.
- If backend logic changes, this file must be updated in the same change set.
