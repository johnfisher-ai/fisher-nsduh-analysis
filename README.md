# Depression and Substance Use in the United States

An analysis of the **National Survey on Drug Use and Health (NSDUH)**, 2022 to 2024. Three
survey years pooled to 134,897 adults, examining who reports a past-year major depressive
episode, which substances travel with it, and what the survey's own design changes about the
answer. By **John Fisher**.

🌐 **Live site:** <https://johnfisher-ai.github.io/fisher-nsduh-analysis/>

---

## The analysis

NSDUH is a stratified multistage probability sample run annually by the U.S. government.
Some groups are deliberately over-sampled, so every respondent carries a weight saying how
many people they represent, alongside stratum and replicate identifiers describing how the
sample was drawn.

Seven measures are used: past-month alcohol, marijuana and cigarette use, sex, age band,
household income, and self-rated health. The outcome is past-year major depressive episode.
The pipeline reduces the measures by PCA, groups respondents with k-means, then predicts the
outcome with penalized logistic regression and a classification tree.

**Three findings shape the site:**

- **The survey design moves the estimates.** Unweighted, 11.29% of respondents report a
  past-year depressive episode. Weighted to the population, 8.44%. The unweighted figure
  overstates it by about a third, because the survey over-samples young adults and young
  adults report depression at much higher rates. Every descriptive figure here is computed
  both ways.
- **Ignoring the design also understates precision.** The same logistic regression fitted
  with the design gives standard errors 1.74 to 1.96 times larger. Intervals computed
  without it are roughly half the width they should be.
- **Accuracy hides a model that predicts nothing.** The classifier reaches AUC 0.741, real
  signal. At the default 0.50 cut-off it is 88.7% accurate while flagging only 805 people
  out of 134,897, with kappa near zero. It achieves that accuracy by answering "no" to
  almost everyone.

A fourth point worth stating: dropping records with a missing outcome removes **every
respondent aged 12 to 17**, because adolescents are asked a different instrument. That is a
restriction on the population, not missing data. Everything here describes adults 18 and
over.

---

## What is in this repository

| File | What it is |
|---|---|
| [R/nsduh_mde_analysis.R](R/nsduh_mde_analysis.R) | The analysis pipeline in R: pooling, recoding, PCA, k-means, penalized regression, a tree, and the survey-design section. |
| [notebooks/nsduh_mde_analysis.ipynb](notebooks/nsduh_mde_analysis.ipynb) | The same analysis in Python, runnable in Colab on synthetic data. |
| [tools/](tools/) | The rebuild pipeline: analysis, figures, notebook and page builders. |

---

## Live site

| Page | What it holds | Status |
|---|---|---|
| **[Overview](https://johnfisher-ai.github.io/fisher-nsduh-analysis/)** | The survey, what the design changes, and the headline results. | ✅ Live |
| **[The analysis](https://johnfisher-ai.github.io/fisher-nsduh-analysis/analysis.html)** | Sample construction, weighted against unweighted throughout, PCA and clustering with a stability check, the classifier and the threshold trade-off, and the design effect on standard errors. | ✅ Live |
| **[The code](https://johnfisher-ai.github.io/fisher-nsduh-analysis/code.html)** | The R pipeline, syntax highlighted, with the Colab notebook and an R-to-Python mapping. | ✅ Live |
| **[The write-up](https://johnfisher-ai.github.io/fisher-nsduh-analysis/writeup.html)** | A plain-language walkthrough for readers without a statistics background. | ✅ Live |

The site is built by [`.github/workflows/pages.yml`](.github/workflows/pages.yml), which
publishes the `public/` folder and nothing else.

---

## Project structure

```
.
├── public/                             # The live site. This folder, and only this folder,
│   ├── index.html                      #   is published to GitHub Pages.
│   ├── analysis.html
│   ├── code.html
│   ├── writeup.html
│   └── assets/
├── R/
│   └── nsduh_mde_analysis.R
├── notebooks/
│   └── nsduh_mde_analysis.ipynb
├── tools/                              # The rebuild pipeline
│   ├── build.sh                        #   bash tools/build.sh [--all]
│   ├── compute_analysis.py             #   [raw] models and design effects -> derived/
│   ├── make_figures.py                 #   [raw] the five SVG charts
│   ├── make_notebook.py                #   the Colab notebook
│   ├── build_pages.py                  #   derived/ + templates/ -> public/
│   └── derived/                        #   aggregate results, committed
├── assets/social/                      # Social card sources and render script
├── .github/workflows/pages.yml         # Builds and deploys public/ to Pages
└── CLAUDE.md                           # Working brief for this repository
```

---

## Data availability

**The survey files are not in this repository.**

The three NSDUH public-use files total about 1.1 GB, roughly 59,000 respondents and 2,650
variables per year. They are not committed for three independent reasons: each exceeds
GitHub's per-file limit; SAMHSA distributes them publicly, so a copy here would only go
stale; and they remain individual-level records covering substance use and mental health,
where publishing derived aggregates is the right level.

Download them from
[SAMHSA](https://www.samhsa.gov/data/data-we-collect/nsduh-national-survey-drug-use-and-health).
Note the survey year on any figure: the questionnaire changes between years.

Everything published here is aggregate. The notebook runs on synthetic data generated from
this study's aggregate parameters, with a flag to switch onto the real files.

---

## Rebuilding

```bash
bash tools/build.sh          # rebuild the pages from committed data
bash tools/build.sh --all    # also recompute from the NSDUH files
```

Stages marked `[raw]` need the survey files. Everything they produce is written to
`tools/derived/` as aggregates, and that folder **is** committed, so every page rebuilds on
a fresh checkout without the data. Random seeds are fixed at 1.
---

## License

The **code** in this repository is released under the [MIT License](LICENSE): the R
pipeline, the Python notebook, and everything under `tools/` and `public/`. This is the
repository with the least attached: essentially all of it is code, so essentially all of it
is reusable.

Not covered by that license:

- **The NSDUH survey files**, which are not in this repository. They are distributed by
  SAMHSA under their own terms. See [Data availability](#data-availability).

---

## Credits

Analysis and site by John Fisher.

Data: Substance Abuse and Mental Health Services Administration, Center for Behavioral
Health Statistics and Quality, National Survey on Drug Use and Health, 2022, 2023 and 2024
public-use files.

© 2026 John Fisher
