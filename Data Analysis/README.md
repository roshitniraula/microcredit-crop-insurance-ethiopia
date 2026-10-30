# Data Analysis — index

Calibration data and parameter sourcing for `Simulation/bpmm_monte_carlo.py`.
The scripts do not read these files at runtime. Every value they use is
transcribed into the script as a constant with a source comment, and the
files here are the provenance for those constants.

| File | What it is | Used for | License |
|---|---|---|---|
| `GYGA/GygaEthiopia.xlsx` | Global Yield Gap Atlas Ethiopia export: actual yield (YA), water-limited potential (YW), yield variability, N-input targets, by crop, station and climate zone. | National calibration (`NATIONAL_MAIZE`, "Country" sheet, rainfed maize). The "Climate zone" sheet is also the source of the regional rows below. | CC BY-NC-SA 4.0 |
| `Region_Crop_Calibration.xlsx` | Every crop present in the GYGA climate zones matched to Jimma, Bahir Dar, Dessie and Hawassa, with a `LOCAL_EVIDENCE_NOTE` column. | The 8 regional calibrations (maize and sorghum rows). | Derived from GYGA: CC BY-NC-SA 4.0 |
| `FEWS NET Prices/` | FEWS NET Data Warehouse market prices for maize and sorghum, all Ethiopian markets, 2004-2026. See its README. | `P_Y_MAIZE` and `P_Y_SORGHUM`; cross-check of `CV_PRICE`. | Public (FEWS NET data usage policy) |
| `Etho-Agr Dataset.xlsx` | Copy of Mekecha (2024), Ethiopian cereal crop panel: 10 regions × 7 cereals × 1996-2022 (area, production, yield). | `FARM_CV_INFLATION` (regional temporal yield CV ÷ GYGA `CV_YA`). Harari's rows contain implausible yields and were excluded. | CC BY 4.0 |
| `External_Parameters_Sourced.md` | Sourcing and derivation for every non-GYGA parameter, §1-§7. | — | — |
| `Region_Crop_Selection_Summary.md` | Why these four regions and these two crops, and how each region was matched to a GYGA climate zone. | — | — |

Parameters without a data file here are cited directly to their published
sources in `External_Parameters_Sourced.md`:
- `R_CONTROL`: Birr Metrics, plus NBE directives for regulatory context.
- `CV_PRICE`: the FAOSTAT producer-price bulk export.
- The fertilizer component of `P_N`: Shega 2026.
- The insurance design: Laterite, VICI and USDA RMA.
- `GAMMA_RRA`: Vieider et al. 2018 and Hadush & Gebregziabher 2022.
