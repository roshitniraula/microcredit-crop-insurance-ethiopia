"""
Loan-size-bounded extension of the BPMM/IACM Monte Carlo model.

`bpmm_monte_carlo.py` lets the farmer's credit-financed input choice N range
freely over N_GRID (0-615 kg N-eq/ha), with no connection to the paper's
stated microfinance product scope of 15,000-50,000 ETB (see the "Loan Size
and Microfinance Scope" section of the paper). This script bounds that
choice to what the proposed product actually offers, so the farmer's problem
becomes a genuine constrained-choice microeconomic problem rather than an
unconstrained optimum.

At P_N = 250 birr/kg (the model's credit-financed input price), the loan
range implies N bounds of 60-200 kg N-eq/ha (LOAN_MIN_ETB / P_N and
LOAN_MAX_ETB / P_N respectively).

Above the cap (N* > 200 under the unconstrained model) is a standard corner
solution: the farmer takes the largest loan the product offers, since more
investment is still better than less. Below the floor (N* < 60) is a real
economic decision, not a corner solution to paper over: rather than forcing
every farmer up to the minimum loan regardless of fit, this script follows
the standard discrete-continuous choice treatment (Hausman, 1985) and
compares the best in-range point against a "no credit" outside option
(N=0 -- the farmer grows without this credit-financed input at all, no loan,
no repayment). If the minimum loan overshoots what the farmer would actually
choose, they decline the product. This choice is also the one consistent
with this project's own cited insurance-takeup evidence (Ahmed, McIntosh &
Sarris, 2019), where Ethiopian farmers were shown to decline a real
index-insurance product at near-zero rates even when it was free -- real
takeup in this market is not automatic just because a product exists.

This script imports bpmm_monte_carlo.py unchanged and does not modify it,
the same pattern already used by gamma_rra_sweep.py. It writes two new,
separate output files (loan_bounded_arm_summary.csv,
regional_loan_bounded_arm_summary.csv) rather than overwriting
arm_summary.csv / regional_arm_summary.csv, so the existing unconstrained
results remain intact and citable until a deliberate decision is made to
fold these numbers into the paper.

Reproducibility note: this script uses its own fixed-seed random number
generator (seed=42, same seed convention as bpmm_monte_carlo.py), rather
than reusing bpmm_monte_carlo's shared `rng` object. Reusing the imported
module's `rng` would make this script's results depend on incidental
import-time side effects in bpmm_monte_carlo.py (specifically, how many
random draws NATIONAL_MAIZE's construction consumes at import) rather than
on anything in this script -- fragile, and not reproducible on its own
terms. A dedicated local generator keeps this script fully self-contained,
consistent with the "one generator, fixed seed, used for every draw"
principle bpmm_monte_carlo.py itself follows. This does mean N* values here are independent Monte Carlo
estimates, not byte-identical to arm_summary.csv/regional_arm_summary.csv
even for combinations whose optimum falls inside the loan range -- expect
agreement within Monte Carlo noise (well under 1% per the model's own
convergence check at N_MC=10,000 draws), not exact equality.
"""

import os
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from bpmm_monte_carlo import (
    P_N, N_MC, ARMS, OUTDIR, CV_PRICE,
    simulate_arm, NATIONAL_MAIZE, build_region_crop_calibrations,
)

_rng = np.random.default_rng(42)


def _draw_theta_yield(n, calib):
    """Local reimplementation of bpmm_monte_carlo.draw_theta_yield, using
    this script's own generator instead of the imported module's shared one
    (see reproducibility note above). Same lognormal, mean-one,
    CV-matched parameterization."""
    sigma2 = np.log(1 + calib.EFFECTIVE_CV_YA ** 2)
    sigma = np.sqrt(sigma2)
    mu = -sigma2 / 2
    return _rng.lognormal(mu, sigma, n)


def _draw_theta_price(n):
    """Local reimplementation of bpmm_monte_carlo.draw_theta_price -- see
    _draw_theta_yield docstring."""
    sigma2 = np.log(1 + CV_PRICE ** 2)
    sigma = np.sqrt(sigma2)
    mu = -sigma2 / 2
    return _rng.lognormal(mu, sigma, n)


LOAN_MIN_ETB = 15_000.0
LOAN_MAX_ETB = 50_000.0
N_MIN = LOAN_MIN_ETB / P_N   # 60.0 kg N-eq/ha
N_MAX = LOAN_MAX_ETB / P_N   # 200.0 kg N-eq/ha
LOAN_GRID = np.arange(N_MIN, N_MAX + 5.0, 5.0)  # 60, 65, ..., 200

# The base model's N_MC=10,000 was validated (via bpmm_monte_carlo's own
# convergence check) for *point-estimate* accuracy on mean profit -- well
# under 1% error. A binary participate/decline decision is more sensitive
# to noise than that: empirically, at least one cell (Hawassa Maize, T1)
# flips sign between two different seeds at N_MC=10,000, and only settles
# to a stable answer at higher draw counts. This script therefore uses a
# larger draw count specifically for the participation comparison, still
# cheap at this problem size (36 optimizations total).
N_MC_PARTICIPATION = 200_000


def optimal_investment_bounded(r, insured, calib, n=N_MC_PARTICIPATION, theta_yield=None, theta_price=None):
    """Grid-search the farmer's mean-variance-optimal investment within the
    product's loan range, and compare it against the 'no credit' outside
    option (N=0). Returns (N_star, participates): N_star is None when the
    farmer is better off declining the product than taking its minimum loan.

    Uses the same common-random-numbers convention as
    bpmm_monte_carlo.optimal_investment(): one set of shocks, shared across
    every candidate N *and* the outside option, so the in-range-vs-outside
    comparison isn't distorted by independent Monte Carlo noise.

    Returns (N_star, participates, margin_pct): margin_pct is the percentage
    gap between the best in-range objective and the outside option's,
    relative to the outside option -- a small |margin_pct| flags a
    borderline participation call worth reporting, not just a bare Yes/No.
    """
    abs_risk_aversion = calib.ABS_RISK_AVERSION
    if theta_yield is None:
        theta_yield = _draw_theta_yield(n, calib)
    if theta_price is None:
        theta_price = _draw_theta_price(n)

    best_N, best_obj = None, -np.inf
    for N in LOAN_GRID:
        _, _, profit, _ = simulate_arm(N, r, insured, calib, theta_yield=theta_yield, theta_price=theta_price)
        obj = profit.mean() - (abs_risk_aversion / 2) * profit.var()
        if obj > best_obj:
            best_obj, best_N = obj, N

    # Outside option: no loan at all. N=0 makes loan = P_N * 0 = 0, so
    # repayment_due = (1+r)*0 = 0 regardless of r -- a clean "farmer grows
    # without this credit-financed input" baseline (see simulate_arm).
    _, _, profit_outside, _ = simulate_arm(0.0, r, False, calib, theta_yield=theta_yield, theta_price=theta_price)
    obj_outside = profit_outside.mean() - (abs_risk_aversion / 2) * profit_outside.var()

    margin_pct = 100 * (best_obj - obj_outside) / abs(obj_outside)
    if best_obj > obj_outside:
        return best_N, True, margin_pct
    return None, False, margin_pct


def compute_all_arms_bounded(calib, n_report=N_MC):
    """Loan-bounded analogue of bpmm_monte_carlo.compute_all_arms(): all 4
    arms, but N is restricted to LOAN_GRID and a farmer may opt out entirely
    (see optimal_investment_bounded). The participate/decline decision itself
    uses N_MC_PARTICIPATION draws (more precision needed for a binary call
    near indifference); the reported yield/profit/burden statistics at the
    chosen N* use n_report draws, matching the rest of this project's
    reporting convention (N_MC=10,000, from bpmm_monte_carlo.py)."""
    results = {}
    for name, cfg in ARMS.items():
        N_star, participates, margin_pct = optimal_investment_bounded(cfg["r"], cfg["insured"], calib)
        if participates:
            yld, revenue, profit, default = simulate_arm(N_star, cfg["r"], cfg["insured"], calib, n=n_report)
        else:
            # Declines the product: no loan, no insurance, baseline yield only.
            yld, revenue, profit, default = simulate_arm(0.0, cfg["r"], False, calib, n=n_report)
        burden = 1 - profit / revenue
        results[name] = dict(N_star=N_star, participates=participates, margin_pct=margin_pct,
                              yield_mean=yld.mean(), profit_mean=profit.mean(), profit_sd=profit.std(),
                              default_rate=default.mean(), burden_mean=burden.mean(), profit=profit)
    return results


def _n_star_cell(r):
    return round(r["N_star"], 1) if r["participates"] else ""


def write_loan_bounded_summary_csv(results):
    path = os.path.join(OUTDIR, "loan_bounded_arm_summary.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["arm", "r", "insured", "participates", "participation_margin_pct",
                    "N_star_kgNeq_ha", "mean_yield_t_ha", "mean_profit_birr_ha",
                    "sd_profit_birr_ha", "default_rate_pct", "mean_repayment_burden_pct"])
        for name, cfg in ARMS.items():
            r = results[name]
            w.writerow([name, cfg["r"], cfg["insured"], r["participates"], round(r["margin_pct"], 2),
                        _n_star_cell(r), round(r["yield_mean"], 2), round(r["profit_mean"], 1),
                        round(r["profit_sd"], 1), round(100 * r["default_rate"], 2),
                        round(100 * r["burden_mean"], 2)])
    return path


def run_region_crop_comparison_bounded(calibrations=None):
    if calibrations is None:
        calibrations = build_region_crop_calibrations()

    all_results = {}
    rows = []
    for calib in calibrations:
        results = compute_all_arms_bounded(calib)
        all_results[(calib.region, calib.crop)] = results
        for name, cfg in ARMS.items():
            r = results[name]
            rows.append([calib.region, calib.crop, name, cfg["r"], cfg["insured"], r["participates"],
                         round(r["margin_pct"], 2), _n_star_cell(r), round(r["yield_mean"], 2),
                         round(r["profit_mean"], 1), round(r["profit_sd"], 1),
                         round(100 * r["default_rate"], 2), round(100 * r["burden_mean"], 2)])

    csv_path = os.path.join(OUTDIR, "regional_loan_bounded_arm_summary.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["region", "crop", "arm", "r", "insured", "participates", "participation_margin_pct",
                    "N_star_kgNeq_ha", "mean_yield_t_ha", "mean_profit_birr_ha", "sd_profit_birr_ha",
                    "default_rate_pct", "mean_repayment_burden_pct"])
        w.writerows(rows)

    return all_results, csv_path


def plot_participation(all_results, calibrations):
    """One new figure: which region-crop x arm cells opt out of the
    15,000-50,000 ETB product under this bounded model -- the one genuinely
    new finding this analysis produces."""
    arm_names = list(ARMS.keys())
    grid = np.array([[1 if all_results[(c.region, c.crop)][name]["participates"] else 0
                       for name in arm_names] for c in calibrations])
    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.imshow(grid, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(arm_names)))
    ax.set_xticklabels(arm_names, rotation=30, ha="right", fontsize=8)
    ax.set_yticks(range(len(calibrations)))
    ax.set_yticklabels([f"{c.region} - {c.crop}" for c in calibrations], fontsize=8)
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            ax.text(j, i, "Yes" if grid[i, j] else "No", ha="center", va="center", fontsize=8)
    ax.set_title("Participation in the 15,000-50,000 ETB product\nby region-crop combination and arm")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "Loan_Bounded_Participation.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    print("=" * 72)
    print(f"Loan-bounded analysis: N in [{N_MIN:.0f}, {N_MAX:.0f}] kg N-eq/ha "
          f"({LOAN_MIN_ETB:,.0f}-{LOAN_MAX_ETB:,.0f} ETB at P_N={P_N:.0f} birr/kg)")
    print("=" * 72)

    BORDERLINE_PCT = 3.0  # flag any participation call within +/-3% margin

    national_results = compute_all_arms_bounded(NATIONAL_MAIZE)
    national_csv = write_loan_bounded_summary_csv(national_results)
    print(f"\nNational (maize):  -> {national_csv}")
    for name, cfg in ARMS.items():
        r = national_results[name]
        n_disp = f"{r['N_star']:.0f}" if r["participates"] else "opts out"
        flag = "  <-- BORDERLINE, verify before citing" if abs(r["margin_pct"]) < BORDERLINE_PCT else ""
        print(f"  {name:<24}{cfg['r']*100:>6.1f}%  N*={n_disp:>10}  "
              f"profit={r['profit_mean']:>12,.0f} birr/ha  margin={r['margin_pct']:+6.2f}%{flag}")

    calibrations = build_region_crop_calibrations()
    regional_results, regional_csv = run_region_crop_comparison_bounded(calibrations)
    print(f"\nRegional (8 combos x 4 arms) -> {regional_csv}")
    for calib in calibrations:
        for name, cfg in ARMS.items():
            r = regional_results[(calib.region, calib.crop)][name]
            n_disp = f"{r['N_star']:.0f}" if r["participates"] else "opts out"
            flag = "  <-- BORDERLINE, verify before citing" if abs(r["margin_pct"]) < BORDERLINE_PCT else ""
            print(f"  {calib.region:<12}{calib.crop:<10}{name:<24}N*={n_disp:>10}  "
                  f"margin={r['margin_pct']:+6.2f}%{flag}")

    plot_participation(regional_results, calibrations)
    print("\nParticipation figure -> Loan_Bounded_Participation.png")
