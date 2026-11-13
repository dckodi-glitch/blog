# Data-source and evidence inventory

**Audit date: 2026-11-13.** Proposed plan, pending user review. Sources were
read via GitHub API and pinned file downloads; workbooks were inspected as
Open XML ZIPs, the electricity ZIP was streamed with Python's standard
library, CSVs were parsed read-only, and notebook JSON was read without
executing any notebook cells or source-repository code. No repository was
checked out or modified. A repository commit timestamp is evidence of that
commit, not proof of when the underlying work was performed.

## Repository snapshots

| Repository | Inspected HEAD commit | HEAD commit time (UTC) | Earliest available commit (UTC) | Current contents |
|---|---|---|---|---|
| [blog](https://github.com/dckodi-glitch/blog) | `9aa2db605a58a930d2e959322e8a9125beaf4e54` | 2026-11-13 21:37:27 | 2026-11-13 21:37:27 | README only at audit; this plan is new workspace content. |
| [grocery-changes](https://github.com/dckodi-glitch/grocery-changes) | `be45c4a1946bbda7739a889b8fcb3f90d0c098fe` | 2026-11-13 22:38:22 | 2026-11-13 21:35:51 | README and bread, eggs, milk XLSX; no notebook at HEAD. |
| [electricity-changes](https://github.com/dckodi-glitch/electricity-changes) | `929ed43064487e09fe69af58f5c43d5971fa14a4` | 2026-11-13 22:18:04 | 2026-11-13 21:36:39 | README and one archive; no notebook at HEAD. |
| [fantasy-changes](https://github.com/dckodi-glitch/fantasy-changes) | `1c0f7b29ff332313cc4d27eb28d1ac635fa31e9f` | 2026-11-13 21:53:49 | 2025-12-30 00:27:41 | Notebook, matchup inputs, results, 2024 weekly player statistics, README. |
| [online-changes](https://github.com/dckodi-glitch/online-changes) | `a51ba30520859201319ec9efc40142153fb68fc2` | 2026-11-13 22:42:03 | 2025-12-30 00:37:16 | Notebook, platform CSV, README and `diff_data/` OULAD tables. |

Earliest timestamps shown are UTC, so the fantasy and online initial commits
fell on December 29 in the US Pacific time zone. They establish neither a
starting date for the underlying analysis nor weekly activity. HEAD blob IDs
below allow later verification independent of mutable branch names.

## Groceries: source and vintage

Each XLSX contains a `README` metadata sheet and `Vintages Starting 2023-06-13`
data sheet. All have 65 monthly observations, January 2018–May 2023; vintage
is **2023-06-13**, not a 2026 work date. The workbook core creation timestamps
are 2026-11-13 22:32:56Z, 22:35:18Z and 22:36:23Z respectively. First proposed
analysis coverage is 2023-06-14. Files at the current repository snapshot
cannot establish that analyses occurred in 2023.

| Workbook | ALFRED series | Git blob SHA | Unit/subject |
|---|---|---|---|
| `bread.xlsx` | [APU0000702111](https://alfred.stlouisfed.org/series?seid=APU0000702111) | `f12b3b3fccf7a93c13337951970776e58c95626b` | White bread, per pound |
| `eggs.xlsx` | [APU0000708111](https://alfred.stlouisfed.org/series?seid=APU0000708111) | `da7a65787a22153fd37411a02a483544672c4efe` | Grade A large eggs, per dozen |
| `milk.xlsx` | [APU0000709112](https://alfred.stlouisfed.org/series?seid=APU0000709112) | `39a9993dd58f1440e929ecb7e6a42bd7fa9b113c` | Fresh whole milk, per gallon |

Source notes state that average prices are best used for price levels, not
price changes; use CPI indices to measure price change. Check
[FRED terms](https://fred.stlouisfed.org/legal#fred-terms-faq) before reuse.
The specific public release timing of each value is not independently
established by an observation month; the vintage is the knowledge snapshot.

## Electricity: archive structure

`individual+household+electric+power+consumption.zip`, blob
`ae8864521e68b784443e4e9f55c7505812ee6c36`, is 20,640,916 bytes and has
one member, `household_power_consumption.txt` (132,960,755 uncompressed
bytes). Its semicolon-delimited header is `Date;Time;Global_active_power;
Global_reactive_power;Voltage;Global_intensity;Sub_metering_1;Sub_metering_2;
Sub_metering_3` (shown wrapped here only). It has 2,075,259 data rows, first
timestamp 2006-12-16 17:24:00 and last 2010-11-26 21:02:00.

[UCI source](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption)
describes one household in Sceaux, France, minute sampling, missing measurements
and donation on 2012-08-29. It is not representative national or current
electricity data and contains no prices. Unit conversions, time convention,
missing markers and partial days require explicit validation. UCI identifies
the dataset as CC BY 4.0; cite the source.

## Fantasy: week mapping and exclusions

The README says input filenames name the number of weeks already observed.
Saved notebook sections cover projections and comparisons for Weeks 7–10,
projections for Weeks 11 and 13, and a reusable blueprint. Saved outputs
indicate notebook content, not a verified execution date or reliable results.
Original notebooks and CSVs remain untouched. Input season/source provenance
and release timing should be confirmed before a dated claim.

| Prior-week input pair | Result file and `WK` | Treatment |
|---|---|---|
| `WR6.csv`, `Defense6.csv` | `WR6Results.csv`: 7 | Candidate Week 7 comparison, subject to input/provenance validation. |
| `WR7.csv`, `Defense7.csv` | `WR7Results.csv`: 8 | **Exclude original 2025 Week 8 matchup analysis:** Defense7 and Defense6 both have Git blob `b066fef0b5d017ae3686d5f5447bae0a83229f46`. Do not repair by inventing slot/wide splits. |
| `WR8.csv`, `Defense8.csv` | `WR8Results.csv`: 9 | Candidate Week 9 comparison. |
| `WR9.csv`, `Defense9.csv` | `WR9Results.csv`: 10 | Candidate Week 10 comparison. |
| `WR10.csv`, `Defense10.csv` | `WR10Results.csv`: 11 | Result rows exist; notebook has a Week 11 projection section, not a verified completed comparison. |
| `WR12.csv`, `Defense12.csv` | No `WR12Results.csv` | Intended Week 13 projection has no corresponding result file. Missing Week 12 split inputs are not to be reconstructed. |

Results tables have duplicate column names such as `YDS` and `TD`: resolve them
explicitly when parsing; do not silently overwrite fields. Results counts are
100, 100, 100, 99 and 100 respectively. `stats_player_week_2024.csv` is a
separate 2024 source and cannot substitute for unavailable 2025 slot/wide
splits. Validate player joins, exclusions and matching before analysis.

## Learning data and notebook evidence

The OULAD source is [UCI dataset 349](https://archive.ics.uci.edu/dataset/349/open+university+learning+analytics+dataset),
donated 2015-12-20, CC BY 4.0. Local `diff_data/` tables, parsed at the
snapshot above, are:

| File | Data rows | Key use |
|---|---:|---|
| `courses.csv` | 22 | Module/presentation context; presentations 2013B, 2013J, 2014B, 2014J. |
| `assessments.csv` | 206 | Assessment definitions and due-day metadata. |
| `studentInfo.csv` | 32,593 | Module-presentation registrations and final outcome; learner-level. |
| `studentRegistration.csv` | 32,593 | Registration/unregistration offsets; learner-level. |
| `studentAssessment.csv` | 173,912 | Assessment submissions and scores; learner-level. |
| `vle.csv` | 6,364 | Activity resource metadata, **not** learner interactions. |
| `OULAD.names` | not a CSV | Source schema and documentation; lists 32,953 students/registrations, which conflicts with the parsed local count. Use observed local counts and investigate rather than silently reconciling. |

Do not use, download, or require `studentVle.csv`; neither clickstream nor
engagement measures can be inferred from `vle.csv`. Record a valid observation
window and cutoff, distinguish course-relative dates from calendar dates, and
prevent final outcomes and post-cutoff assessments leaking into predictions.
Do not publish individual records.

The existing `learningWebsites.ipynb` contains one code cell with saved outputs
and reads `online_learning_course_consumption_dataset.csv`; saved output shows
500 rows and platform-oriented analysis. This does not establish execution
date, representativeness, or platform superiority. The
[Kaggle dataset](https://www.kaggle.com/datasets/prince7489/online-learning-and-course-consumption-dataset)
page identifies version 1 and modification on 2025-12-13; collection
methodology and exact identity with the local CSV were not independently
verified in this audit. Its linked
[notebook](https://www.kaggle.com/code/devraai/online-learning-course-completion-analysis)
was published 2025-12-26. These dates are source context, not evidence that
the local notebook was executed then. The local CSV contains learner-level
records and must not enter the published website.

## Outstanding provenance

Verify fantasy season, original split-source definitions and input release
dates; confirm course-platform dataset identity and collection methodology;
and check exact source licensing and privacy policy before publication.
Unassigned ledger slots are missing evidence, not implicit completed work.
