"""
GAMMA_RRA sensitivity sweep -- national maize calibration, all 4 arms.

CONTEXT (see Data Analysis/External_Parameters_Sourced.md #5):
GAMMA_RRA is a placeholder (2.0, "typical
ag-household range ~1-3") with no clean single sourced replacement. The two
real Ethiopia-specific risk-elicitation studies found this project disagree
in DIRECTION, not just magnitude -- Vieider et al. (2018) imply a forced
one-parameter fit of RRA ~= -0.63 (risk-SEEKING; the authors themselves flag
this as a poor fit to their richer, S-shaped finding), while Hadush &
Gebregziabher (2022) find a sample squarely in risk-AVERSE territory on a
different measure. Averaging two studies that disagree on sign isn't
defensible, so the decision (2026-07-20) is to sweep GAMMA_RRA across a
range spanning both signs and see how much of H1/H2/H4 depends on it,
rather than pick one point estimate.

IMPORTANT -- negative GAMMA_RRA is not a bug: the farmer's objective is
    E[profit] - (abs_risk_aversion / 2) * Var[profit],   abs_risk_aversion = GAMMA_RRA / W0
When GAMMA_RRA < 0, -(abs_risk_aversion/2) is POSITIVE: variance now ADDS to
the objective instead of subtracting from it. The model farmer becomes a
variance-seeker on that side of the sweep -- that's what "risk-seeking"
means inside this framework, and a qualitative kink at gamma=0 is the
expected signature of it working correctly, not a sign of a scaling error
(contrast with the corner-solution diagnostic in Simulation/README.md, where
a bug looked like a UNIFORM zero across every arm/calibration at once).

This script does not modify bpmm_monte_carlo.py. It imports that module's
already-built NATIONAL_MAIZE calibration and its simulate_arm/optimal_investment
functions unchanged, and only overrides abs_risk_aversion per grid point via
optimal_investment's existing override parameter (calib.W0 itself does not
depend on GAMMA_RRA, only on P_Y and YA, so it stays valid across the sweep).

One deliberate departure from bpmm_monte_carlo.py's own convention: unlike
compute_all_arms (which lets optimal_investment and the follow-up
simulate_arm draw independent shocks), this sweep draws ONE shared
(theta_yield, theta_price) pair up front and reuses it for every gamma/arm
combination -- so the N*-vs-gamma and profit-vs-gamma curves reflect only
the risk-aversion effect, not point-to-point Monte Carlo noise. National
maize only (not the 8 region-crop combinations) -- this is a targeted
robustness check on the single flagship calibration, not a re-run of the
whole regional comparison.
"""

import os
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from bpmm_monte_carlo import (
    NATIONAL_MAIZE, ARMS, N_MC, OUTDIR,
    draw_theta_yield, draw_theta_price, optimal_investment, simulate_arm,
)

# Spans Vieider et al.'s implied -0.63 through past the "typical 1-3" range,
# including 0 (risk-neutral) as an explicit reference point.
GAMMA_GRID = np.round(np.arange(-2.0, 4.01, 0.5), 2)

REFERENCE_POINTS = {
    -0.63: "Vieider et al. (2018) implied RRA",
    0.0: "risk-neutral",
    2.0: "current placeholder",
}


def run_sweep(calib=NATIONAL_MAIZE, n=N_MC):
    """One shared shock draw for the whole sweep -- see module docstring."""
    theta_yield = draw_theta_yield(n, calib)
    theta_price = draw_theta_price(n)

    rows = []
    for gamma in GAMMA_GRID:
        abs_ra = gamma / calib.W0
        for name, cfg in ARMS.items():
            N_star = optimal_investment(cfg["r"], cfg["insured"], calib,
                                         abs_risk_aversion=abs_ra, n=n,
                                         theta_yield=theta_yield, theta_price=theta_price)
            _, revenue, profit, default = simulate_arm(
                N_star, cfg["r"], cfg["insured"], calib, n=n,
                theta_yield=theta_yield, theta_price=theta_price)
            rows.append({
                "gamma_rra": gamma, "arm": name, "N_star_kgNeq_ha": round(N_star, 1),
                "mean_profit_birr_ha": round(profit.mean(), 1),
                "sd_profit_birr_ha": round(profit.std(), 1),
                "default_rate_pct": round(100 * default.mean(), 2),
            })
    return rows


def write_csv(rows):
    path = os.path.join(OUTDIR, "gamma_rra_sweep.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return path


def plot_sweep(rows):
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    for name in ARMS:
        gammas = [r["gamma_rra"] for r in rows if r["arm"] == name]
        n_stars = [r["N_star_kgNeq_ha"] for r in rows if r["arm"] == name]
        ax.plot(gammas, n_stars, marker="o", markersize=3, label=name)

    ax.axvline(0, color="black", linewidth=0.9, linestyle="-", alpha=0.6)
    colors = {-0.63: "#c44e52", 0.0: "#555555", 2.0: "#8172b2"}
    for gamma_ref, label in REFERENCE_POINTS.items():
        if gamma_ref != 0.0:  # 0 already drawn as the solid axline above
            ax.axvline(gamma_ref, color=colors[gamma_ref], linewidth=0.8,
                       linestyle=":", label=f"{label} ({gamma_ref})")

    ax.set_xlabel("GAMMA_RRA (relative risk aversion; negative = risk-seeking)")
    ax.set_ylabel("Optimal extra investment N* (kg N-eq/ha)")
    ax.set_title("Sensitivity of optimal investment to risk-aversion assumption\n(national maize, all 4 arms)")
    ax.legend(fontsize=7, loc="best")
    fig.tight_layout()
    path = os.path.join(OUTDIR, "GAMMA_RRA_sweep.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def print_reference_summary(rows):
    print(f"\n{'gamma_rra':>10} {'arm':<24}{'N* (kgN/ha)':>14}{'profit (birr/ha)':>18}{'sd':>12}{'default %':>11}")
    for gamma_ref, label in REFERENCE_POINTS.items():
        closest = min(GAMMA_GRID, key=lambda g: abs(g - gamma_ref))
        print(f"\n-- {label}: gamma={gamma_ref} (nearest grid point: {closest}) --")
        for row in rows:
            if row["gamma_rra"] == closest:
                print(f"{row['gamma_rra']:>10} {row['arm']:<24}{row['N_star_kgNeq_ha']:>14.1f}"
                      f"{row['mean_profit_birr_ha']:>18.1f}{row['sd_profit_birr_ha']:>12.1f}"
                      f"{row['default_rate_pct']:>10.2f}%")


if __name__ == "__main__":
    print(f"Running GAMMA_RRA sweep: {GAMMA_GRID[0]} to {GAMMA_GRID[-1]} in steps of 0.5, "
          f"national maize, all 4 arms ({len(GAMMA_GRID)} x {len(ARMS)} = {len(GAMMA_GRID)*len(ARMS)} evaluations)...")
    rows = run_sweep()
    csv_path = write_csv(rows)
    png_path = plot_sweep(rows)
    print(f"Saved {csv_path}")
    print(f"Saved {png_path}")
    print_reference_summary(rows)
