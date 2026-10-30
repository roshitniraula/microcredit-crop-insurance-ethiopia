"""
Monte Carlo simulation of the Baseline Profit Maximization Model (BPMM) /
Insurance-Adjusted Credit Model (IACM) described in the paper.

Farmer problem:
    E[pi] = E[f(N, theta)] - (1+r) * Loan(N)

where N is credit-financed input investment (kg N-equivalent/ha, ON TOP of
whatever the farmer already applies), theta is a multiplicative weather/price
shock, and f(N, theta) = theta * (YA + (YW - YA) * g(N)) is a diminishing-
returns yield-response function that saturates at the water-limited potential
yield YW.

Farmers choose N to maximize a mean-variance objective
    E[pi] - (gamma/2) * Var[pi]
which is the standard tractable proxy for risk aversion, and lets insurance
(a variance-reduction device) show up directly in the optimal investment
decision -- this is the mechanism behind H2.

Four arms, matching the paper's multi-arm design:
    Control : standard microcredit      (high r,  no insurance, no incentive)
    T1      : low-interest loan         (low r,   no insurance, no incentive)
    T2      : insurance-backed loan     (low r,   insurance,    no incentive)
    T3      : combined model            (low r,   insurance,    incentive)

CALIBRATIONS (the region/crop-specific inputs): every YA, YW, CV_YA, and the
three MIN_N_INPUT_TARGET_*_PERC points come from GYGA (Global Yield Gap Atlas)
data -- the national default from GygaEthiopia.xlsx ("Country" sheet, Rainfed
maize), the 8 region-crop combinations from
Data Analysis/Region_Crop_Calibration.xlsx. See the `Calibration` class below.

PARAMETER STATUS: every shared parameter below is marked "# SOURCED" or
"# PLACEHOLDER". Simulation/SYNTHETIC_DATA.md lists them all with their
basis; Data Analysis/External_Parameters_Sourced.md gives the derivations.
The placeholders (P_N, GAMMA_RRA, INCENTIVE_RATE_CUT) are shared across every
calibration, deliberately, rather than varied by crop/region.

Sourced shared parameters:
    R_CONTROL  -- a named Ethiopian MFI's stated lending rate (27%; see
                  External_Parameters_Sourced.md #1).
    CV_PRICE   -- FAOSTAT's official 1994-2018 Ethiopia producer-price series
                  for maize and sorghum (year-to-year log-return volatility,
                  pooled across both crops).
    P_Y_MAIZE, P_Y_SORGHUM -- wholesale-equivalent prices from the FEWS NET
                  Data Warehouse (Addis Ababa Merkato, May 2026 retail,
                  converted via the wholesale/retail ratio from FEWS NET's own
                  overlapping observations: 520 market-months for maize, 31
                  for sorghum; see External_Parameters_Sourced.md #2).

P_Y is crop-specific because Ethiopian sorghum prices run ~35-38% above
maize, confirmed by two independent methods (2018 FAOSTAT official annual
prices and the 2026 FEWS NET same-market comparison); a shared price would
be inconsistent with this model's already crop-specific yield data.

Run from this directory:  python bpmm_monte_carlo.py
Writes arm_summary.csv, regional_arm_summary.csv and the H1-H4 and
Regional_H1-H4 figures here. Fixed seed (42), 10,000 draws per evaluation.
gamma_rra_sweep.py and loan_bounded_analysis.py build on this module
without modifying it.
"""


import numpy as np
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import csv
import os
from dataclasses import dataclass

rng = np.random.default_rng(42)
OUTDIR = os.path.dirname(os.path.abspath(__file__))


def saturating(N, N0, k):
    return 1 - np.exp(-((N / N0) ** k))


# ---------------------------------------------------------------------------
# 1. SHARED PLACEHOLDER PARAMETERS -- same value for every calibration below.
#    See Simulation/SYNTHETIC_DATA.md for the full list with justification.
# ---------------------------------------------------------------------------
KG_PER_TONNE = 1000.0  # yield is in t/ha; P_Y is birr/kg
P_Y_MAIZE = 62.0    # SOURCED: wholesale-equivalent producer price, birr/kg. Addis Ababa Merkato retail, May 2026 = 70.75 birr/kg (FEWS NET Data Warehouse), x 0.873 wholesale/retail ratio (mean of 520 market-month pairs where FEWS NET reports both, nationally). Supersedes an earlier ~35 birr/kg estimate that used a wholesale/retail ratio computed from a single overlapping data point -- see Data Analysis/External_Parameters_Sourced.md #2.
P_Y_SORGHUM = 85.0  # SOURCED: wholesale-equivalent producer price, birr/kg. Addis Ababa Merkato retail, May 2026, White (89.34) and Yellow (106.00) varieties averaged = 97.67 birr/kg, x 0.866 wholesale/retail ratio (mean of 31 market-month pairs, Sorghum White). ~37% above P_Y_MAIZE -- independently corroborated by FAOSTAT's 2018 official annual prices (maize 5.64, sorghum 7.64 birr/kg, ~35% gap). See Data Analysis/External_Parameters_Sourced.md #2.
P_N = 250.0         # PLACEHOLDER (fertilizer component partially corroborated): birr/kg N-equivalent credit-financed input package (fertilizer + seed + labor bundle, not raw urea). The fertilizer piece alone now has a real, cited farm-gate anchor -- Shega's 4,972 birr/quintal 2025/26 NPS subsidy price / 19% N (Ministry-of-Agriculture NPS blend, 3 independent citations) = ~262 birr/kg-N, within 5% of this value -- but seed and labor costs remain completely unsourced, so this stays a placeholder overall, not "# SOURCED". See Data Analysis/External_Parameters_Sourced.md #3.
R_CONTROL = 0.27    # SOURCED: Torban Microfinance's stated typical lending rate, Birr Metrics, 18 Oct 2025 -- one named institution, not a portfolio-wide average; see Data Analysis/External_Parameters_Sourced.md #1 and Simulation/SYNTHETIC_DATA.md
R_LOW = 0.03        # midpoint of the paper's proposed 0-5% target -- not a placeholder, it's the policy target itself
GAMMA_RRA = 2.0     # PLACEHOLDER: relative risk aversion coefficient (typical ag-household range ~1-3)
INCENTIVE_RATE_CUT = 0.015   # PLACEHOLDER: extra rate discount for T3's repayment incentive
CV_PRICE = 0.27     # SOURCED: pooled maize+sorghum annual producer-price volatility, Ethiopia, FAOSTAT official series 1994-2018 (log-return sigma converted to CV) -- see Data Analysis/External_Parameters_Sourced.md #2 and Simulation/SYNTHETIC_DATA.md. Index insurance below is yield-indexed only, so it does NOT cover this price risk -- deliberate basis risk.
FARM_CV_INFLATION = 2.05  # SOURCED (regional, not household-level): ratio of Etho-Agr Dataset.xlsx regional temporal yield CV to GYGA CV_YA, averaged across the 8 region-crop combos (per-combo range 1.41-2.78; exact mean 2.044, 2.05 when averaged from ratios rounded to 2 dp). A household-level panel CV would be a better source. See Data Analysis/External_Parameters_Sourced.md #7.

# Insurance design (index-based, T2 & T3)
THETA_FLOOR = 0.85       # index floor: payout triggers below 85% of expected yield
INSURANCE_LOADING = 1.3  # insurer loading factor over actuarially fair premium

N_MC = 10_000                      # Monte Carlo draws per evaluation (see convergence check)
N_GRID = np.arange(0, 620, 5.0)    # candidate extra-investment levels, kg N-eq/ha


# ---------------------------------------------------------------------------
# 2. CALIBRATION -- region/crop-specific, sourced-from-data inputs.
#    Everything else in this file reads from a Calibration object instead of
#    module-level globals, so the same Monte Carlo logic runs unchanged for
#    the national default or any of the 8 region-crop combinations.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Calibration:
    region: str
    crop: str
    YA: float                  # t/ha, current actual yield
    YW: float                  # t/ha, water-limited potential yield (ceiling)
    CV_YA: float                # temporal coefficient of variation of actual yield
    N_TARGET_POINTS: np.ndarray  # [0, N_30pct, N_50pct, N_80pct] kg N-eq/ha
    GAP_CLOSURE_FRAC: np.ndarray  # [0, 0.30, 0.50, 0.80] -- fixed structural assumption, not data
    P_Y: float                  # birr/kg producer price -- crop-specific, sourced (see module docstring)
    N0_FIT: float                # fitted saturating-curve params (derived, not sourced or guessed)
    K_FIT: float
    EFFECTIVE_CV_YA: float       # CV_YA * FARM_CV_INFLATION
    SHORTFALL_PER_UNIT: float    # E[max(THETA_FLOOR - theta_yield, 0)] under this calibration's yield variance
    W0: float                    # reference wealth (birr/ha) used to scale risk aversion
    ABS_RISK_AVERSION: float     # GAMMA_RRA / W0


def make_calibration(region, crop, YA, YW, CV_YA, N30, N50, N80, P_Y):
    N_TARGET_POINTS = np.array([0.0, N30, N50, N80])
    GAP_CLOSURE_FRAC = np.array([0.0, 0.30, 0.50, 0.80])
    (N0_FIT, K_FIT), _ = curve_fit(saturating, N_TARGET_POINTS, GAP_CLOSURE_FRAC,
                                    p0=[150, 1.2], maxfev=10000)

    effective_cv_ya = CV_YA * FARM_CV_INFLATION
    sigma2 = np.log(1 + effective_cv_ya ** 2)
    sigma = np.sqrt(sigma2)
    mu = -sigma2 / 2
    theta_big = rng.lognormal(mu, sigma, 200_000)
    shortfall_per_unit = np.mean(np.maximum(THETA_FLOOR - theta_big, 0))

    W0 = KG_PER_TONNE * P_Y * YA
    abs_risk_aversion = GAMMA_RRA / W0

    return Calibration(region=region, crop=crop, YA=YA, YW=YW, CV_YA=CV_YA,
                        N_TARGET_POINTS=N_TARGET_POINTS, GAP_CLOSURE_FRAC=GAP_CLOSURE_FRAC,
                        P_Y=P_Y, N0_FIT=N0_FIT, K_FIT=K_FIT,
                        EFFECTIVE_CV_YA=effective_cv_ya, SHORTFALL_PER_UNIT=shortfall_per_unit,
                        W0=W0, ABS_RISK_AVERSION=abs_risk_aversion)


# National default -- GygaEthiopia.xlsx ("Country" sheet, Rainfed maize, Ethiopia).
# Unchanged from the original single-calibration version of this script.
NATIONAL_MAIZE = make_calibration(
    region="National (Ethiopia)", crop="Maize",
    YA=3.271301, YW=14.955811, CV_YA=0.146672,
    N30=90.641277, N50=151.068794, N80=253.164294,
    P_Y=P_Y_MAIZE,
)

# 4 regions x 2 crops (maize, sorghum) -- Data Analysis/Region_Crop_Calibration.xlsx,
# GYGA climate-zone data. Region/crop choice explained in
# Data Analysis/Region_Crop_Selection_Summary.md. P_Y is crop-specific
# (P_Y_MAIZE / P_Y_SORGHUM), matching each entry's crop.
#
# Built lazily (a function, not a module-level list) so that constructing
# these 8 calibrations -- each of which draws 200,000 samples from the shared
# `rng` to compute SHORTFALL_PER_UNIT -- never perturbs the draw stream ahead
# of the national-maize flagship run above. `run_region_crop_comparison()`
# calls this itself, after the national run has already consumed its draws.
def build_region_crop_calibrations():
    return [
        make_calibration("Jimma", "Maize",      YA=3.155677, YW=15.318144, CV_YA=0.171680, N30=92.837238, N50=154.728729, N80=259.297691, P_Y=P_Y_MAIZE),
        make_calibration("Jimma", "Sorghum",    YA=2.664333, YW=9.767780,  CV_YA=0.097831, N30=70.610461, N50=117.684102, N80=246.268117, P_Y=P_Y_SORGHUM),
        make_calibration("Bahir Dar", "Maize",   YA=3.298417, YW=11.864911, CV_YA=0.160055, N30=71.908554, N50=119.847589, N80=200.843136, P_Y=P_Y_MAIZE),
        make_calibration("Bahir Dar", "Sorghum", YA=2.092333, YW=6.344394,  CV_YA=0.152424, N30=45.863088, N50=76.438480,  N80=159.956700, P_Y=P_Y_SORGHUM),
        make_calibration("Dessie", "Maize",     YA=3.520341, YW=16.821133, CV_YA=0.136589, N30=101.946262, N50=169.910437, N80=284.739519, P_Y=P_Y_MAIZE),
        make_calibration("Dessie", "Sorghum",   YA=2.176139, YW=7.786598,  CV_YA=0.219283, N30=56.288660,  N50=93.814434,  N80=196.317971, P_Y=P_Y_SORGHUM),
        make_calibration("Hawassa", "Maize",    YA=2.816667, YW=11.880947, CV_YA=0.237012, N30=72.005742,  N50=120.009569, N80=201.114585, P_Y=P_Y_MAIZE),
        make_calibration("Hawassa", "Sorghum",  YA=2.140000, YW=6.521076,  CV_YA=0.172450, N30=47.140305,  N50=78.567176,  N80=164.411251, P_Y=P_Y_SORGHUM),
    ]


def gap_closure(N, calib):
    """Fraction of (YW - YA) gap closed by extra investment N (kg N-eq/ha)."""
    return saturating(np.maximum(N, 0), calib.N0_FIT, calib.K_FIT)


def expected_yield(N, calib):
    """Deterministic (theta=1) yield response curve, t/ha."""
    return calib.YA + (calib.YW - calib.YA) * gap_closure(N, calib)


def draw_theta_yield(n, calib):
    """Lognormal yield shock, mean 1, CV = calib.EFFECTIVE_CV_YA."""
    sigma2 = np.log(1 + calib.EFFECTIVE_CV_YA ** 2)
    sigma = np.sqrt(sigma2)
    mu = -sigma2 / 2
    return rng.lognormal(mu, sigma, n)


def draw_theta_price(n):
    """Lognormal output-price shock, mean 1, CV = CV_PRICE (shared, sourced)."""
    sigma2 = np.log(1 + CV_PRICE ** 2)
    sigma = np.sqrt(sigma2)
    mu = -sigma2 / 2
    return rng.lognormal(mu, sigma, n)


def simulate_arm(N, r, insured, calib, n=N_MC, theta_yield=None, theta_price=None):
    """Simulate one candidate investment level N under interest rate r, for a
    given calibration. Returns yield (t/ha), revenue, profit, default arrays
    of length n."""
    if theta_yield is None:
        theta_yield = draw_theta_yield(n, calib)
    if theta_price is None:
        theta_price = draw_theta_price(len(theta_yield))
    base_yield = expected_yield(N, calib)           # t/ha
    yield_realized = theta_yield * base_yield       # t/ha

    loan = P_N * N
    if insured:
        # index payout is yield-indexed only -- price crashes are NOT covered (basis risk)
        indemnity = np.maximum(THETA_FLOOR - theta_yield, 0) * base_yield * KG_PER_TONNE * calib.P_Y
        premium = INSURANCE_LOADING * calib.SHORTFALL_PER_UNIT * base_yield * KG_PER_TONNE * calib.P_Y
        loan = loan + premium
    else:
        indemnity = 0.0

    revenue = (calib.P_Y * theta_price) * yield_realized * KG_PER_TONNE + indemnity
    repayment_due = (1 + r) * loan
    profit = revenue - repayment_due
    default = (revenue < repayment_due).astype(float)
    return yield_realized, revenue, profit, default


def optimal_investment(r, insured, calib, abs_risk_aversion=None, n=N_MC,
                        theta_yield=None, theta_price=None):
    """Grid-search the farmer's mean-variance-optimal extra investment N*.

    Uses common random numbers (the same shock draws reused across every N on
    the grid, and optionally passed in so a whole sweep over r/gamma/etc. also
    shares them) so the objective is smooth -- without this, independently
    redrawing shocks makes the estimated objective jagged with Monte Carlo
    noise and the argmax picks noise instead of the true optimum. This is a
    standard variance-reduction trick and lets a modest N_MC give a stable
    optimum instead of needing a much larger one.
    """
    if abs_risk_aversion is None:
        abs_risk_aversion = calib.ABS_RISK_AVERSION
    if theta_yield is None:
        theta_yield = draw_theta_yield(n, calib)
    if theta_price is None:
        theta_price = draw_theta_price(n)
    best_N, best_obj = 0.0, -np.inf
    for N in N_GRID:
        _, _, profit, _ = simulate_arm(N, r, insured, calib, theta_yield=theta_yield, theta_price=theta_price)
        obj = profit.mean() - (abs_risk_aversion / 2) * profit.var()
        if obj > best_obj:
            best_obj, best_N = obj, N
    return best_N


ARMS = {
    "Control": dict(r=R_CONTROL, insured=False),
    "T1 (low-interest)": dict(r=R_LOW, insured=False),
    "T2 (insurance-backed)": dict(r=R_LOW, insured=True),
    "T3 (combined)": dict(r=R_LOW - INCENTIVE_RATE_CUT, insured=True),
}


def compute_all_arms(calib, n=N_MC):
    """Run all 4 arms for one calibration. Shared by h3_h4_arm_comparison
    (national default, with plots) and run_region_crop_comparison (all 8
    region-crop combinations, no per-combo plots -- see that function)."""
    results = {}
    for name, cfg in ARMS.items():
        N_star = optimal_investment(cfg["r"], cfg["insured"], calib, n=n)
        yld, revenue, profit, default = simulate_arm(N_star, cfg["r"], cfg["insured"], calib, n=n)
        # debt-service-to-revenue ratio: a graduated repayment-stress measure
        # (standard in the microfinance risk literature) that's informative
        # even when the strict default indicator (revenue < repayment due) is
        # ~0 -- see README for why strict default is near-zero in this model.
        burden = 1 - profit / revenue
        results[name] = dict(N_star=N_star, yield_mean=yld.mean(), profit_mean=profit.mean(),
                              profit_sd=profit.std(), default_rate=default.mean(),
                              burden_mean=burden.mean(), profit=profit)
    return results


# ---------------------------------------------------------------------------
# 3. Monte Carlo convergence check -- answers "how many draws do we need?"
#    empirically, using this model, instead of asserting a rule of thumb.
# ---------------------------------------------------------------------------
def convergence_check():
    print("=" * 72)
    print("MONTE CARLO CONVERGENCE CHECK  (T1 arm, N = 150 kg N-eq/ha, national maize)")
    print("Repeats each draw-count 30x to measure how much the mean-profit")
    print("estimate itself bounces around, i.e. the Monte Carlo error.")
    print("=" * 72)
    sizes = [100, 1_000, 5_000, 10_000, 50_000, 100_000]
    r, insured = ARMS["T1 (low-interest)"]["r"], False
    print(f"{'draws':>8} | {'mean profit (birr/ha)':>22} | {'MC std-error':>12} | {'SE as % of mean':>16}")
    for n in sizes:
        means = [simulate_arm(150.0, r, insured, NATIONAL_MAIZE, n=n)[2].mean() for _ in range(30)]
        m, se = np.mean(means), np.std(means, ddof=1)
        print(f"{n:>8} | {m:>22.1f} | {se:>12.2f} | {100*se/abs(m):>15.2f}%")
    print("-> error keeps shrinking roughly as 1/sqrt(draws); 10,000 draws")
    print("   gets the mean-profit estimate to well under 1% Monte Carlo")
    print("   error here, which is why it's used as the default below.")
    print()


# ---------------------------------------------------------------------------
# 4. H1: investment vs. interest rate (uninsured) -- national maize
# ---------------------------------------------------------------------------
def h1_investment_vs_rate(calib=None):
    if calib is None:
        calib = NATIONAL_MAIZE
    rates = np.linspace(0.0, 0.30, 16)
    # shared shocks across the whole sweep (common random numbers) so the
    # curve reflects the rate effect only, not draw-to-draw MC noise
    ty, tp = draw_theta_yield(N_MC, calib), draw_theta_price(N_MC)
    invest = [optimal_investment(r, insured=False, calib=calib, theta_yield=ty, theta_price=tp) for r in rates]
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(100 * rates, invest, marker="o")
    ax.set_xlabel("Interest rate (%)")
    ax.set_ylabel("Optimal extra investment N* (kg N-eq/ha)")
    ax.set_title("H1: Lower interest rates increase agricultural investment")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "H1_investment_vs_rate.png"), dpi=150)
    plt.close(fig)
    return rates, invest


# ---------------------------------------------------------------------------
# 5. H2: insurance vs. no insurance, at the same low rate -- national maize
# ---------------------------------------------------------------------------
def h2_insurance_effect(calib=None):
    if calib is None:
        calib = NATIONAL_MAIZE
    r = R_LOW
    N_unins = optimal_investment(r, insured=False, calib=calib)
    N_ins = optimal_investment(r, insured=True, calib=calib)
    _, _, pi_unins, _ = simulate_arm(N_unins, r, False, calib, n=N_MC)
    _, _, pi_ins, _ = simulate_arm(N_ins, r, True, calib, n=N_MC)
    # isolate the pure risk-reduction channel: insurance at the SAME investment
    # level as the uninsured optimum (before the farmer reinvests the saved risk)
    _, _, pi_ins_fixedN, _ = simulate_arm(N_unins, r, True, calib, n=N_MC)

    print(f"  Pure risk-reduction effect (both at N={N_unins:.0f}): "
          f"sd {pi_unins.std():.0f} -> {pi_ins_fixedN.std():.0f} birr/ha "
          f"({100*(1-pi_ins_fixedN.std()/pi_unins.std()):.1f}% lower)")
    print(f"  Farmer's response: reinvests that risk reduction into more input "
          f"(N* {N_unins:.0f} -> {N_ins:.0f}), which pushes variance back up "
          f"while raising mean profit -- net effect is a better risk-return "
          f"tradeoff, not necessarily a narrower distribution.")

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.hist(pi_unins, bins=60, alpha=0.55, label=f"No insurance (N*={N_unins:.0f}, sd={pi_unins.std():.0f})", density=True)
    ax.hist(pi_ins, bins=60, alpha=0.55, label=f"Insured, reinvested (N*={N_ins:.0f}, sd={pi_ins.std():.0f})", density=True)
    ax.set_xlabel("Profit (birr/ha)")
    ax.set_ylabel("Density")
    ax.set_title("H2: Insurance raises optimal investment,\nshifting profit upward (see console for the isolated variance effect)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "H2_insurance_effect.png"), dpi=150)
    plt.close(fig)
    return N_unins, N_ins, pi_unins, pi_ins


# ---------------------------------------------------------------------------
# 6. H3 & H4: full 4-arm comparison (default rates, profit distributions)
#    -- national maize
# ---------------------------------------------------------------------------
def h3_h4_arm_comparison(calib=None):
    if calib is None:
        calib = NATIONAL_MAIZE
    results = compute_all_arms(calib)

    # H3: default rate AND repayment burden by arm
    names = list(results.keys())
    x = np.arange(len(names))
    width = 0.35
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(x - width/2, [100 * results[n]["default_rate"] for n in names], width,
           label="Strict default rate (revenue < repayment due)", color="#c44e52")
    ax.bar(x + width/2, [100 * results[n]["burden_mean"] for n in names], width,
           label="Mean repayment burden (debt service / revenue)", color="#4c72b0")
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylabel("%")
    ax.set_title("H3: Incentive-linked repayment and default/repayment-burden risk")
    ax.legend(fontsize=7)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "H3_default_rate_by_arm.png"), dpi=150)
    plt.close(fig)

    # H4: profit distribution, Control vs Combined
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.hist(results["Control"]["profit"], bins=60, alpha=0.55, density=True,
            label=f"Control (mean={results['Control']['profit_mean']:.0f})")
    ax.hist(results["T3 (combined)"]["profit"], bins=60, alpha=0.55, density=True,
            label=f"T3 combined (mean={results['T3 (combined)']['profit_mean']:.0f})")
    ax.set_xlabel("Profit (birr/ha)")
    ax.set_ylabel("Density")
    ax.set_title("H4: Combined model shifts the profit distribution\nabove standard microcredit")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "H4_profit_control_vs_combined.png"), dpi=150)
    plt.close(fig)

    return results


def write_summary_csv(results):
    path = os.path.join(OUTDIR, "arm_summary.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["arm", "r", "insured", "N_star_kgNeq_ha", "mean_yield_t_ha",
                    "mean_profit_birr_ha", "sd_profit_birr_ha", "default_rate_pct",
                    "mean_repayment_burden_pct"])
        for name, cfg in ARMS.items():
            r = results[name]
            w.writerow([name, cfg["r"], cfg["insured"], round(r["N_star"], 1),
                        round(r["yield_mean"], 2), round(r["profit_mean"], 1),
                        round(r["profit_sd"], 1), round(100 * r["default_rate"], 2),
                        round(100 * r["burden_mean"], 2)])
    return path


# ---------------------------------------------------------------------------
# 7. Region/crop comparison -- 4 regions x 2 crops (maize, sorghum), 8
#    combinations total. Each output maps to one of H1-H4, testing whether
#    that hypothesis holds across agro-climatic contexts rather than just in
#    the single national-maize aggregate above. See Simulation/README.md and
#    Simulation/SYNTHETIC_DATA.md.
# ---------------------------------------------------------------------------
def run_region_crop_comparison(calibrations=None):
    if calibrations is None:
        calibrations = build_region_crop_calibrations()

    all_results = {}
    rows = []
    for calib in calibrations:
        results = compute_all_arms(calib)
        all_results[(calib.region, calib.crop)] = results
        for name, cfg in ARMS.items():
            r = results[name]
            rows.append([calib.region, calib.crop, name, cfg["r"], cfg["insured"],
                         round(r["N_star"], 1), round(r["yield_mean"], 2),
                         round(r["profit_mean"], 1), round(r["profit_sd"], 1),
                         round(100 * r["default_rate"], 2), round(100 * r["burden_mean"], 2)])

    csv_path = os.path.join(OUTDIR, "regional_arm_summary.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["region", "crop", "arm", "r", "insured", "N_star_kgNeq_ha", "mean_yield_t_ha",
                    "mean_profit_birr_ha", "sd_profit_birr_ha", "default_rate_pct",
                    "mean_repayment_burden_pct"])
        w.writerows(rows)

    labels = [f"{c.region}\n{c.crop}" for c in calibrations]
    x = np.arange(len(calibrations))
    width = 0.35

    # Regional H1: investment vs. rate, one line per combo -- does the
    # negative-slope finding (lower rate -> more investment) hold everywhere?
    rates = np.linspace(0.0, 0.30, 16)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for calib in calibrations:
        ty, tp = draw_theta_yield(N_MC, calib), draw_theta_price(N_MC)
        invest = [optimal_investment(r, insured=False, calib=calib, theta_yield=ty, theta_price=tp) for r in rates]
        ax.plot(100 * rates, invest, marker="o", markersize=3, label=f"{calib.region} - {calib.crop}")
    ax.set_xlabel("Interest rate (%)")
    ax.set_ylabel("Optimal extra investment N* (kg N-eq/ha)")
    ax.set_title("H1 across region-crop contexts:\nlower rates increase investment everywhere?")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "Regional_H1_investment_vs_rate.png"), dpi=150)
    plt.close(fig)

    # Regional H2: N* with vs. without insurance, grouped bar per combo
    N_unins_list = [all_results[(c.region, c.crop)]["T1 (low-interest)"]["N_star"] for c in calibrations]
    N_ins_list = [all_results[(c.region, c.crop)]["T2 (insurance-backed)"]["N_star"] for c in calibrations]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.bar(x - width/2, N_unins_list, width, label="T1: low-interest, no insurance")
    ax.bar(x + width/2, N_ins_list, width, label="T2: low-interest + insurance")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylabel("Optimal extra investment N* (kg N-eq/ha)")
    ax.set_title("H2 across region-crop contexts:\ndoes insurance increase investment everywhere?")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "Regional_H2_insurance_effect.png"), dpi=150)
    plt.close(fig)

    # Regional H3: Control vs. T3 repayment burden, grouped bar per combo
    control_burden = [100 * all_results[(c.region, c.crop)]["Control"]["burden_mean"] for c in calibrations]
    t3_burden = [100 * all_results[(c.region, c.crop)]["T3 (combined)"]["burden_mean"] for c in calibrations]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.bar(x - width/2, control_burden, width, label="Control", color="#c44e52")
    ax.bar(x + width/2, t3_burden, width, label="T3 (combined)", color="#4c72b0")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylabel("Mean repayment burden (%)")
    ax.set_title("H3 across region-crop contexts:\nare insured arms' burdens still higher everywhere?")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "Regional_H3_repayment_burden.png"), dpi=150)
    plt.close(fig)

    # Regional H4: mean profit uplift, T3 - Control, one bar per combo
    uplift = [all_results[(c.region, c.crop)]["T3 (combined)"]["profit_mean"]
              - all_results[(c.region, c.crop)]["Control"]["profit_mean"] for c in calibrations]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    colors = ["#55a868" if u > 0 else "#c44e52" for u in uplift]
    ax.bar(x, uplift, color=colors)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylabel("Mean profit uplift, T3 - Control (birr/ha)")
    ax.set_title("H4 across region-crop contexts:\ndoes the combined model raise profit everywhere?")
    ax.axhline(0, color="black", linewidth=0.8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "Regional_H4_profit_uplift.png"), dpi=150)
    plt.close(fig)

    return csv_path, all_results


if __name__ == "__main__":
    print(f"Fitted saturating yield-response curve (national maize): N0={NATIONAL_MAIZE.N0_FIT:.1f}, k={NATIONAL_MAIZE.K_FIT:.2f}\n")

    convergence_check()

    print("Running H1 (investment vs. rate)...")
    h1_investment_vs_rate()

    print("Running H2 (insurance effect)...")
    N_unins, N_ins, pi_unins, pi_ins = h2_insurance_effect()
    print(f"  No insurance: N*={N_unins:.0f} kg N-eq/ha, profit sd={pi_unins.std():.0f} birr/ha")
    print(f"  Insured:      N*={N_ins:.0f} kg N-eq/ha, profit sd={pi_ins.std():.0f} birr/ha\n")

    print("Running H3/H4 (4-arm comparison, national maize)...")
    results = h3_h4_arm_comparison()
    csv_path = write_summary_csv(results)

    print(f"\n{'arm':<24}{'r':>7}{'N* (kgN/ha)':>14}{'yield (t/ha)':>14}{'profit (birr/ha)':>18}{'default %':>12}{'burden %':>11}")
    for name in ARMS:
        r = results[name]
        print(f"{name:<24}{ARMS[name]['r']*100:>6.1f}%{r['N_star']:>14.0f}{r['yield_mean']:>14.2f}"
              f"{r['profit_mean']:>18.0f}{100*r['default_rate']:>11.1f}%{100*r['burden_mean']:>10.1f}%")

    print(f"\nSaved: H1_investment_vs_rate.png, H2_insurance_effect.png,")
    print(f"       H3_default_rate_by_arm.png, H4_profit_control_vs_combined.png,")
    print(f"       {os.path.basename(csv_path)}")

    print("\nRunning region-crop comparison (4 regions x 2 crops = 8 combinations)...")
    regional_csv_path, all_regional_results = run_region_crop_comparison()
    print(f"\n{'region':<14}{'crop':<10}{'arm':<24}{'N* (kgN/ha)':>14}{'profit (birr/ha)':>18}{'burden %':>11}")
    for (region, crop), res in all_regional_results.items():
        for name in ARMS:
            r = res[name]
            print(f"{region:<14}{crop:<10}{name:<24}{r['N_star']:>14.0f}"
                  f"{r['profit_mean']:>18.0f}{100*r['burden_mean']:>10.1f}%")
    print(f"\nSaved: {os.path.basename(regional_csv_path)}, Regional_H1_investment_vs_rate.png,")
    print(f"       Regional_H2_insurance_effect.png, Regional_H3_repayment_burden.png,")
    print(f"       Regional_H4_profit_uplift.png")
    print(f"\nAll outputs in: {OUTDIR}")
