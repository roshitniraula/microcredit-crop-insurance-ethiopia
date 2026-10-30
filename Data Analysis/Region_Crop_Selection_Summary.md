# Why these regions, and why these crops

## Crop set

The study uses **maize and sorghum in all four regions**:

| Region | Crops in the study |
|---|---|
| **Jimma** | Maize, Sorghum |
| **Bahir Dar** | Maize, Sorghum |
| **Dessie** | Maize, Sorghum |
| **Hawassa** | Maize, Sorghum |

Using the same two crops everywhere means that differences across regions
reflect climate and yield-gap differences, not a different crop mix.

Wheat was considered and dropped because GYGA has no wheat entries at all
for the Jimma or Bahir Dar climate zones; including it would have produced
an uneven design. Common bean was dropped because no price data was found.

`Region_Crop_Calibration.xlsx` lists every crop present in each matched
climate zone. Only the maize and sorghum rows are used by the simulation.

## Why these four regions

Each region represents a distinct agro-economic profile:

- **Jimma** (Jimma Zone, Oromia): wet agricultural benchmark
- **Bahir Dar** (West Gojjam Zone, Amhara): highland farming comparison
- **Dessie** (South Wollo Zone, Amhara): climate vulnerability
- **Hawassa** (Sidama region): commercial / agricultural growth

Dessie and Hawassa are deliberately the harder, more marginal cases.

## How crops were matched to each region

GYGA (`GYGA/GygaEthiopia.xlsx`) reports station-level data only where a
trial station exists. Neither Dessie nor Hawassa has one. The nearest
stations are Kombolacha (~10 km from Dessie), which has only sorghum trials,
and Arsi-Negele (~39 km from Hawassa), which has only common bean. That
would badly understate what is grown in those areas.

Each region is therefore matched to its GYGA **climate zone**: 6801 Jimma,
6601 Bahir Dar, 6501 Dessie, 6301 Hawassa. Each zone is the ~30-50 km-radius
aggregate that a station belongs to. The crop mix at that level lines up
with independent literature:

- **Jimma (6801)**: maize is dominant (255,947 ha in-zone vs. 115,768 ha
  sorghum, 27,466 ha millet, 20,563 ha common bean). This matches the Jimma
  Zone physical and socio-economic profile, where maize is the largest
  cereal by area (173,286 ha), and recent Jimma-area irrigation-modeling
  work that describes maize as the dominant crop.
- **Bahir Dar (6601)**: maize is dominant (106,601 ha vs. 40,892 ha sorghum),
  consistent with West Gojjam literature and a maize-productivity survey for
  Bahir Dar Zuriya district.
- **Dessie (6501)**: there is no single dominant crop.
  - In GYGA, wheat (196,280 ha) and maize (185,051 ha) lead, with sorghum
    (133,786 ha) close behind, and chickpea and common bean are also present.
  - This matches a Wageningen University & Research thesis on farm-household
    production efficiency in Dessie Zuria, which describes a mixed
    crop-livestock system.
  - It also matches a 2025 South Wollo ethnobotanical survey (Melese &
    Asfaw, PMC12023553), which reports wheat (53%), chickpea (49%) and
    sorghum (43%) among the most commonly cultivated crops by household
    prevalence.
- **Hawassa (6301)**: maize (110,514 ha) and wheat (97,390 ha) lead, with
  sorghum (71,059 ha), common bean and chickpea also present.
  - A 2025 *Discover Food* study of maize commercialization in northern
    Sidama supports maize as a primary crop
    (https://doi.org/10.1007/s44187-025-00709-8).

The `LOCAL_EVIDENCE_NOTE` column of `Region_Crop_Calibration.xlsx` records
which crops have local confirmation beyond the GYGA aggregate.

## Data limitations

1. **Teff is absent from GYGA.** Local survey evidence suggests teff may be
   among the most commonly grown crops around Dessie, but no yield-gap data
   exists for it, so it cannot be simulated with this method.
2. **There is no farmgate producer price for either crop.** The model uses
   wholesale-equivalent prices derived from FEWS NET retail data (see
   `External_Parameters_Sourced.md` §2), which likely sit above what farmers
   receive.
3. **One national price and one interest rate are used in all four
   regions.** Regional variation comes only from the GYGA yield data.
4. **Climate-zone matching is approximate.** Each city is represented by the
   GYGA climate zone containing or nearest to it, not by a station at the
   city itself.
