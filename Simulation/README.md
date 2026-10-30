# BPMM Monte Carlo simulation

Technical reference for the three scripts in this folder. Parameter values
and their sources are in `SYNTHETIC_DATA.md` (summary) and
`../Data Analysis/External_Parameters_Sourced.md` (derivations).

## Purpose

Simulates a smallholder's credit-financed input decision under the Baseline
Profit Maximization Model (BPMM) and Insurance-Adjusted Credit Model (IACM)
described in the paper. The aim is to test whether the theoretical
mechanisms behind hypotheses H1-H4 hold once the model is populated with
sourced parameters. It is a theory check, distinct from the randomized
controlled trial the paper proposes.

## Running

```
pip install -r ../requirements.txt
python bpmm_monte_carlo.py        # national + regional four-arm comparison
python gamma_rra_sweep.py         # risk-aversion sensitivity sweep
python loan_bounded_analysis.py   # 15,000-50,000 ETB loan-size extension
```

Each script writes its outputs into this folder and regenerates the
committed CSVs exactly (tested with Python 3.13 and the pinned versions in
`requirements.txt`). The main model takes about 5 seconds; the first run in
a fresh environment is slower while matplotlib builds its font cache.

## Model specification

A farmer chooses extra credit-financed input `N` (kg N-equivalent/ha, on top
of current practice) to maximize `E[profit] - (A/2)·Var[profit]`, a
mean-variance proxy for risk aversion.

- **Yield response.** Yield follows a diminishing-returns curve from actual
  yield `YA` toward the water-limited potential `YW`. The curve is fitted
  (`scipy.optimize.curve_fit`) to GYGA's estimates of the extra N needed to
  close 30%, 50% and 80% of the yield gap.
- **Shocks.** Each simulated season draws a yield shock and an output-price
  shock, both mean-one lognormal. The yield CV is GYGA's `CV_YA` scaled by
  `FARM_CV_INFLATION`; the price CV is `CV_PRICE`.
- **Loan and repayment.** The loan is `P_N · N`. Repayment due is
  `(1 + r) · loan`, and profit is revenue minus repayment due.
- **Insurance (T2, T3).** Insurance is yield-indexed. It pays
  `max(THETA_FLOOR − θ_yield, 0)` × expected revenue. The premium is
  `INSURANCE_LOADING` × the expected payout and is financed into the loan.
  Price risk is not covered (basis risk).
- **Risk aversion.** `A = GAMMA_RRA / W0`, where `W0` is the reference
  wealth `P_Y · YA` (birr/ha) of each calibration.
- **Optimization.** Grid search over `N_GRID` (0-615 kg N-eq/ha in steps
  of 5), with `N_MC = 10,000` draws per evaluation.

| Arm | Interest rate | Insurance | Repayment incentive |
|---|---|---|---|
| Control | `R_CONTROL` = 27% | No | No |
| T1 | `R_LOW` = 3% | No | No |
| T2 | 3% | Yes | No |
| T3 | 3% − `INCENTIVE_RATE_CUT` = 1.5% | Yes | Yes |

## Calibrations

A `Calibration` dataclass carries everything that varies by region and crop:
`YA`, `YW`, `CV_YA`, the N-input targets, and `P_Y`. All calibrations are
built by `make_calibration()`:

- **`NATIONAL_MAIZE`**: the national "Country" sheet of
  `../Data Analysis/GYGA/GygaEthiopia.xlsx` (rainfed maize).
- **`build_region_crop_calibrations()`**: 4 regions (Jimma, Bahir Dar,
  Dessie, Hawassa) × 2 crops (maize, sorghum), from GYGA climate-zone data in
  `../Data Analysis/Region_Crop_Calibration.xlsx`. See
  `../Data Analysis/Region_Crop_Selection_Summary.md` for why these regions
  and crops.

The 8 regional calibrations are built lazily, inside
`run_region_crop_comparison()`. Each one draws 200,000 samples to price its
insurance, and building them only after the national run keeps them from
perturbing that run's random-number stream.

## Outputs

| File | Produced by | Content |
|---|---|---|
| `arm_summary.csv` | `bpmm_monte_carlo.py` | National maize, four arms: N\*, mean yield, mean and SD of profit, default rate, repayment burden |
| `regional_arm_summary.csv` | `bpmm_monte_carlo.py` | Same columns, 8 region-crop combinations × 4 arms |
| `H1_investment_vs_rate.png` | `bpmm_monte_carlo.py` | Optimal investment vs. interest rate (0-30%), uninsured, national |
| `H2_insurance_effect.png` | `bpmm_monte_carlo.py` | Insurance's effect on investment and the profit distribution |
| `H3_default_rate_by_arm.png` | `bpmm_monte_carlo.py` | Default rate and repayment burden by arm |
| `H4_profit_control_vs_combined.png` | `bpmm_monte_carlo.py` | Profit distribution, Control vs. T3 |
| `Regional_H1-H4_*.png` | `bpmm_monte_carlo.py` | The same four tests across the 8 region-crop combinations |
| `gamma_rra_sweep.csv`, `GAMMA_RRA_sweep.png` | `gamma_rra_sweep.py` | National maize, all arms, γ from −2.0 to +4.0 in steps of 0.5 |
| `loan_bounded_arm_summary.csv`, `regional_loan_bounded_arm_summary.csv`, `Loan_Bounded_Participation.png` | `loan_bounded_analysis.py` | N restricted to 60-200 kg N-eq/ha (15,000-50,000 ETB at `P_N` = 250), with a decline-the-loan option |

**Repayment burden** is repayment due as a percentage of revenue. Because
the insurance premium is financed into the loan, burden is higher in the
insured arms.

**Default rate** is the share of draws in which revenue falls short of
repayment due. It is 0.00% in every calibration and at every γ in the sweep.
A mean-variance optimizer facing thin-tailed shocks chooses investment
levels that keep revenue above the amount due.

## Extensions

- **`gamma_rra_sweep.py`** imports the main model unchanged and re-runs the
  national four-arm comparison at each γ. It tests whether H2 depends on
  farmers being risk-averse (it does: the insured arms invest more than T1
  only for γ > 0).
- **`loan_bounded_analysis.py`** bounds the farmer's choice to the
  product's 15,000-50,000 ETB loan range.
  - Above the cap, the farmer takes the largest loan.
  - Below the floor, the farmer compares the best in-range loan against not
    borrowing at all (N = 0) and may decline. This is the standard
    discrete-continuous treatment (Hausman, 1985).
  - The participation comparison uses 200,000 draws because a binary
    decision is more sensitive to Monte Carlo error. Reported statistics use
    10,000.
  - The script uses its own seed-42 generator, so its N\* values are
    independent estimates. They agree with `arm_summary.csv` within Monte
    Carlo noise, not exactly.

## Reproducibility and Monte Carlo error

- A single generator, `np.random.default_rng(42)`, supplies every draw in
  `bpmm_monte_carlo.py`.
- Within each optimization, the grid search reuses the same shock draws for
  every candidate `N` and across the H1 rate sweep. These common random
  numbers make the objective smooth instead of noisy.
- Each arm draws its own shocks, so small between-arm differences of one
  5 kg grid step are within Monte Carlo noise. An example is Hawassa maize,
  where Control is 35 and T1 is 30.
- `convergence_check()` shows that the mean-profit estimate is stable to
  well under 1% at 10,000 draws.

## Calibration sensitivity

`P_N` is set where marginal revenue and marginal financing cost are
comparable. With a much cheaper input, the optimizer picks the top of the
grid at any interest rate, and the rate effect (H1) cannot appear.

The highest N\* in any run, including the γ sweep down to −2.0, is 515 kg
N-eq/ha. That is below the grid ceiling, so no result is pinned at the
grid edge.

## Implementation pitfalls

Both of these fail silently: they produce a degenerate result (all-zero or
all-corner investment) rather than an error. Check for them when extending
the model.

1. **Unit mismatch.** GYGA yield is in tonnes/ha, while `P_Y` is in birr/kg.
   Multiplying them directly understates revenue 1000× and makes every
   investment unprofitable. Handled by `KG_PER_TONNE`.
2. **Unscaled risk aversion.** With profit in birr, an absolute penalty on
   `Var[profit]` (birr²) swamps `E[profit]` for any non-trivial γ and drives
   investment to zero. Handled by scaling with reference wealth
   (`A = GAMMA_RRA / W0`).

A real corner solution is selective: some arms or calibrations sit at
N\* = 0 while treated arms respond. A scaling bug is uniform, with every arm
in every calibration at zero, including the insured arms. If a parameter
change makes the treated arms collapse to zero across most calibrations,
check the `W0` scaling first.
