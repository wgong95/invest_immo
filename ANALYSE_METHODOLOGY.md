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

### 2.1 Core financing and market inputs

- apport
- taux_interet
- revenu_mensuel_brut
- prix_m2_achat
- loyer_m2 (unfurnished rent rate, drives Location Nue)
- loyer_m2_meuble (furnished rent rate, drives LMNP and Location Courte Duree; optional — falls back to loyer_m2 x 1.15 when omitted)
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

### 2.2 LMNP-specific inputs (current model)

- travaux_annuel
- assurance_pno_annuel
- cfe_annuel
- honoraires_comptable_annuel
- amort_frais_acq_annuel

### 2.3 Multi-flat mode overrides

In the multi-flat front-end flow, each flat can override:
- prix_m2_achat
- loyer_m2
- loyer_m2_meuble
- surface
- frais_notaire_pct
- charges_copro_mensuelle
- taxe_fonciere_mensuelle
- vacance_locative_pct
- gestion_locative_pct

The backend is still called once per flat. Each call is independent.

## 3) Core Engine Calculations (used by several strategies)

### 3.1 Acquisition and financing

$$
\text{prix\_achat} = \text{prix\_m2\_achat} \times \text{surface}
$$

$$
\text{frais\_notaire} = \text{prix\_achat} \times \frac{\text{frais\_notaire\_pct}}{100}
$$

$$
\text{cout\_total} = \text{prix\_achat} + \text{frais\_notaire}
$$

$$
\text{emprunt} = \max\big(0,\ \text{cout\_total} - \text{apport}\big)
$$

### 3.2 Loan monthly payment

Let:

$$
t = \frac{\text{taux\_interet}}{100 \times 12}, \qquad n = \text{duree\_pret\_ans} \times 12
$$

$$
\text{mensualite} =
\begin{cases}
0 & \text{emprunt} \le 0 \\[4pt]
\dfrac{\text{emprunt}}{n} & \text{emprunt} > 0 \text{ and } t = 0 \\[8pt]
\dfrac{\text{emprunt} \times t}{1-(1+t)^{-n}} & \text{emprunt} > 0 \text{ and } t \ne 0 \quad \text{(annuity formula)}
\end{cases}
$$

### 3.3 Amortization table

For each month $m$:

$$
\text{interets}_m = \text{capital\_restant} \times t
$$

$$
\text{amort}_m = \text{mensualite} - \text{interets}_m
$$

$$
\text{capital\_restant} \leftarrow \max\big(0,\ \text{capital\_restant} - \text{amort}_m\big)
$$

Yearly helpers:

$$
\text{interets\_annuels}(y) = \sum_{m \,\in\, \text{months of year } y} \text{interets}_m
$$

$$
\text{capital\_restant}(y) = \text{capital\_restant at the end of year } y
$$

### 3.4 Shared tax rate

$$
\text{taux\_fiscal} = \frac{\text{tmi} + 17.2}{100}
$$

17.2 is modeled as social contributions.

### 3.5 Shared valuation revaluation

For non-SCPI real estate strategies:

$$
\text{valeur\_bien}(y) = \text{prix\_achat} \times \left(1 + \frac{\text{revalorisation\_bien\_pct}}{100}\right)^{y}
$$

## 4) Strategy Methodology

### 4.1 Strategy A - Location Nue

**Revenue**

Base monthly rent:

$$
\text{loyer\_nu} = \text{loyer\_m2} \times \text{surface}
$$

Year $y$ annual rent:

$$
\text{loyer}(y) = \text{loyer\_nu} \times 12 \times \left(1+\frac{\text{revalorisation\_loyer\_pct}}{100}\right)^{y-1} \times \left(1-\frac{\text{vacance\_locative\_pct}}{100}\right)
$$

**Charges**

$$
\text{charges\_copro} = \text{charges\_copro\_mensuelle} \times 12, \qquad
tf = \text{taxe\_fonciere\_mensuelle} \times 12
$$

$$
\text{gestion}(y) = \text{loyer}(y) \times \frac{\text{gestion\_locative\_pct}}{100}
$$

**Tax base and tax**

$$
\text{revenu\_foncier}(y) = \text{loyer}(y) - \text{interets}(y) - \text{charges\_copro} - tf - \text{gestion}(y)
$$

$$
\text{impot}(y) =
\begin{cases}
\text{revenu\_foncier}(y) \times \text{taux\_fiscal} & \text{if } \text{revenu\_foncier}(y) > 0 \\[6pt]
-\min\!\big(|\text{revenu\_foncier}(y)|,\ 10700\big) \times \dfrac{\text{tmi}}{100} & \text{otherwise}
\end{cases}
$$

Negative impot here models a tax benefit from deductible deficit (simplified).

**Cash flow**

$$
\text{mensualite\_an}(y) =
\begin{cases}
\text{mensualite} \times 12 & y \le \text{duree\_pret\_ans} \\
0 & \text{otherwise}
\end{cases}
$$

$$
\text{cash\_flow}(y) = \text{loyer}(y) - \text{mensualite\_an}(y) - \text{charges\_copro} - tf - \text{gestion}(y) - \text{impot}(y)
$$

**Patrimoine net**

$$
\text{patrimoine\_net}(y) = \text{valeur\_bien}(y) - \text{capital\_restant}(y)
$$

### 4.2 Strategy B - LMNP Meuble

This strategy was updated to include:
- deductible current charges block,
- amortization capping,
- amortization carryforward,
- deficit carryforward over 10 years.

**Revenue**

$$
\text{loyer\_meuble\_mensuel} = \text{loyer\_m2\_meuble} \times \text{surface}
$$

If loyer_m2_meuble is not provided, it defaults to loyer_m2 x 1.15.

$$
\text{loyer}(y) = \text{loyer\_meuble\_mensuel} \times 12 \times \left(1+\frac{\text{revalorisation\_loyer\_pct}}{100}\right)^{y-1} \times \left(1-\frac{\text{vacance\_locative\_pct}}{100}\right)
$$

**Amortization hypotheses**

$$
\text{mobilier} = \text{prix\_achat} \times 0.12, \qquad
\text{amort\_bien\_an} = \text{prix\_achat} \times \frac{0.80}{30}
$$

$$
\text{amort\_mob}(y) =
\begin{cases}
\dfrac{\text{mobilier}}{7} & y \le 7 \\
0 & y > 7
\end{cases}
$$

`amort_frais_acq_annuel` = input parameter.

**Step-by-step fiscal pipeline**

1) Deductible charges excluding amortization:

$$
\text{charges\_courantes}(y) = \text{interets}(y) + \text{charges\_copro}(y) + tf(y) + \text{gestion}(y) + \text{travaux\_annuel} + \text{assurance\_pno\_annuel} + \text{cfe\_annuel} + \text{honoraires\_comptable\_annuel}
$$

2) BIC before amortization:

$$
\text{bic\_avant\_amort}(y) = \text{loyer}(y) - \text{charges\_courantes}(y)
$$

3) Capped amortization deduction:

$$
\text{amort\_total}(y) = \text{amort\_bien\_an} + \text{amort\_mob}(y) + \text{amort\_frais\_acq\_annuel} + \text{amort\_reporte\_anterieur}
$$

$$
\text{amort\_deductible}(y) = \min\Big(\text{amort\_total}(y),\ \max\big(0,\ \text{bic\_avant\_amort}(y)\big)\Big)
$$

$$
\text{amort\_reporte\_nouveau} = \text{amort\_total}(y) - \text{amort\_deductible}(y)
$$

4) BIC after amortization:

$$
\text{bic\_apres\_amort}(y) = \text{bic\_avant\_amort}(y) - \text{amort\_deductible}(y)
$$

5) Deficit carryforward (10-year stock). The model keeps yearly deficit buckets with 10-year remaining life:

- If $\text{bic\_apres\_amort}(y) > 0$: apply deficits from existing buckets (oldest first); $\text{imputation\_deficit}(y)$ = applied amount.
- If $\text{bic\_apres\_amort}(y) < 0$: create a new deficit bucket with $\text{montant} = |\text{bic\_apres\_amort}(y)|$, $\text{annees\_restantes} = 10$.

$$
\text{bic\_net\_imposable}(y) = \max\Big(0,\ \text{bic\_apres\_amort}(y) - \text{imputation\_deficit}(y)\Big)
$$

6) Tax:

$$
\text{impot}(y) = \text{bic\_net\_imposable}(y) \times \text{taux\_fiscal}
$$

**Cash flow (economic)**

LMNP cash flow remains an economic cash flow:

$$
\text{cash\_flow}(y) = \text{loyer}(y) - \text{mensualite\_an}(y) - \text{charges\_copro}(y) - tf(y) - \text{gestion}(y) - \text{impot}(y)
$$

Important:
- non-cash accounting items (amortissement) do not leave cash,
- but they affect tax through $\text{bic\_net\_imposable}$.

**Yearly outputs used in UI**

$$
\text{charges} = \text{charges\_courantes}, \qquad
\text{amortissement} = \text{amort\_deductible}, \qquad
\text{bic\_imposable} = \text{bic\_net\_imposable}
$$

### 4.3 Strategy C - Location Courte Duree (Airbnb-like)

**Revenue hypotheses**

$$
\text{revenu\_nuitee} = \text{loyer\_meuble\_mensuel} \times 2.8
$$

Uses the furnished rent baseline (same as LMNP, see 4.2), since a short-term let is inherently furnished.

$$
\text{taux\_occupation} = \frac{120}{365} \approx 32.9\%
$$

— Paris-like regulatory cap of 120 rental days/year for short-term letting of a primary residence.

$$
\text{revenu\_mensuel} = \text{revenu\_nuitee} \times \text{taux\_occupation}
$$

$$
\text{revenu}(y) = \text{revenu\_mensuel} \times 12 \times \left(1+\frac{\text{revalorisation\_loyer\_pct}}{100}\right)^{y-1}
$$

**Cost hypotheses**

$$
\text{charges\_copro} = \text{charges\_copro\_mensuelle} \times 12, \qquad
tf = \text{taxe\_fonciere\_mensuelle} \times 12
$$

$$
\text{plateforme}(y) = \text{revenu}(y) \times 0.15, \qquad
\text{conciergerie}(y) = \text{revenu}(y) \times 0.20, \qquad
\text{menage} = 150 \times 12
$$

**Fiscal base**

$$
\text{mobilier} = \text{prix\_achat} \times 0.12
$$

— unified with the LMNP furniture allowance, see 4.2.

$$
\text{amort\_bien\_an} = \text{prix\_achat} \times \frac{0.80}{30}, \qquad
\text{amort\_mob}(y) =
\begin{cases}
\dfrac{\text{mobilier}}{7} & y \le 7 \\
0 & y > 7
\end{cases}
$$

$$
\text{bic}(y) = \text{revenu}(y) - \text{interets}(y) - \text{charges\_copro} - tf - \text{plateforme}(y) - \text{conciergerie}(y) - \text{menage} - \text{amort\_bien\_an} - \text{amort\_mob}(y)
$$

$$
\text{impot}(y) = \max\big(0,\ \text{bic}(y)\big) \times \text{taux\_fiscal}
$$

**Cash flow**

$$
\text{cash\_flow}(y) = \text{revenu}(y) - \text{mensualite\_an}(y) - \text{charges\_copro} - tf - \text{plateforme}(y) - \text{conciergerie}(y) - \text{menage} - \text{impot}(y)
$$

**Patrimoine**

$$
\text{patrimoine\_net}(y) = \text{valeur\_bien}(y) - \text{capital\_restant}(y)
$$

### 4.4 Strategy D - SCPI

**Capital and return hypotheses**

$$
\text{capital\_net} = \text{apport} \times (1 - 0.09), \qquad
\text{rendement} = \frac{\text{rendement\_scpi}}{100}, \qquad
\text{revalorisation\_parts} = 0.01 \ / \text{an}
$$

**Yearly loop**

$$
\text{revenu}(y) = \text{valeur\_parts}(y-1) \times \text{rendement}
$$

$$
\text{impot}(y) = \text{revenu}(y) \times \text{taux\_fiscal}
$$

$$
\text{cash\_flow}(y) = \text{revenu}(y) - \text{impot}(y)
$$

$$
\text{valeur\_parts}(y) = \text{valeur\_parts}(y-1) \times (1 + 0.01)
$$

In SCPI rows:

$$
\text{patrimoine\_net} = \text{valeur\_parts}
$$

### 4.5 Strategy E - Residence Principale

**Economic benefit approach**

No rental income is modeled. Instead, the model uses avoided rent:

$$
\text{loyer\_economise}(y) = \text{loyer\_nu} \times 12 \times \left(1+\frac{\text{revalorisation\_loyer\_pct}}{100}\right)^{y-1}
$$

**Costs and cash flow differential**

$$
\text{charges} = \text{charges\_copro} + tf
$$

$$
\text{cash\_flow}(y) = \text{loyer\_economise}(y) - \text{mensualite\_an}(y) - \text{charges\_copro} - tf
$$

**Patrimoine**

$$
\text{patrimoine\_net}(y) = \text{valeur\_bien}(y) - \text{capital\_restant}(y)
$$

## 5) Output Indicators - Definitions

### 5.1 Global summary indicators

- prix_achat
- frais_notaire
- cout_total
- emprunt
- mensualite
- loyer_mensuel_brut

$$
\text{rendement\_brut\_nu} = \frac{\text{loyer\_nu} \times 12}{\text{prix\_achat}} \times 100
$$

### 5.2 Yearly table indicators

- annee: year index 1..horizon
- loyer_annuel or loyer_economise
- interets: annual interest
- charges: annual expenses block (strategy-dependent)
- mensualite_an: annual debt service while loan is active
- amortissement: LMNP deductible amortization in current year
- impot: annual modeled tax
- cash_flow: annual economic cash flow
- cash flow/mois (UI): $\text{round}(\text{cash\_flow} / 12)$
- valeur_bien (except SCPI)
- capital_restant (except SCPI)
- patrimoine_net

### 5.3 Strategy-level synthetic indicators

$$
\text{cash\_flow\_moyen} = \text{round}\left(\frac{\sum_{y=1}^{\text{horizon}} \text{cash\_flow}(y)}{\text{horizon} \times 12}\right)
$$

- patrimoine_net_final
  - last yearly patrimoine_net

$$
\text{rendement\_brut} =
\begin{cases}
\dfrac{\text{loyer\_nu} \times 12}{\text{prix\_achat}} \times 100 & \text{Location Nue} \\[10pt]
\dfrac{\text{loyer\_meuble} \times 12}{\text{prix\_achat}} \times 100 & \text{LMNP} \\[10pt]
\dfrac{\text{revenu\_mensuel} \times 12}{\text{prix\_achat}} \times 100 & \text{Courte Duree} \\[10pt]
\text{rendement\_scpi} & \text{SCPI} \\[6pt]
0 & \text{Residence Principale}
\end{cases}
$$

- tri (IRR)
  - computed from yearly cash flow series + terminal value component

## 6) TRI / IRR Construction

### 6.1 General numerical method

TRI (the internal rate of return) is the rate $r$ that solves:

$$
0 = \sum_{i=0}^{n} \frac{CF_i}{(1+r)^{i}}
$$

where $CF_0, CF_1, \dots, CF_n$ is the strategy's cash-flow vector (section 6.2).
Solved via:
- Newton-Raphson iterations
- max iterations: 1000
- tolerance: $10^{-8}$
- return accepted only if $r$ lies in a bounded interval (model guardrail)

### 6.2 Cash-flow vectors by strategy

Location Nue:
- initial outflow: $-(\text{apport} + \text{frais\_notaire})$
- yearly inflows: annual cash_flow
- final add-on: $\text{valeur\_fin} - \text{capital\_restant\_fin}$

LMNP:
- initial outflow: $-(\text{apport} + \text{frais\_notaire} + \text{mobilier})$
- yearly inflows: annual cash_flow
- final add-on: $\text{valeur\_fin} - \text{capital\_restant\_fin}$

Courte Duree:
- initial outflow: $-(\text{apport} + \text{frais\_notaire} + \text{mobilier})$
- yearly inflows: annual cash_flow
- final add-on: $\text{valeur\_fin} - \text{capital\_restant\_fin}$

SCPI:
- initial outflow: $-\text{apport}$
- yearly inflows: annual cash_flow
- final add-on: final $\text{valeur\_parts}$

Residence Principale:
- initial outflow: $-(\text{apport} + \text{frais\_notaire})$
- yearly inflows: annual cash_flow
- final add-on: $\text{valeur\_fin}$

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
