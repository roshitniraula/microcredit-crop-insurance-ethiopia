# Sourced external parameters (non-GYGA)

Sourcing and derivation for every shared (non-GYGA) parameter in
`Simulation/bpmm_monte_carlo.py`. Each value is marked in the script as
`# SOURCED` or `# PLACEHOLDER`; `Simulation/SYNTHETIC_DATA.md` gives the
one-line summary, this file gives the detail. Yield calibration (GYGA) is
documented in `Simulation/README.md` and `Region_Crop_Selection_Summary.md`.

| Parameter | Value | Status | Section |
|---|---|---|---|
| `R_CONTROL` | 0.27 | Sourced | §1 |
| `P_Y_MAIZE` / `P_Y_SORGHUM` | 62.0 / 85.0 birr/kg | Sourced | §2 |
| `P_N` | 250.0 birr/kg N-eq. | Placeholder, fertilizer component corroborated | §3 |
| `THETA_FLOOR` / `INSURANCE_LOADING` | 0.85 / 1.3 | Assumed, consistent with real product design | §4 |
| `GAMMA_RRA` | 2.0 | Assumed, bracketed by two field studies; sensitivity sweep | §5 |
| `CV_PRICE` | 0.27 | Sourced | §2, §5 |
| `FARM_CV_INFLATION` | 2.05 | Sourced (regional, not household-level) | §7 |
| `INCENTIVE_RATE_CUT` | 0.015 | Authors' assumption, no external source | — |

## 1. MFI interest rate (`R_CONTROL`)

**Value: 27%.** Birr Metrics ("At 30 Percent Interest, Who Wins? Ethiopia's
Microfinance Paradox," 18 Oct 2025) quotes Torban Microfinance's CEO: *"We
pay around 20 percent interest to depositors, and lend out at roughly 27
percent."* The same article cites a borrower paying 30% on one loan and
describes 13-14% as a historical concessional-partnership rate.

This is one named institution, not a portfolio-wide average, but it is
current, dated, and a retail lending rate. Treat 27% as a point estimate,
30% as a documented upper case, and the NBE policy rate (16%, Jan 2026) as a
floor.

**Why an observed rate rather than a regulated one.** There is no
regulatory MFI lending-rate cap. NBE Directive NBE/INT/12/2017 (effective
11 Oct 2017), §2.1, leaves bank lending rates "to be freely determined by
each bank"; Directive MFI/29/2017 applies the same rule to microfinance
institutions. Directive NBE/INT/13/2026 (effective 9 Jan 2026) repeals and
replaces 12/2017 but keeps lending rates market-determined.

Other figures considered, and why they were not used:

| Figure | Source | Year | Why not used |
|---|---|---|---|
| ACSI & OCSSCO ~12%/year (rural Amhara & Oromiya) | Tarozzi, Desai & Johnson (2015) | 2002-03 | Over 20 years old; predates the high-inflation 2020s |
| Global median MFI interest yield ~27% | Rosenberg et al., CGAP/MIX (2013) | 2011 | Not Ethiopia-specific (agrees with the value used) |
| Cross-country mean real rate 36.6% (897 MFIs, 106 countries) | Rauf et al. (2022) | 2008-2020 | Not Ethiopia-specific |
| Institution-level APRs for OCSSCO/ACSI | MFTransparency.org | 2011-era | Site no longer reachable; would predate the 2025 figure anyway |

## 2. Producer / output prices (`P_Y_MAIZE`, `P_Y_SORGHUM`) and price volatility (`CV_PRICE`)

Target crops are maize and sorghum in all four regions (see
`Region_Crop_Selection_Summary.md`).

### Price levels

**Values: maize 62 birr/kg, sorghum 85 birr/kg** (wholesale-equivalent).

Derived from the FEWS NET Data Warehouse market price API
(`https://fdw.fews.net/api/marketpricefacts/`, no account required), full
Ethiopia series for Maize Grain (White), Sorghum (White) and Sorghum
(Yellow), saved in `FEWS NET Prices/`:

1. Addis Ababa Merkato retail, May 2026: maize 70.75 birr/kg; sorghum White
   89.34 and Yellow 106.00, averaged 97.67 birr/kg.
2. Wholesale/retail ratio, computed from every market-month in which FEWS
   NET reports both price types: maize 0.873 (520 pairs, national), sorghum
   0.866 (31 pairs, White variety; Yellow's wholesale series ends in 2015).
3. Maize: 70.75 × 0.873 ≈ **62**. Sorghum: 97.67 × 0.866 ≈ **85**.

**Why the price is crop-specific.** Sorghum is priced well above maize in
Ethiopia, confirmed by two independent methods about seven years apart:
FAOSTAT official 2018 producer prices (maize 5.64, sorghum 7.64 birr/kg,
~35% gap) and the May 2026 FEWS NET Merkato comparison above (~38% gap). A
single shared price would misstate whichever crop it did not match.

**Independent cross-checks of the maize level** (none is a farmgate quote):

| Estimate | Source | Period |
|---|---|---|
| ~37-38 birr/kg wholesale, ~44-45 retail (Adama reference market; $284-290/MT wholesale at ~130 ETB/USD) | USDA FAS GAIN Report ET2025-0011, "Grain and Feed Annual" | Jan-Mar 2025 |
| 22.56 birr/kg export unit value | Selina Wamucii, Ethiopia maize price page | May 2026 |
| ~30-65 birr/kg retail | FEWS NET Ethiopia Price Bulletin | Apr 2024 |

FAOSTAT's Producer Price Index (2014-2016 = 100) projects the 2018 prices
forward to only ~10-13 birr/kg by 2025, but every year of that index is
FAO-estimated (flag "E"), and it does not appear to capture the July 2024
currency float. It is treated as an outlier.

**Limitations.**
- Wholesale is not farmgate; a true farmgate price would sit somewhat below
  these values. No farmgate quote was found for either crop.
- The retail level is Addis Ababa Merkato-specific, while the ratio is
  pooled from other markets (Merkato has no month with both price types).
  Bahir Dar and Dessie are among the main contributing markets; Jimma and
  Hawassa are not.
- Sorghum's ratio comes from the White variety but is applied to the
  White+Yellow average.
- One national price per crop is used in all four regions.
- Sorghum's absolute level rests on FEWS NET alone.

### Price volatility

**Value: CV_PRICE = 0.27**, from FAOSTAT's officially reported (flag "A")
annual producer prices for Ethiopian maize and sorghum, 1994-2018 (bulk
export `Prices_E_All_Data.zip`, January 2026; area 238, items 56 and 83).
Year-over-year log-return volatility, annualized across the single
reporting gap (2008 to 2010), converted to a CV:

| Crop | Full series (1994-2018) | 2008-2018 subset |
|---|---|---|
| Maize | ≈ 0.29 | ≈ 0.23 |
| Sorghum | ≈ 0.26 | ≈ 0.17 |
| **Pooled (both crops, full series)** | **≈ 0.27** | — |

Volatility measures swings within the officially reported window, so it
does not need to be carried forward across the 2024 currency float.
Cross-check: the same statistic computed from six FEWS NET market/product
series (2004-2024 wholesale and 2019-2026 retail) falls in 0.18-0.35 for
five of the six.

Because the index insurance in the model is yield-indexed only, price risk
is uninsured in every arm (basis risk). 1994-2018 volatility may understate
current risk given the instability of the 2020s. A crop-specific CV_PRICE
(maize 0.29, sorghum 0.26) is available from the same computation but is
not used.

## 3. Fertilizer / input price (`P_N`)

**Value: 250 birr/kg N-equivalent — placeholder.** `P_N` prices a bundle of
fertilizer, seed and labor per kg of nitrogen-equivalent. Only the
fertilizer component has a sourced anchor; seed and labor costs are
unsourced, so the parameter stays marked `# PLACEHOLDER`.

**Fertilizer component ≈ 262 birr/kg N.** Shega (D. Metaferiya,
"Subsidies, Supply Chains, and the Limits of Ethiopia's Fertilizer Model,"
29 Jun 2026) states that "the subsidized farm-gate price held at 4,972 birr
per quintal" for the 2026 Meher season. Ethiopia's standard NPS blend is
19% N (with urea at 46% N), confirmed by three independent sources:
Ahmed & Bekele (2022), Ayalew, Chamberlin & Newman (2022, Table 4 note),
and a 2020 IJRAS district study (Kachabirra District, Kembata Tambaro
Zone). Reading 4,972 as an NPS price:

4,972 birr/quintal ÷ 100 kg ÷ 0.19 ≈ **262 birr/kg N**, within ~5% of 250.

**Interpretation risk.** If 4,972 were instead a program-wide average over
a roughly 1:1 NPS:urea mix (effective N ≈ 32.5%), the fertilizer component
would be ≈ 153 birr/kg N. The NPS reading is adopted because it continues
Addis Fortune's explicitly NPS-specific price series (1,600 birr/quintal in
2021, ~4,500-4,577 in early 2022) with no stated change in what is
measured. Confidence: medium.

Earlier price points, consistent with that trajectory:

| Figure | Source | Year |
|---|---|---|
| NPS 1,600 → ~4,500-4,577 birr/quintal | Addis Fortune, "Skyrocketing Fertiliser Costs Petrify Farmers" | 2021 → early 2022 |
| Local fertilizer 27,735 → 47,150 birr/tonne (2,774 → 4,715 birr/quintal) | IFPRI blog on domestic fertilizer markets | 2020 → 2022 |
| Spike to 4,800 birr/quintal | The Reporter Ethiopia | Mar 2022 |
| Subsidy of 4,972 birr/quintal (subsidy amount; net farmer price not stated) | Kana TV News | 2025/26 season |

Context from the Shega article: Ethiopia applies ~45.3 kg/ha of fertilizer
(roughly 30% of the world average); the 4,972 price held only because
procurement was contracted before the Feb-Apr 2026 Strait of Hormuz closure
roughly doubled global urea prices; and the subsidy is an IMF Extended
Credit Facility parameter designed to shrink. The price is a current
snapshot, not a stable level.

## 4. Insurance design (`THETA_FLOOR`, `INSURANCE_LOADING`)

**Values: payout floor 0.85, loading 1.3 (30%) — assumed.** The model pays
out when the yield shock falls below 85% of expected yield.

- **Trigger level.** 85% is the highest individual-yield coverage level in
  USDA RMA crop insurance ("Coverage levels range from 50 to 85 percent of
  your approved yield"), and within the 50-90% range the World Bank gives
  for area-yield index insurance trigger yields.
- **Ethiopian product.** VICI, an NDVI-based index insurance product
  (Copernicus Land Monitoring Service use case; Laterite policy brief, Sept
  2019, published Jan 2021): partial payout begins at the 15th percentile
  of the historical local NDVI distribution, with maximum payout at or below
  the 5th percentile and linear payout in between. A floor at the low tail
  of the yield distribution is directionally consistent with this design.
- **Premium level.** Laterite gives commercially viable premiums of 15% of
  coverage for drought-only insurance and 20-25% for hybrid
  (drought + pest/disease) insurance. These are premium-to-coverage ratios,
  not loadings over the actuarially fair premium, so they are not directly
  comparable to 1.3, but they suggest 1.3 is not high relative to real
  Ethiopian pricing.
- **Willingness to pay** (Laterite): ~50% of farmers would pay the
  15%-of-coverage rate for ETB 2,000 coverage, ~37% for ETB 4,000; WTP drops
  sharply near ETB 200-250, anchored on the ETB 240/year Community-Based
  Health Insurance premium.
- The VICI product covers cereals (maize, wheat, sorghum, teff, barley).

## 5. Risk aversion (`GAMMA_RRA`) and output-price volatility (`CV_PRICE`)

**Value: γ = 2.0 — assumed.** Two Ethiopia-specific field studies exist but
disagree in direction, so neither gives a point estimate:

- **Vieider et al. (2018)**, >500 rural household heads in several
  highland regions, certainty-equivalent elicitation. Households are on
  average significantly *risk-seeking* for small-to-medium probabilities
  (up to p ≈ 0.5) and risk-averse only for larger ones, an S-shaped pattern
  in the sense of Markowitz (1952). The central estimate is a probability-
  weighting function (Prelec form: α = 0.538, β = 0.703, δ = 0.233), a
  dimension this model does not have. The forced one-parameter power-utility
  fit gives ρ = 1.634 (se 0.065), i.e. RRA = 1 − ρ ≈ −0.63, which the
  authors say "does not provide a good fit."
- **Hadush & Gebregziabher (2022)**, 518 dairy farmers in Tigray, 7-item
  safe-choice count. Mean score 4.411 (SD 2.120) out of 7, in the paper's
  own risk-averse range (> 2). The ordinal score is not converted to a CRRA
  coefficient.

The studies differ in instrument, region and year, so regional
heterogeneity is as plausible an explanation as either being wrong.

**Sensitivity sweep** (`Simulation/gamma_rra_sweep.py`,
`Simulation/gamma_rra_sweep.csv`): national maize, all four arms, γ from
−2.0 to +4.0 in steps of 0.5.
- The rate effect never reverses: Control never invests more than T1.
  Control and T1 tie at γ = 3.0 and 4.0.
- The insurance effect depends on the sign of γ. Insured arms (T2/T3)
  invest more than T1 only for γ > 0. For γ < 0 (the direction Vieider et
  al. imply), T1 invests more, because variance reduction has no value to a
  variance-seeking objective. The arms tie at γ = 0.

H2's validity is therefore conditional on farmers being risk-averse.

**CV_PRICE**: see §2.

## 6. Agricultural credit flow (context only)

Not a model parameter and not used in the paper. Section retained so that
section numbers cited elsewhere remain stable.

## 7. Farm-level yield variability (`FARM_CV_INFLATION`)

**Value: 2.05.** GYGA's `CV_YA` is a climate-zone figure, which smooths out
the year-to-year swings an individual farm faces. `FARM_CV_INFLATION`
scales it up toward farm-level risk.

**Derivation.** `Etho-Agr Dataset.xlsx` (a copy of Mekecha, "Ethiopian
cereal crop dataset (1996-2022)," figshare, CC BY 4.0) is a national
region × crop × year panel (10 regions, 7 cereals). Its year-to-year
temporal yield CV for each study region, divided by the matching GYGA
`CV_YA`:

| Region (→ study zone) | Crop | Years | Mean yield (kg/ha) | Temporal CV |
|---|---|---|---|---|
| Oromiya (→ Jimma) | Maize | 26 | 2,810 | 0.317 |
| Oromiya (→ Jimma) | Sorghum | 26 | 2,024 | 0.272 |
| Amhara (→ Bahir Dar, Dessie) | Maize | 26 | 2,713 | 0.342 |
| Amhara (→ Bahir Dar, Dessie) | Sorghum | 26 | 1,810 | 0.309 |
| S.N.N.P.R (→ Hawassa) | Maize | 26 | 2,538 | 0.353 |
| S.N.N.P.R (→ Hawassa) | Sorghum | 26 | 1,636 | 0.372 |

Implied ratios: Jimma-Maize 1.85, Jimma-Sorghum 2.78, Bahir Dar-Maize 2.14,
Bahir Dar-Sorghum 2.03, Dessie-Maize 2.50, Dessie-Sorghum 1.41,
Hawassa-Maize 1.49, Hawassa-Sorghum 2.16.

The mean of these rounded ratios is 2.05, the value used. The exact mean
from unrounded ratios is 2.044. The difference is small relative to the
spread across combinations (1.41-2.78).

Harari's rows were excluded: their yields (~45,000-47,000 kg/ha) are an
obvious error in the source, roughly an order of magnitude too high for
rainfed cereals. Harari is not a study region.

**Limitations.**
- This is regional, not household-level. The same spatial-averaging
  critique that applies to GYGA applies here, at a coarser unit.
- A household-level panel CV, for example from the World Bank's Ethiopia
  Socioeconomic Panel Survey (ESPS), would be a better source.
- Even household survey yields understate true farm risk. Sida et al. (2021)
  found, from full-plot harvests of 230 Amhara maize fields, that intra-plot
  heterogeneity accounts for 62-74% of total variability. Single-subplot
  crop cuts misrepresent it.

## Sources

- Ahmed, K., & Bekele, D. (2022). Effect of blended NPS fertilizer on food barley varieties in Gurawa District, Ethiopia. *Asian Journal of Plant Science & Research*, 12(5). https://doi.org/10.36648/2249-7412/22.12.5.223
- Ayalew, H., Chamberlin, J., & Newman, C. (2022). Site-specific agronomic information and technology adoption: A field experiment from Ethiopia. *Journal of Development Economics*, 156, 102788. https://doi.org/10.1016/j.jdeveco.2021.102788
- Birr Metrics (M. Tariku), "At 30 Percent Interest, Who Wins? Ethiopia's Microfinance Paradox," 18 Oct 2025. https://birrmetrics.com/at-30-percent-interest-who-wins-ethiopias-microfinance-paradox/
- Addis Fortune (T. Hailemichael), "Skyrocketing Fertiliser Costs Petrify Farmers, Threaten Productivity," 19 Mar 2022. https://addisfortune.news/skyrocketing-fertiliser-costs-petrify-farmers-threaten-productivity/
- Copernicus Land Monitoring Service, "Vegetation Index Crop Insurance (VICI) service," 2022. https://land.copernicus.eu/en/use-cases/vegetation-index-crop-insurance-vici-service
- FAOSTAT, Producer Prices (PP) domain; bulk export `Prices_E_All_Data.zip` (Jan 2026). https://www.fao.org/faostat/en/#data/PP
- FEWS NET Data Warehouse, market price facts API (queried 19 Jul 2026). https://fdw.fews.net/ — raw series in `FEWS NET Prices/`
- FEWS NET, Ethiopia Price Bulletin, April 2024.
- Hadush, M., & Gebregziabher, K. (2022). It is too late to regret and take risk: Farmers' adoption decision for stall-feeding (SF) in Tigray, Ethiopia. *Review of Agricultural and Applied Economics*, 25(2), 79-98. https://doi.org/10.15414/raae.2022.25.02.79-98
- IFPRI blog, "Grappling with compounding crises in domestic fertilizer markets in Africa: The case of Ethiopia." https://www.ifpri.org/blog/grappling-compounding-crises-domestic-fertilizer-markets-africa-case-ethiopia/
- Kana TV News, "Ethiopia Spent $525 Million Subsidizing Fertilizer Imports This Year," 29 Jun 2026. https://kanatelevision.com/news/ethiopia-spent-usd525-million-subsidizing-fertilizer-imports-this-year-a-usd4-billion-plant/
- Laterite, "Ethiopian smallholder farmers' willingness to pay for crop micro-insurance," policy brief, Jan 2021. https://www.laterite.com/wp-content/uploads/2021/02/Laterite_Policy-Brief_GGGI_WTP-crop-micro-insurance_Jan2021.pdf
- Markowitz, H. (1952). The utility of wealth. *Journal of Political Economy*, 60(2), 151-158.
- Mekecha, B. B. (2024). Ethiopian cereal crop dataset (1996-2022): Regional annual yield, production, and cultivated area trends. figshare, ver. 2. https://doi.org/10.6084/m9.figshare.27680280.v2 — copy in `Etho-Agr Dataset.xlsx`
- National Bank of Ethiopia, Directive No. MFI/29/2017 (11 Oct 2017), applying Directive No. NBE/INT/12/2017. https://nbe.gov.et/wp-content/uploads/2023/04/mif-29-2017.pdf
- National Bank of Ethiopia, Directive No. NBE/INT/13/2026 (9 Jan 2026). https://nbe.gov.et/wp-content/uploads/2026/01/DIRECTIVE-NO.NBE-INT-13-2026-INTEREST-RATES-AS-AMENDED-.pdf
- Rauf et al. (2022). *Frontiers in Psychology*, 13, 1008002. https://doi.org/10.3389/fpsyg.2022.1008002
- Rosenberg, R., Gaul, S., Ford, W., & Tomilova, O. (2013). *Microcredit interest rates and their determinants: 2004-2011*. CGAP / MIX / KfW.
- Selina Wamucii, Ethiopia maize prices (checked 9 Jun 2026). https://www.selinawamucii.com/insights/prices/ethiopia/maize/
- Shega (D. Metaferiya), "Subsidies, Supply Chains, and the Limits of Ethiopia's Fertilizer Model," 29 Jun 2026. https://shega.co/news/subsidies-supply-chains-and-the-limits-of-ethiopia-s-fertiliser-model
- Sida, T. S., Chamberlin, J., Ayalew, H., Kosmowski, F., & Craufurd, P. (2021). Implications of intra-plot heterogeneity for yield estimation accuracy: Evidence from smallholder maize systems in Ethiopia. *Field Crops Research*, 267, 108147. https://doi.org/10.1016/j.fcr.2021.108147
- Tarozzi, A., Desai, J., & Johnson, K. (2015). The impacts of microcredit: Evidence from Ethiopia. *American Economic Journal: Applied Economics*, 7(1), 54-89. https://doi.org/10.1257/app.20130475
- The Reporter Ethiopia, fertilizer price coverage, March 2022.
- USDA Foreign Agricultural Service, GAIN Report ET2025-0011, "Grain and Feed Annual," Post Addis Ababa, 7 May 2025.
- USDA Risk Management Agency, "Grain sorghum – Arizona," fact sheet, 2018 crop year. https://legacy.rma.usda.gov/fields/ca_rso/2018/azgrainsorghum.pdf
- Vieider, F. M., Beyene, A., Bluffstone, R., Dissanayake, S., Gebreegziabher, Z., Martinsson, P., & Mekonnen, A. (2018). Measuring risk preferences in rural Ethiopia. *Economic Development and Cultural Change*, 66(3), 417-446. https://doi.org/10.1086/696106
- World Bank, "Deep dive into area yield index insurance (AYII)," training session, Mar 2024. https://www.financialprotectionforum.org/sites/default/files/Deep%20dive%20into%20AYII.pdf
