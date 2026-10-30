# Parameter provenance for `bpmm_monte_carlo.py`

Every model input is either **sourced** (real, dated, cited data) or
**assumed** (a calibration choice, not an estimate). Assumed values are
marked `# PLACEHOLDER` in the script. Full derivations and confidence levels
are in `Data Analysis/External_Parameters_Sourced.md`.

There are 9 calibrations: national maize plus 4 regions × 2 crops.

## Sourced, varies by region and crop

From GYGA (Global Yield Gap Atlas): the national "Country" sheet of
`Data Analysis/GYGA/GygaEthiopia.xlsx` for the default calibration, and
climate-zone data (`Data Analysis/Region_Crop_Calibration.xlsx`) for the 8
region-crop combinations.

| Field | What it is |
|---|---|
| `YA` | Current actual yield, t/ha |
| `YW` | Water-limited potential yield (ceiling), t/ha |
| `CV_YA` | Temporal coefficient of variation of actual yield |
| `N30` / `N50` / `N80` | Extra N (kg/ha) to close 30% / 50% / 80% of the yield gap |

## Sourced, varies by crop (shared across regions)

| Parameter | Value | Source |
|---|---|---|
| `P_Y_MAIZE` | 62.0 birr/kg | FEWS NET Data Warehouse, Addis Ababa Merkato retail, May 2026 (70.75 birr/kg) × wholesale/retail ratio 0.873 (520 market-months). §2 |
| `P_Y_SORGHUM` | 85.0 birr/kg | Same method: White (89.34) and Yellow (106.00) averaged, 97.67 birr/kg × 0.866 (31 market-months). §2 |

Sorghum is priced ~35-38% above maize, confirmed by FAOSTAT's 2018 official
prices (maize 5.64, sorghum 7.64 birr/kg) and by the 2026 FEWS NET
same-market comparison. A single shared price would misstate one crop
alongside otherwise crop-specific yield data. The arm comparisons are made
within each region-crop combination, so a crop-specific price does not
confound the H1-H4 tests.

## Sourced, shared across all calibrations

| Parameter | Value | Source |
|---|---|---|
| `R_CONTROL` | 0.27 | Torban Microfinance's stated lending rate (Birr Metrics, 18 Oct 2025). One named institution, not a portfolio average; no regulated MFI rate exists to cite (NBE Directive MFI/29/2017). §1 |
| `CV_PRICE` | 0.27 | FAOSTAT official annual producer prices, maize and sorghum pooled, 1994-2018, year-to-year log-return volatility. Five of six FEWS NET market series fall in 0.18-0.35. Price risk is uninsured in every arm (basis risk). §2 |
| `FARM_CV_INFLATION` | 2.05 | Ratio of `Data Analysis/Etho-Agr Dataset.xlsx` regional temporal yield CV to GYGA `CV_YA`, averaged over the 8 region-crop combinations (exact mean 2.044). Regional, not household-level. §7 |

## Assumed, shared across all calibrations

| Parameter | Value | Basis |
|---|---|---|
| `P_N` | 250.0 birr/kg N-eq. | Fertilizer + seed + labor bundle. The fertilizer component is corroborated within ~5% (Shega 2026 farm-gate NPS price ÷ 19% N ≈ 262 birr/kg N); seed and labor are unsourced. The level also keeps financing cost non-trivial in the investment decision (see `README.md`, "Calibration sensitivity"). §3 |
| `GAMMA_RRA` | 2.0 | Two Ethiopian field studies disagree in sign: Vieider et al. (2018) risk-seeking, Hadush & Gebregziabher (2022) risk-averse. Examined with a sweep from −2.0 to +4.0 (`gamma_rra_sweep.py`). §5 |
| `INCENTIVE_RATE_CUT` | 0.015 | Authors' assumption for T3's repayment incentive; no external source. |
| `THETA_FLOOR` | 0.85 | Consistent with the 85% top coverage level in USDA RMA and with VICI's low-tail index trigger. §4 |
| `INSURANCE_LOADING` | 1.3 | Not directly comparable to VICI's 15-25%-of-coverage premiums. §4 |
| `R_LOW` | 0.03 | Policy design parameter: midpoint of the proposed 0-5% low-interest range. |

`R_CONTROL`, `CV_PRICE` and the assumed parameters are uniform across crops
and regions. Differences between regions in the outputs therefore come only
from the GYGA yield data; differences between maize and sorghum also
reflect the crop-specific price.
