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
- loyer_meuble_m2
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
- taux_actualisation (required return used to discount VAN; user-set, no CAPM/beta involved)
- stress_cashflow_factor
- stress_terminal_factor

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

$$
\begin{aligned}
\text{prix\_achat} &= \text{prix\_m2\_achat} \times \text{surface} \\
\text{frais\_notaire} &= \text{prix\_achat} \times \frac{\text{frais\_notaire\_pct}}{100} \\
\text{cout\_total} &= \text{prix\_achat} + \text{frais\_notaire} \\
\text{emprunt} &= \max(0,\ \text{cout\_total} - \text{apport})
\end{aligned}
$$

## 3.2 Loan monthly payment

Let:

$$
t = \frac{\text{taux\_interet}}{100 \times 12}, \qquad n = \text{duree\_pret\_ans} \times 12
$$

$$
\text{mensualite} =
\begin{cases}
0 & \text{if } \text{emprunt} \le 0 \\[4pt]
\dfrac{\text{emprunt}}{n} & \text{if } \text{emprunt} > 0 \text{ and } t = 0 \\[4pt]
\text{emprunt} \times \dfrac{t}{1-(1+t)^{-n}} & \text{if } \text{emprunt} > 0 \text{ and } t \neq 0 \quad \text{(annuity formula)}
\end{cases}
$$

## 3.3 Amortization table

For each month:

$$
\begin{aligned}
\text{interets}_m &= \text{capital\_restant} \times t \\
\text{amort}_m &= \text{mensualite} - \text{interets}_m \\
\text{capital\_restant} &\leftarrow \max(0,\ \text{capital\_restant} - \text{amort}_m)
\end{aligned}
$$

Yearly helpers:

$$
\text{interets\_annuels}(y) = \sum_{m \,\in\, \text{months of year } y} \text{interets}_m
$$

$$
\text{capital\_restant}(y) = \text{remaining principal at the end of year } y
$$

## 3.4 Shared tax rate

$$
\text{taux\_fiscal} = \frac{\text{tmi} + 17.2}{100}
$$

17.2 is modeled as social contributions.

## 3.5 Shared valuation revaluation

For non-SCPI real estate strategies:

$$
\text{valeur\_bien}(y) = \text{prix\_achat} \times \left(1 + \frac{\text{revalorisation\_bien\_pct}}{100}\right)^{y}
$$

## 4) Strategy Methodology

## 4.1 Strategy A - Location Nue

### Revenue

Base monthly rent:

$$
\text{loyer\_nu} = \text{loyer\_m2} \times \text{surface}
$$

Year y annual rent:

$$
\text{loyer}(y) = \text{loyer\_nu} \times 12 \times \left(1+\frac{\text{revalorisation\_loyer\_pct}}{100}\right)^{y-1} \times \left(1 - \frac{\text{vacance\_locative\_pct}}{100}\right)
$$

### Charges

$$
\begin{aligned}
\text{charges\_copro} &= \text{charges\_copro\_mensuelle} \times 12 \\
\text{tf} &= \text{taxe\_fonciere\_mensuelle} \times 12 \\
\text{gestion}(y) &= \text{loyer}(y) \times \frac{\text{gestion\_locative\_pct}}{100}
\end{aligned}
$$

### Tax base and tax

$$
\text{revenu\_foncier}(y) = \text{loyer}(y) - \text{interets}(y) - \text{charges\_copro} - \text{tf} - \text{gestion}(y)
$$

$$
\text{impot}(y) =
\begin{cases}
\text{revenu\_foncier}(y) \times \text{taux\_fiscal} & \text{if } \text{revenu\_foncier}(y) > 0 \\[4pt]
-\min\!\big(|\text{revenu\_foncier}(y)|,\ 10{,}700\big) \times \dfrac{\text{tmi}}{100} & \text{otherwise}
\end{cases}
$$

Negative impot here models a tax benefit from deductible deficit (simplified).

### Cash flow

$$
\text{mensualite\_an}(y) =
\begin{cases}
\text{mensualite} \times 12 & \text{if } y \le \text{duree\_pret\_ans} \\
0 & \text{otherwise}
\end{cases}
$$

$$
\text{cash\_flow}(y) = \text{loyer}(y) - \text{mensualite\_an}(y) - \text{charges\_copro} - \text{tf} - \text{gestion}(y) - \text{impot}(y)
$$

### Patrimoine net

$$
\text{patrimoine\_net}(y) = \text{valeur\_bien}(y) - \text{capital\_restant}(y)
$$

## 4.2 Strategy B - LMNP Meuble

This strategy was updated to include:
- deductible current charges block,
- amortization capping,
- amortization carryforward,
- deficit carryforward over 10 years.

### Revenue

$$
\text{loyer\_meuble\_mensuel} = \text{loyer\_meuble\_m2} \times \text{surface}
$$

$$
\text{loyer}(y) = \text{loyer\_meuble\_mensuel} \times 12 \times \left(1+\frac{\text{revalorisation\_loyer\_pct}}{100}\right)^{y-1} \times \left(1 - \frac{\text{vacance\_locative\_pct}}{100}\right)
$$

`loyer_meuble_m2` is a dedicated furnished-rent rate input, independent from `loyer_m2` (unfurnished). It no longer derives from `loyer_nu` via a fixed multiplier.

### Amortization hypotheses

$$
\begin{aligned}
\text{mobilier} &= \text{prix\_achat} \times 0.12 \\
\text{amort\_bien\_an} &= \text{prix\_achat} \times \frac{0.80}{30} \\
\text{amort\_mob}(y) &=
\begin{cases}
\text{mobilier} / 7 & 1 \le y \le 7 \\
0 & y > 7
\end{cases} \\
\text{amort\_frais\_acq\_annuel} &= \text{input parameter}
\end{aligned}
$$

### Step-by-step fiscal pipeline

**1) Deductible charges excluding amortization**

$$
\begin{aligned}
\text{charges\_courantes}(y) = {}& \text{interets}(y) + \text{charges\_copro}(y) + \text{tf}(y) + \text{gestion}(y) \\
&+ \text{travaux\_annuel} + \text{assurance\_pno\_annuel} + \text{cfe\_annuel} + \text{honoraires\_comptable\_annuel}
\end{aligned}
$$

**2) BIC before amortization**

$$
\text{bic\_avant\_amort}(y) = \text{loyer}(y) - \text{charges\_courantes}(y)
$$

**3) Capped amortization deduction**

$$
\text{amort\_total}(y) = \text{amort\_bien\_an} + \text{amort\_mob}(y) + \text{amort\_frais\_acq\_annuel} + \text{amort\_reporte\_anterieur}
$$

$$
\text{amort\_deductible}(y) = \min\!\Big(\text{amort\_total}(y),\ \max\big(0,\ \text{bic\_avant\_amort}(y)\big)\Big)
$$

$$
\text{amort\_reporte\_nouveau}(y) = \text{amort\_total}(y) - \text{amort\_deductible}(y)
$$

**4) BIC after amortization**

$$
\text{bic\_apres\_amort}(y) = \text{bic\_avant\_amort}(y) - \text{amort\_deductible}(y)
$$

**5) Deficit carryforward (10-year stock)**

The model keeps yearly deficit buckets with 10-year remaining life.

$$
\text{imputation\_deficit}(y) =
\begin{cases}
\text{sum applied from existing buckets (oldest first)} & \text{if } \text{bic\_apres\_amort}(y) > 0 \\
0 & \text{otherwise}
\end{cases}
$$

If $\text{bic\_apres\_amort}(y) < 0$, a new deficit bucket is created:

$$
\text{montant} = \big|\text{bic\_apres\_amort}(y)\big|, \qquad \text{annees\_restantes} = 10
$$

$$
\text{bic\_net\_imposable}(y) = \max\!\Big(0,\ \text{bic\_apres\_amort}(y) - \text{imputation\_deficit}(y)\Big)
$$

**6) Tax**

$$
\text{impot}(y) = \text{bic\_net\_imposable}(y) \times \text{taux\_fiscal}
$$

### Cash flow (economic)

LMNP cash flow remains an economic cash flow:

$$
\text{cash\_flow}(y) = \text{loyer}(y) - \text{mensualite\_an}(y) - \text{charges\_copro}(y) - \text{tf}(y) - \text{gestion}(y) - \text{impot}(y)
$$

Important:
- non-cash accounting items (amortissement) do not leave cash,
- but they affect tax through bic_net_imposable.

### Yearly outputs used in UI

- charges = charges_courantes
- amortissement = amort_deductible
- bic_imposable = bic_net_imposable

## 4.3 Strategy C - Location Courte Duree (Airbnb-like)

### Revenue hypotheses

$$
\begin{aligned}
\text{revenu\_nuitee} &= \text{loyer\_nu} \times 2.8 \\
\text{taux\_occupation} &= 0.70 \\
\text{revenu\_mensuel} &= \text{revenu\_nuitee} \times \text{taux\_occupation} \\
\text{revenu}(y) &= \text{revenu\_mensuel} \times 12 \times \left(1+\frac{\text{revalorisation\_loyer\_pct}}{100}\right)^{y-1}
\end{aligned}
$$

### Cost hypotheses

$$
\begin{aligned}
\text{charges\_copro} &= \text{charges\_copro\_mensuelle} \times 12 \\
\text{tf} &= \text{taxe\_fonciere\_mensuelle} \times 12 \\
\text{plateforme}(y) &= \text{revenu}(y) \times 0.15 \\
\text{conciergerie}(y) &= \text{revenu}(y) \times 0.20 \\
\text{menage} &= 150 \times 12
\end{aligned}
$$

### Fiscal base

$$
\begin{aligned}
\text{mobilier} &= 20{,}000 \quad \text{(fixed)} \\
\text{amort\_bien\_an} &= \text{prix\_achat} \times \frac{0.80}{30} \\
\text{amort\_mob}(y) &=
\begin{cases}
\text{mobilier} / 7 & 1 \le y \le 7 \\
0 & y > 7
\end{cases}
\end{aligned}
$$

$$
\text{bic}(y) = \text{revenu}(y) - \text{interets}(y) - \text{charges\_copro} - \text{tf} - \text{plateforme}(y) - \text{conciergerie}(y) - \text{menage} - \text{amort\_bien\_an} - \text{amort\_mob}(y)
$$

$$
\text{impot}(y) = \max\big(0,\ \text{bic}(y)\big) \times \text{taux\_fiscal}
$$

### Cash flow

$$
\text{cash\_flow}(y) = \text{revenu}(y) - \text{mensualite\_an}(y) - \text{charges\_copro} - \text{tf} - \text{plateforme}(y) - \text{conciergerie}(y) - \text{menage} - \text{impot}(y)
$$

### Patrimoine

$$
\text{patrimoine\_net}(y) = \text{valeur\_bien}(y) - \text{capital\_restant}(y)
$$

## 4.4 Strategy D - SCPI

### Capital and return hypotheses

$$
\begin{aligned}
\text{frais\_entree} &= 9\% \\
\text{capital\_net} &= \text{apport} \times (1 - 0.09) \\
\text{rendement} &= \frac{\text{rendement\_scpi}}{100} \\
\text{revalorisation\_parts} &= 1\%\ \text{per year}
\end{aligned}
$$

### Yearly loop

$$
\begin{aligned}
\text{revenu}(y) &= \text{valeur\_parts}(y-1) \times \text{rendement} \\
\text{impot}(y) &= \text{revenu}(y) \times \text{taux\_fiscal} \\
\text{cash\_flow}(y) &= \text{revenu}(y) - \text{impot}(y) \\
\text{valeur\_parts}(y) &= \text{valeur\_parts}(y-1) \times 1.01
\end{aligned}
\qquad \text{with } \text{valeur\_parts}(0) = \text{capital\_net}
$$

In SCPI rows:
- patrimoine_net = valeur_parts

## 4.5 Strategy E - Residence Principale

### Economic benefit approach

No rental income is modeled.
Instead, the model uses avoided rent:

$$
\text{loyer\_economise}(y) = \text{loyer\_nu} \times 12 \times \left(1+\frac{\text{revalorisation\_loyer\_pct}}{100}\right)^{y-1}
$$

### Costs and cash flow differential

$$
\text{charges} = \text{charges\_copro} + \text{tf}
$$

$$
\text{cash\_flow}(y) = \text{loyer\_economise}(y) - \text{mensualite\_an}(y) - \text{charges\_copro} - \text{tf}
$$

### Patrimoine

$$
\text{patrimoine\_net}(y) = \text{valeur\_bien}(y) - \text{capital\_restant}(y)
$$

## 5) Output Indicators - Definitions

## 5.1 Global summary indicators

- prix_achat
- frais_notaire
- cout_total
- emprunt
- mensualite
- loyer_mensuel_brut

$$
\text{rendement\_brut\_nu} = \frac{\text{loyer\_nu} \times 12}{\text{prix\_achat}} \times 100
$$

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

**cash_flow_moyen** — average monthly cash flow over horizon:

$$
\text{cash\_flow\_moyen} = \text{round}\!\left(\frac{\sum_{y} \text{cash\_flow}(y)}{\text{horizon\_ans} \times 12}\right)
$$

**patrimoine_net_final** — last yearly patrimoine_net.

**rendement_brut**:

$$
\text{rendement\_brut} =
\begin{cases}
\dfrac{\text{loyer\_nu} \times 12}{\text{prix\_achat}} \times 100 & \text{Location Nue} \\[8pt]
\dfrac{\text{loyer\_meuble} \times 12}{\text{prix\_achat}} \times 100 & \text{LMNP} \\[8pt]
\dfrac{\text{revenu\_mensuel} \times 12}{\text{prix\_achat}} \times 100 & \text{Courte Duree} \\[8pt]
\text{rendement\_scpi (input)} & \text{SCPI} \\[8pt]
0 & \text{Residence Principale}
\end{cases}
$$

**tri (IRR)** — computed from yearly cash flow series + terminal value component (see section 6).

**van (NPV)** — net present value of the same cash-flow vector used for TRI (see section 6.2), discounted at the user-set required return:

$$
\text{van} = \sum_{i=0}^{n} \frac{\text{cf}_i}{(1 + r)^{i}}, \qquad r = \frac{\text{taux\_actualisation}}{100}
$$

`taux_actualisation` is a direct user input (default 4%) — it is not derived from CAPM or a beta assumption.

**stress_van** — same NPV formula, applied to a haircut scenario:

$$
\begin{aligned}
\text{cf}_i^{\text{stress}} &= \text{cf}_i \times \text{stress\_cashflow\_factor} && (i = 1..n) \\
\text{terminal}^{\text{stress}} &= \text{terminal} \times \text{stress\_terminal\_factor}
\end{aligned}
$$

`stress_pass = stress_van > 0`.

**is_candidate** — `van > 0`.

**is_recommended** — among candidates (or, if none, among all strategies), the strategy with the highest `van`.

**coc_return_pct** — cash-on-cash return, year 1 cash flow over the initial equity outlay:

$$
\text{coc\_return\_pct} = \frac{\text{cash\_flow}(1)}{|\text{initial\_outlay}|} \times 100
$$

**dscr** — Debt Service Coverage Ratio, year 1 income over year 1 annual debt service:

$$
\text{dscr} = \frac{\text{loyer\_annuel}(1)\ \text{or}\ \text{loyer\_economise}(1)}{\text{mensualite\_an}(1)}
$$

Not applicable to SCPI (no financed asset) — returned as `null`. A value ≥ 1 means year-1 rent alone covers the mortgage payment.

## 6) TRI / IRR Construction

## 6.1 General numerical method

- Newton-Raphson iterations
- max iterations: 1000
- tolerance: 1e-8
- return accepted only if rate in a bounded interval (model guardrail)

## 6.2 Cash-flow vectors by strategy

**Location Nue**
- initial outflow: $-(\text{apport} + \text{frais\_notaire})$
- yearly inflows: annual cash_flow
- final add-on: $\text{valeur\_fin} - \text{capital\_restant\_fin}$

**LMNP**
- initial outflow: $-(\text{apport} + \text{frais\_notaire} + \text{mobilier})$
- yearly inflows: annual cash_flow
- final add-on: $\text{valeur\_fin} - \text{capital\_restant\_fin}$

**Courte Duree**
- initial outflow: $-(\text{apport} + \text{frais\_notaire} + \text{mobilier})$
- yearly inflows: annual cash_flow
- final add-on: $\text{valeur\_fin} - \text{capital\_restant\_fin}$

**SCPI**
- initial outflow: $-\text{apport}$
- yearly inflows: annual cash_flow
- final add-on: final valeur_parts

**Residence Principale**
- initial outflow: $-(\text{apport} + \text{frais\_notaire})$
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
