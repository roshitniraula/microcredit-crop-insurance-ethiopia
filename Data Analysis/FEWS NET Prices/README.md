# FEWS NET Data Warehouse — Ethiopia maize/sorghum prices

Source: FEWS NET Data Warehouse (`fdw.fews.net`), Markets & Trade → Prices,
pulled on 2026-07-19 via the public API
(`https://fdw.fews.net/api/marketpricefacts/?format=csv&fields=simple`,
filtered by `country=ET` and `product=`; no account required). Rows carry
`data_usage_policy=Public`.

Each file is the full, unfiltered country-level series for one product:
every market, source organization and price type. The dataset has only
Retail and Wholesale prices for these crops, with no Farmgate/Producer type.

| File | Rows | Product |
|---|---|---|
| `Ethiopia_Maize_Grain_White_AllMarkets.csv` | 9,254 | Maize Grain (White) |
| `Ethiopia_Sorghum_White_AllMarkets.csv` | 3,151 | Sorghum (White) |
| `Ethiopia_Sorghum_Yellow_AllMarkets.csv` | 4,497 | Sorghum (Yellow) |

Each row is one market / product / price type / source / date observation.
Prices are already normalized to birr/kg in the `common_unit_price` column.

## Use in the model: `P_Y_MAIZE`, `P_Y_SORGHUM`

| | Maize | Sorghum White | Sorghum Yellow |
|---|---|---|---|
| Retail, Addis Ababa Merkato, May 2026 (birr/kg) | 70.75 | 89.34 | 106.00 |
| Wholesale/retail ratio (all market-months with both types) | 0.873 (520) | 0.866 (31) | not used |

- Maize: 70.75 × 0.873 ≈ **62 birr/kg**.
- Sorghum: the average of White and Yellow (97.67) × 0.866 ≈ **85 birr/kg**.

Full derivation and limitations: `../External_Parameters_Sourced.md` §2.

## Use as a cross-check: `CV_PRICE`

Annualized log-return volatility, converted to a CV. Monthly log-returns are
annualized with `1/sqrt(gap_in_years)`.

| Series | CV |
|---|---|
| Maize, Addis Ababa Ehile berenda wholesale (ETBC, 2004-2024) | 0.35 |
| Sorghum White, same series | 0.23 |
| Sorghum Yellow, same series | 0.26 |
| Maize, Addis Ababa Merkato retail (FEWS NET, 2019-2026) | 0.21 |
| Sorghum White, same series | 0.18 |
| Sorghum Yellow, same series | 0.44 (thinner market) |

Five of the six fall in 0.18-0.35, bracketing the FAOSTAT-derived value of
0.27 used in the model.

## Not used

The data includes market-level series for Jimma, Bahir Dar and Dessie, and
for Hawassa via Shashemene / Awassa zuriya. Region-specific prices are
therefore possible, but the model uses one national price per crop.
