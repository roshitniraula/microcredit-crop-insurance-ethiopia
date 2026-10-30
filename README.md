# Low-Interest, Insurance-Backed Agricultural Credit in Ethiopia

Code and calibration data for the paper *The impact of low-interest,
insurance-backed agricultural credit on smallholder farmers' investment, and
repayment challenges in Ethiopia*.

A Monte Carlo simulation of a smallholder's credit-financed input decision
compares four credit products for maize and sorghum farmers in Jimma, Bahir
Dar, Dessie and Hawassa:

| Arm | Interest rate | Crop insurance | Repayment incentive |
|---|---|---|---|
| Control | 27% | No | No |
| T1 | 3% | No | No |
| T2 | 3% | Yes | No |
| T3 | 1.5% (3% − 1.5 pp) | Yes | Yes |

## Repository layout

```
Simulation/                       Model code, outputs (CSV), figures (PNG)
  bpmm_monte_carlo.py             Main model: national + 8 region-crop calibrations
  gamma_rra_sweep.py              Risk-aversion sensitivity sweep
  loan_bounded_analysis.py        15,000-50,000 ETB loan-size extension
  README.md                       Model specification and outputs
  SYNTHETIC_DATA.md               Sourced vs. assumed parameters
Data Analysis/                    Calibration data and parameter sourcing
  GYGA/GygaEthiopia.xlsx          Global Yield Gap Atlas export (yield, yield gap, variability)
  Region_Crop_Calibration.xlsx    GYGA climate-zone values for the 4 regions
  FEWS NET Prices/                Maize and sorghum market prices, 2004-2026
  Etho-Agr Dataset.xlsx           Regional cereal yield panel, 1996-2022
  External_Parameters_Sourced.md  Source and derivation for every non-GYGA parameter
  Region_Crop_Selection_Summary.md  Why these regions and crops
```

## Reproducing the results

Tested with Python 3.13 and the versions pinned in `requirements.txt`.

```bash
pip install -r requirements.txt
cd Simulation
python bpmm_monte_carlo.py        # arm_summary.csv, regional_arm_summary.csv, H1-H4 figures
python gamma_rra_sweep.py         # gamma_rra_sweep.csv, GAMMA_RRA_sweep.png
python loan_bounded_analysis.py   # loan_bounded_*.csv, Loan_Bounded_Participation.png
```

All scripts use a fixed seed (42). Reported statistics use 10,000 draws per
evaluation; the loan-size extension uses 200,000 draws for its
participation decision.

Each script regenerates its committed CSV files exactly. The main model runs
in about 5 seconds. The scripts read no data files at runtime: calibration
values are constants in `bpmm_monte_carlo.py`, with their sources in
`Data Analysis/`.

## Data sources

| Input | Source |
|---|---|
| Yield, yield gap, yield variability | Global Yield Gap Atlas (www.yieldgap.org); van Ittersum et al. (2013) |
| Control lending rate (27%) | Birr Metrics (2025); NBE Directives MFI/29/2017 and NBE/INT/13/2026 |
| Output prices (maize 62, sorghum 85 birr/kg) | FEWS NET Data Warehouse (May 2026); FAOSTAT producer prices |
| Price volatility (CV 0.27) | FAOSTAT producer prices, 1994-2018 |
| Farm-risk inflation factor (2.05) | Mekecha (2024) regional cereal panel vs. GYGA |
| Input price (250 birr/kg N-eq.) | Fertilizer component corroborated by Shega (2026) |
| Insurance trigger and loading | Laterite (2019/2021), VICI index-insurance product, USDA RMA |
| Risk aversion (γ = 2.0) | Assumed; bracketed by Vieider et al. (2018) and Hadush & Gebregziabher (2022), with sensitivity sweep |

Full citations are in `Data Analysis/External_Parameters_Sourced.md`.
Parameters marked as assumptions there are calibration choices, not
estimates.

## License

- **Code** (`*.py`): MIT License, see `LICENSE`.
- **Data** keeps the license of its source:
  - GYGA files (`GygaEthiopia.xlsx`, and `Region_Crop_Calibration.xlsx`, which is derived from it): CC BY-NC-SA 4.0.
  - `Etho-Agr Dataset.xlsx` (Mekecha, 2024): CC BY 4.0.
  - FEWS NET price series: public, under the FEWS NET data usage policy.
- **Documentation and generated outputs**: CC BY 4.0.

## Citation

See `CITATION.cff`, or use GitHub's "Cite this repository" button.
