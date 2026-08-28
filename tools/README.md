# tools

```bash
bash tools/build.sh          # rebuild the pages
bash tools/build.sh --all    # also recompute from the NSDUH files
```

## The two halves

**[raw]** stages need the three NSDUH public-use files in `../source/`, about 1.1 GB. They
are not committed: too large, publicly distributed by SAMHSA, and individual-level. What
those stages produce lands in `derived/` as aggregates, and `derived/` **is** committed, so
the pages rebuild on any checkout without the data.

| Stage | Reads | Writes |
|---|---|---|
| `compute_analysis.py` **[raw]** | NSDUH files | `derived/analysis.json`, `derived/sim_params.json` |
| `make_figures.py` **[raw]** | derived | `derived/f1..f5.svg` |
| `make_notebook.py` | `derived/sim_params.json` | `notebooks/*.ipynb` |
| `build_pages.py` | derived, templates | `public/*.html` |

## Things that will bite you

**Read only the columns you need.** Each file has about 2,650. `load_pooled()` passes a
`usecols` predicate; reading everything is slow and memory hungry for no benefit.

**Pooling years divides the weight by the number of years.** Without that the weighted totals
describe a population three times too large. `load_pooled()` does it; do not remove it.

**The design variables are not optional.** `ANALWT2_C`, `VESTR_C` and `VEREP` are what make
an estimate a statement about the country rather than about the respondents. Every
descriptive figure on the site is computed both ways deliberately.

**Dropping missing MDE removes every 12-17 year old**, because they are asked a different
instrument. That is a population restriction, not missingness. The analysis is of adults.

**Seeds are fixed at 1.** Changing them relabels clusters and moves the last digits of the
cross-validated figures, several of which are published.

**Never write respondent-level anything into `derived/`.** It is committed. Aggregates only;
`sim_params.json` holds marginals and coefficients, and must stay that way.

**The notebook's synthetic data has no correlation structure**, so its PCA step is
degenerate by construction. The notebook says so. Do not "fix" it by tuning the generator
until the PCA looks good; that would fake structure the aggregates do not contain.
