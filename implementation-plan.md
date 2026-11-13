# Portfolio implementation and editorial plan

**Status: proposed, pending user review.** This is a planning artifact, not an
approved schedule, a record of past effort, or a claim that analyses or posts
exist. The companion [ledger](weekly-editorial-ledger.json) assigns every
Wednesday from 2023-06-14 through 2027-06-09 to a single project; it also
identifies weeks for which no distinct milestone or historical evidence is
available. The [evidence inventory](data-source-evidence-inventory.md) records
what was actually inspected.

## Editorial contract

The proposed coverage periods are groceries (June 2023–May 2024), electricity
(June 2024–September 2025), fantasy football (October 2025–January 2026), and
learning analytics (February 2026–June 2027). Coverage slots are editorial
labels, **not** execution or publication dates. The final portfolio summary is
separate, proposed for June 2027, and has no invented publication date.

For each eventual post distinguish:

1. **Verified historical work:** quote or link a dated, attributable source
   and its exact revision; a saved notebook output alone does not establish
   when it was produced. Do not infer activity from a coverage date.
2. **New retrospective analysis:** record its actual execution date and code
   revision, observation period, source vintage and cutoff, and inputs. It may
   use later-created artifacts only when explicitly identified as retrospective.
3. **Future plan:** leave results, execution and publication dates unset, and
   keep the post excluded from the site. No fictional weekly releases, results,
   hours, commits, or first-person experiences.

Every assigned milestone budgets at most 120 minutes **including writing**.
The ledger allocates 60 minutes to analysis, 25 to validation and 35 to writing;
these are estimates, not time logs. An unassigned slot has a zero allocation
and is not a request to create a filler post. Larger tasks should be reduced to
one question and deferred rather than silently exceeding the budget. Do not
create the hundreds of posts implied by the calendar: draft or publish only a
reviewed, evidence-supported milestone.

## First eight grocery milestones

All eight use the same three workbooks' June 13, 2023 ALFRED vintage and
January 2018–May 2023 observations; the files themselves were created in
November 2026. They are **proposals for retrospective execution**, not claims
that these files or analyses existed on the coverage dates. Verify exact
release timing when making a contemporaneous claim. Use source terms, units and
definitions; the workbook cautions that these average prices are not the
preferred measure of price change over time.

| Coverage | Question and bounded task | Evidence and focused check |
|---|---|---|
| 2023-06-14 | What do the files represent? Inventory series IDs, units, vintage and file creation metadata; write source notes. | Metadata table; compare all three sheets and distinguish vintage from file creation. |
| 2023-06-21 | Are the monthly observations usable? Parse copies read-only; check dates, duplicates, missing values and units separately. | Small completeness table; test 65 dates per file and report any discrepancy, not an assumed clean result. |
| 2023-06-28 | How did the recorded bread average price move within this vintage? Make a clearly labeled monthly level plot. | Bread plot and source note; verify dates and dollar-per-pound unit. |
| 2023-07-05 | What pattern appears in egg average price levels? Make the comparable labeled egg plot. | Egg plot; validate its dozen-unit and date range. |
| 2023-07-12 | What pattern appears in milk average price levels? Make the comparable labeled milk plot. | Milk plot; validate its gallon-unit and date range. |
| 2023-07-19 | How can the three different units be displayed without implying direct price comparability? Combine the three level plots as separate panels. | Faceted plot with explicit axes and units; check no common raw-price ranking is implied. |
| 2023-07-26 | Which dates have the largest within-series month-to-month level differences? Compute and inspect differences, explicitly descriptive, not a CPI inflation measure. | Small per-series table; verify missing values, first-month handling and units. |
| 2023-08-02 | How sensitive is a relative-level view to its chosen base? Compare one clearly stated nonzero base across the three series as descriptive context. | Base-normalized plot; check arithmetic and disclose that average-price series are not CPI price-change indices. |

Subsequent assigned milestones in the ledger are deliberately higher-level.
Electricity milestones use the static 2006–2010 single-household archive, not
contemporary electricity prices. Fantasy milestones separate input weeks from
outcome weeks and exclude the original Week 8 matchup analysis. OULAD work
uses only available non-clickstream tables, explicitly limits inference to the
observed cohort, and avoids outcome leakage in any prediction exercise.

## Small implementation path, after approval

1. Create a minimal Quarto website: `_quarto.yml`, `index.qmd`, a `posts/`
   listing, and a single GitHub Actions workflow using the official Quarto
   setup action to render and deploy GitHub Pages. Choose the supported Pages
   deployment source after checking repository permissions. Pin action
   revisions and declare the Quarto version. Do not introduce a framework,
   analytics service, dependency manager, or custom theme without need.
2. Keep unpublished work outside the render tree (for example `drafts/`,
   excluded explicitly in `_quarto.yml`), rather than relying on dates or
   front-matter alone. Render only curated, approved posts. Keep sources and
   raw data in their original repositories unmodified; store separately
   documented corrections and small reproducible analysis scripts alongside
   derived outputs in the relevant project when implementation is authorized.
3. For each executed analysis export a figure as an accessible SVG (plus PNG
   when a renderer requires it), a UTF-8 CSV of **aggregate** results with
   named columns and units, and a UTF-8 JSON metadata sidecar with `project`,
   `question`, `observation_start`, `observation_end`, `source_vintage`,
   `historical_cutoff`, `source_urls`, `input_revision`, `input_hashes`,
   `analysis_revision`, `execution_date`, `publication_date`, `method`,
   `limitations`, and `outputs`. Unknown dates and revisions are JSON null,
   never guessed. Record code revision and data revision separately; use ISO
   dates and specify timezone for actual timestamps.
4. Validate narrow invariants first: source schema and expected dates, one
   controlled aggregation or formula with a fixture, missing-value handling,
   join cardinality and cutoff checks, and render/link checks for approved
   output. Do not turn planning estimates into reported execution time.
5. Keep learner-level OULAD and course-platform records, IDs, model predictions,
   and raw notebook outputs out of the website, render tree and deployment
   artifacts. Export aggregates only after disclosure review: suppress counts
   below 10 and complementary cells where needed to prevent subtraction;
   suppress percentages or plots from suppressed cells. Avoid high-cardinality
   intersections and never expose individual IDs. Review whether the threshold
   is sufficient before release.

## Decisions needed before implementation

- Approve or revise the proposed coverage sequence, milestone selection, and
  handling of unassigned weeks; decide which, if any, become actual posts.
- Confirm publication venue/Pages permissions and whether retrospective posts
  should display coverage date alongside actual publication date.
- Approve the disclosure policy and allowed level of aggregation for learning
  data; resolve source rights/collection-method uncertainty before making
  platform-comparison claims. For fantasy, confirm season and input provenance
  before using any matchup analysis; do not reconstruct missing split inputs.

No pull request or site implementation is part of this stage.
